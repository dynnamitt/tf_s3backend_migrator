from dataclasses import dataclass
from functools import lru_cache
from . import psudo_workspaces as pw
from . import queries as q
from . import aws
from rich import print
import json
from pathlib import Path
from typing import List, Dict
import click


DEF_ARN = "arn:aws:iam::{}:role/admin"

# make enum ?
EXPECTED_VALS = {"bucket", "region", "dynamodb_table", "key", "role_arn"}

DEFAULT_WRKSPACE = "test"

CS = ["cyan", "blue", "yellow", "red", "purple", "magenta", "green"]

CONF_FILE = "config.tf"
C_TEMPL_FILE = Path(__file__).parent / "templ/config.tf"
C_MAP_TEMPL_PH = "###wrkspc_config###"
C_ACC_MAP_TEMPL_PH = "###accounts###"


@dataclass()
class StateBackup:
    psudo_wrkspc_name: str
    temp_file: Path
    variable_map: Dict[str, str]
    role_arn: aws.AwsArn


def main(root_dir: Path, new_backend_tf: Path):
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

    project = pw.get_legacy_project(root_dir)

    print(f"\n:bulb: Project_dir is of type '{project.pattern}'\n")
    print(f"Psudo-workspaces located:")

    ws_names = [w.name for w in project.workspaces]

    for idx, w in enumerate(ws_names):
        print(f" - [{CS[idx+1]}]{w}[/{CS[idx+1]}]")

    state_backups = handle_downloads(Path(root_dir, pw.TF_CODE_DIR), project)
    config_map = {}
    for sb in state_backups:
        true_wrkspc = (
            "default"
            if sb.psudo_wrkspc_name == DEFAULT_WRKSPACE
            else sb.psudo_wrkspc_name.lower()
        )
        env_part = (
            f"env:/{true_wrkspc}/" if sb.psudo_wrkspc_name != DEFAULT_WRKSPACE else ""
        )
        print(
            "<<<< Uploading {temp_file} to s3://{bucket}/{env_part}{key} ....".format(
                temp_file=sb.temp_file, env_part=env_part, **dest_backend_keys
            )
        )
        aws.upload_to_s3(sb.temp_file, **dest_backend_keys)
        sb.variable_map["aws_account_"] = sb.role_arn.account
        config_map[true_wrkspc] = sb.variable_map

    dest_config_tf = new_backend_tf.parent / CONF_FILE
    config_tf = render_config_tf(dest_config_tf, config_map)
    print(f" ------- {CONF_FILE} ---------")
    print(config_tf)
    print(f" ------- {CONF_FILE} ---------")
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
        init_result = q.parse_file(w.init_file)
        init_vals = (
            init_result.tf_backend_body_kv()
            if w.init_file.name == pw.MK_FILE
            else init_result.key_values()
        )
        vars = q.parse_file(w.input_file).key_values()
        # pprint(vars)
        diff1 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff1) > 0:
            print(
                f"Searching for {diff1} in {code_path.name} (backend block) ... ",
                end="",
            )
            more_kvs = scan_dir_backend_kvs(code_path)
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

        print(">>>> Downloading source: s3://{bucket}/{key} ...".format(**init_vals))
        print(init_vals)
        init_vals = pw.render_possible_placeholders(init_vals, w.name)
        print("---")
        print(init_vals)
        temp_file = aws.download_s3_obj(**init_vals)
        backups.append(
            StateBackup(w.name, temp_file, vars, aws.AwsArn(init_vals["role_arn"]))
        )

    # <-- indent
    # oh god ... clean up these for-loops eh??
    return backups


def render_config_tf(file: Path, data: dict) -> str:
    wrkspc_data_txt = json.dumps(data, indent=2).replace(":", "=")

    with open(file, "r") as f:
        tf_code_templ = f.read()

    config_tf = tf_code_templ.replace(C_MAP_TEMPL_PH, f"    {wrkspc_data_txt}")
    return config_tf


@lru_cache()
def scan_dir_backend_kvs(code_dir: Path) -> q.QResult:
    tfs = [f for f in code_dir.iterdir() if f.suffix == ".tf"]

    for f in tfs:
        try:
            kvs = q.parse_file(f).tf_backend_body_kv()
            print("|code-parsed|", end="")
            return kvs
        except q.TSQueryError:
            pass
            # just move on to next file
    return {}
