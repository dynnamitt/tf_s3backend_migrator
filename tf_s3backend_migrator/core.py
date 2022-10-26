from functools import lru_cache
from . import psudo_workspaces as pw
from . import queries as q
from rich import print
from pathlib import Path
from typing import List,Dict
import click

MK_FILE = "Makefile"

pattern_pairs = {
        ("%/input.tfvars","init.tfvars"),
        ("input-%.tfvars",MK_FILE)
        }

TF_CODE_DIR = "tf-code"

DEF_ARN = "arn:aws:iam::{}:role/admin"

# 100% perf : make enum
EXPECTED_VALS = {"bucket",
                 "region",
                 "dynamodb_table",
                 "key",
                 "role_arn"}

CS = ["cyan","blue","yellow","red","orange","magenta"]

def main(root_dir:Path,new_backend:Path):
    """Select the type and handle it"""
   
    try:
        dest_backend_keys = q.parse_file(new_backend).tf_backend_body_kv()
        print("dest",dest_backend_keys)
    except ModuleNotFoundError as e:
        print(str(e))
        raise AssertionError(f"{str(new_backend)} do not contain as TF BACKEND block ! ")



    for patt,init_glob in pattern_pairs:
        ws = pw.scan_tf_dir(root_dir,patt,excludes=[TF_CODE_DIR])
        ws_names = [w.name for w in ws] 
        if len(ws)>0 :
            print(f"\n:bulb: Project_dir is of type '{patt}'\n")
            print(f"Psudo-workspaces located:")
            [print(f" - [{CS[idx+1]}]{w}[/{CS[idx+1]}]") for idx,w in enumerate(ws_names)]
            handle_current(root_dir,init_glob,ws)
                
def handle_current(root_dir :Path,
                     init_glob :str,
                     ws: List[pw.TFWannabeWorkSpace]):

    code_path = Path(root_dir,TF_CODE_DIR)
    for idx,w in enumerate(ws):
        w.append_init(init_glob)
        print()
        print(f"====== Psudo-TF-Workspace: [{CS[idx+1]}]{w.name}[/{CS[idx+1]}] :computer:")
        print()
        init_result = q.parse_file(w.init_file)
        init_vals = init_result.tf_backend_body_kv() if w.init_file.name == MK_FILE else init_result.key_values()
        vars = q.parse_file(w.input_file).key_values()
        # pprint(vars)
        diff = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff) > 0:
            print(f"Searching for {diff} in {code_path.name} (backend block) ... ",end="")
            more_kvs = scan_dir_backend_kvs(code_path)
            for k,v in more_kvs.items():
                if k in diff:
                    init_vals[k] = v
                    print(f" -> found '{k}' ",end="")
        # round 2
        print()
        diff2 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff2) == 1 and "role_arn" in diff2:
            acc_num = vars.get('account',init_vals.get('account',"???????????"))
            ask = "'role_arn' isn't specified in the code, please Enter"
            r = click.prompt(text=ask, default = DEF_ARN.format(acc_num))
            click.prompt
            init_vals["role_arn"] = r
        if len(diff2) > 2:
            txt = f"CRITICAL: Code parse of '{code_path.name}' still renders missing vals: {diff2} !"
            raise AssertionError(txt)

        print(init_vals)
                
@lru_cache()
def scan_dir_backend_kvs(code_dir:Path) -> q.QResult:
    tfs = [f for f in code_dir.iterdir() if f.suffix == ".tf"]

    for f in tfs:
        try:
            kvs = q.parse_file(f).tf_backend_body_kv()
            print("|code-parsed|",end="")
            return kvs
        except ModuleNotFoundError:
            pass
            # just move on to next file
    return {}

