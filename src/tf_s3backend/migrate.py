from dataclasses import dataclass
from . import psudo_workspaces as pw
from . import queries as q
from . import aws
from rich import print
from pathlib import Path
from typing import List, Dict
import click
from . import algo


DEF_ARN = "arn:aws:iam::{}:role/admin"

# make enum ?
EXPECTED_VALS = {"bucket", "region", "dynamodb_table", "key", "role_arn"}


CS = ["cyan", "blue", "yellow", "red", "purple", "magenta", "green"]

CONF_FILE = "config.tf"
C_TEMPL_FILE = Path(__file__).parent / "templ/config.tf"
C_MAP_TEMPL_PH = "###wrkspc_config###"
C_CONSTS_TEMPL_PH = "###constants###"
C_ACC_MAP_TEMPL_PH = "###accounts###"


@dataclass()
class StateBackup:
    psudo_wrkspc_name: str
    temp_file: Path
    variable_map: Dict[str, str]
    role_arn: aws.AwsArn


def default_workspace(psudo_w_backups: List[StateBackup]) -> str:
    p_wrkspc_names = [bak.psudo_wrkspc_name for bak in psudo_w_backups]

    intersect = {"dev","test","master.test"}.intersection(p_wrkspc_names)
    if intersect:
        return list(intersect)[0]
    else:
        raise AssertionError("Neither dev/test in result. Strange legacy project this")


def main(root_dir: Path, new_backend_tf: Path,tf_code_dir:str):
    """Select the type and handle it"""

    try:
        dest_backend_keys = q.parse_file(new_backend_tf).tf_backend_body_kv()
    except q.TSQueryError as e:
        print("Bad new_backend_tf file!")
        print(e)
        return
    print("Destination backend vals:", dest_backend_keys)
    diff_new_backend_tf = EXPECTED_VALS.difference(dest_backend_keys.keys())
    print("Warning: Missing keys:", diff_new_backend_tf) if len(
        diff_new_backend_tf
    ) > 0 else None
    if not click.confirm("Continue ?"):
        return

    project = pw.get_legacy_project(root_dir,tf_code_dir)

    print(f"\n:bulb: Project_dir is of type '{project.pattern}'\n")
    print(f"Psudo-workspaces located:")

    ws_names = [w.name for w in project.workspaces]

    for idx, w in enumerate(ws_names):
        print(f" - [{CS[idx+1]}]{w}[/{CS[idx+1]}]")

    state_backups = handle_downloads(Path(root_dir, tf_code_dir), project)
    def_p_wrkspace = default_workspace(state_backups)
    config_map = {}
    for sb in state_backups:
        true_wrkspc = (
            "default"
            if sb.psudo_wrkspc_name == def_p_wrkspace
            else sb.psudo_wrkspc_name.lower()
        )
        env_part = (
            f"env:/{true_wrkspc}/" if sb.psudo_wrkspc_name != def_p_wrkspace else ""
        )
        print(
            "<<<< Uploading {temp_file} to s3://{bucket}/{env_part}{key} ....".format(
                temp_file=sb.temp_file, env_part=env_part, **dest_backend_keys
            )
        )
        aws.upload_to_s3(
            sb.temp_file,
            role_arn=dest_backend_keys["role_arn"],
            bucket=dest_backend_keys["bucket"],
            key=env_part + dest_backend_keys["key"].lstrip("/"),
        )
        print()

        # help the local-user in new file-2-write
        sb.variable_map["localuser_assume_role_arn"] = sb.role_arn.arn
        config_map[true_wrkspc] = sb.variable_map

    config_tf = render_config_tf(C_TEMPL_FILE, config_map)
    print(f" ------- {CONF_FILE} ---------")
    print(config_tf)
    print(f" ------- {CONF_FILE} ---------")
    dest_config_tf = new_backend_tf.parent / CONF_FILE
    if dest_config_tf.exists():
        print("WARN: file exist")

    if click.confirm(f"\nWrite to '{dest_config_tf}'"):
        with open(str(dest_config_tf.absolute()), "w") as f:
            f.write(config_tf)
        print("saved.")
    else:
        print("aborre(td)")


def handle_downloads(code_path: Path, project: pw.LegacyProject) -> List[StateBackup]:
    """open all source vals and download"""

    backups: List[StateBackup] = []

    for idx, w in enumerate(project.workspaces):
        print()
        print(
            f"====== Psudo-TF-Workspace: [{CS[idx+1]}]{w.name}[/{CS[idx+1]}] :computer:"
        )
        print()
        init_vals = q.init_vals(q.parse_file(w.init_file))
        vars = q.parse_file(w.input_file).key_values()
        # pprint(vars)
        diff1 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff1) > 0:
            print(
                f"Searching for {diff1} in {code_path.name} (backend block) ... ",
                end="",
            )
            more_kvs = q.scan_dir_backend_kvs(code_path)
            for k, v in more_kvs.items():
                if k in diff1:
                    init_vals[k] = v
                    print(f" -> found '{k}' ", end="")
        # round 2
        print()
        diff2 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff2) == 1 and "role_arn" in diff2:
            acc_num = vars.get("account", init_vals.get("account", "???????????"))
            ask = "\n- 'role_arn' isn't specified in the code\n  please Enter"
            r = click.prompt(text=ask, default=DEF_ARN.format(acc_num))
            init_vals["role_arn"] = r
        elif len(diff2) > 2:
            txt = f"CRITICAL: Code parse of '{code_path.name}' still renders missing vals: {diff2} !"
            raise AssertionError(txt)

        print(code_path.stem)
        init_vals = pw.render_possible_placeholders(init_vals, w.name, code_path.stem)
        print(">>>> Downloading source: s3://{bucket}/{key} ...".format(**init_vals))
        temp_file = aws.download_s3_obj(**init_vals)
        backups.append(
            StateBackup(w.name, temp_file, vars, aws.AwsArn(init_vals["role_arn"]))
        )

    # <-- indent
    # oh god ... clean up these for-loops eh??
    return backups


def render_config_tf(file: Path, data: dict) -> str:
    """Logic for making a config.tf file
    Now ALSO with a global-scope,
    cherry-picking common vals from .data dict"""

    #print(data)
    dups_free_data,common = algo.extract_dups(data)

    def dict_2_tf(m:dict, indent) -> str:
        ind_ = " " * indent
        res = ""
        for k, v in m.items():
            res = res + f'{ind_}{k} = "{v}"\n'
        return res

    def nested_dict_2_tf(m: dict, indent: int = 4) -> str:
        res = ""
        ind_ = " " * indent
        for w0, v_m in m.items():
            res = res + f"{ind_}{w0} = {{\n"
            res = res + dict_2_tf(v_m,indent*2)
            # for k, v in v_m.items():
                # res = res + f'{ind_}{ind_}{k} = "{v}"\n'
            res = res + f"{ind_}}}\n"
        return res

    wrkspc_data_txt = nested_dict_2_tf(dups_free_data)

    with open(file, "r") as f:
        tf_code_templ = f.read()
    print(file.name)

    config_tf = tf_code_templ.replace(C_MAP_TEMPL_PH, wrkspc_data_txt)
    
    if len(common.keys())>0:
        # 2nd pass
        common_txt = dict_2_tf(common)
        config_tf = config_tf.replace(C_CONSTS_TEMPL_PH, common_txt)

    return config_tf
