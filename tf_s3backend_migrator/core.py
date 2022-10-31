from dataclasses import dataclass
from functools import lru_cache
from . import psudo_workspaces as pw
from . import queries as q
from . import aws
from rich import print
from pathlib import Path
from typing import List, Tuple,Dict
import click


DEF_ARN = "arn:aws:iam::{}:role/admin"

# make enum ?
EXPECTED_VALS = {"bucket",
                 "region",
                 "dynamodb_table",
                 "key",
                 "role_arn"}

DEFAULT_WRKSPACE = "test"

CS = ["cyan","blue","yellow","red","purple","magenta","green"]

@dataclass()
class StateBackup:
    psudo_wrkspc_name:str
    temp_file:Path
    inp_vals: Dict[str,str]

def main(root_dir:Path, new_backend_tf:Path):
    """Select the type and handle it"""


    try:
        dest_backend_keys = q.parse_file(new_backend_tf).tf_backend_body_kv()
    except q.TSQueryError as e:
        print("Bad new_backend_tf file!")
        print(e)
        return
    print("Destination backend vals:",dest_backend_keys)
    diff_new_backend_tf = EXPECTED_VALS.difference(dest_backend_keys.keys())
    print("Warning: Missing keys:",diff_new_backend_tf) if len(diff_new_backend_tf)>0 else None
    if not click.confirm("Continue ?"):
        return
    
    project = pw.get_legacy_project(root_dir)

    print(f"\n:bulb: Project_dir is of type '{project.pattern}'\n")
    print(f"Psudo-workspaces located:")
    ws_names = [w.name for w in project.workspaces] 
    for idx,w in enumerate(ws_names):
        color = CS[idx] if w != DEFAULT_WRKSPACE  else "white"
        print(f" - [{color}]{w}[/{color}]")  
    
    state_backups = handle_downloads( Path(root_dir,pw.TF_CODE_DIR),project)
    config_var_section = {}
    print("\n--*--\n")

    for sb in state_backups:
        p_wrkspc_n = sb.psudo_wrkspc_name
        from_file = sb.temp_file
        env_part = f"env:/{p_wrkspc_n}/" if p_wrkspc_n != DEFAULT_WRKSPACE else ""
        true_wrkspc_name = p_wrkspc_n if p_wrkspc_n != DEFAULT_WRKSPACE else 'default'
        config_var_section[true_wrkspc_name] = sb.inp_vals
        print("<<<< Uploading {temp_file} to s3://{bucket}/{env_part}{key} ...."
              .format(temp_file=from_file,env_part=env_part,**dest_backend_keys)) 
        aws.upload_s3_obj(from_file,"tf_migrapolis",**dest_backend_keys)

    print("\n--*--\n")
 
    # new config file
    with open("templ/config.tf","r") as f:
        conf_txt = "".join(f.readlines())
    
    print(str(config_var_section).translate("".maketrans(':',"=")))


def handle_downloads(code_path :Path, project:pw.LegacyProject) -> List[StateBackup]: 
    """open all source vals and download"""

    result : List[StateBackup] = []

    for idx,w in enumerate(project.workspaces):
        print()
        print(f"====== Psudo-TF-Workspace: [{CS[idx+1]}]{w.name}[/{CS[idx+1]}] :computer:")
        print()
        init_result = q.parse_file(w.init_file)
        init_vals = init_result.tf_backend_body_kv() if w.init_file.name == pw.MK_FILE else init_result.key_values()
        vars = q.parse_file(w.input_file).key_values()
        # pprint(vars)
        diff1 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff1) > 0:
            print(f"Searching for {diff1} in {code_path.name} (backend block) ... ",end="")
            more_kvs = scan_dir_backend_kvs(code_path)
            for k,v in more_kvs.items():
                if k in diff1:
                    init_vals[k] = v
                    print(f" -> found '{k}' ",end="")
        # round 2
        print()
        diff2 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff2) == 1 and "role_arn" in diff2:
            acc_num = vars.get('account',init_vals.get('account',"???????????"))
            ask = "\n- 'role_arn' isn't specified in the code\n  please Enter"
            r = click.prompt(text=ask, default = DEF_ARN.format(acc_num))
            init_vals["role_arn"] = r
        elif len(diff2) > 2:
            txt = f"CRITICAL: Code parse of '{code_path.name}' still renders missing vals: {diff2} !"
            raise AssertionError(txt)

        print(">>>> Downloading source: s3://{bucket}/{key} ...".format(**init_vals))
        temp_file = aws.download_s3_obj("tf_migr_tool",**init_vals)
        result.append(StateBackup(w.name,temp_file,vars))

    # <-- indent 
    # oh god ... clean up these for-loops eh??
    return result
                        
@lru_cache()
def scan_dir_backend_kvs(code_dir:Path) -> q.QResult:
    try:
        assert code_dir.is_dir()
    except AssertionError:
        print("\n Ups!")
        print(pw.TF_CODE_DIR, "not in sight!")
        raise NotImplementedError("I need more code , sorry")

    tfs = [f for f in code_dir.iterdir() if f.suffix == ".tf"]

    for f in tfs:
        try:
            kvs = q.parse_file(f).tf_backend_body_kv()
            print("|code-parsed|",end="")
            return kvs
        except q.TSQueryError:
            pass
            # just move on to next file
    return {}

