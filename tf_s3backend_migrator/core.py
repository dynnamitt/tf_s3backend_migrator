from functools import lru_cache
from . import psudo_workspaces as pw
from . import queries as q
from rich import print
from pathlib import Path
from typing import List,Dict
import click

pattern_pairs = {
        ("%/input.tfvars","init.tfvars"),
        ("input-%.tfvars","Makefile")
        }

EXPECTED_VALS = {"bucket",
                 "region",
                 "dynamodb_table",
                 "key",
                 "role_arn"}

TF_CODE_DIR = "tf-code"
CS = ["cyan","blue","yellow","red","orange","magenta"]

def main(root_dir:Path):
    """Select the type and handle it"""

    for patt,init_glob in pattern_pairs:
        ws = pw.scan_tf_dir(root_dir,patt,excludes=[TF_CODE_DIR])
        ws_names = [w.name for w in ws] 
        if len(ws)>0 :
            print(f"\n:bulb: Project_dir is of type '{patt}'\n")
            print(f"Psudo-workspaces located:")
            [print(f" - [{CS[idx+1]}]{w}[/{CS[idx+1]}]") for idx,w in enumerate(ws_names)]
            handle_specifics(root_dir,init_glob,ws)
                
def handle_specifics(root_dir:Path,
                     init_glob:str,
                     ws: List[pw.TFWannabeWorkSpace]):

    code_path = Path(root_dir,TF_CODE_DIR)
    for idx,w in enumerate(ws):
        w.append_init(init_glob)
        print()
        print(f"====== Psudo-TF-Workspace: [{CS[idx+1]}]{w.name}[/{CS[idx+1]}] :computer:")
        print()
        init_vals = q.parse_file(w.init_file).key_values()
        vars = q.parse_file(w.input_file).key_values()
        # pprint(vars)
        diff = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff) > 0:
            print(f"Searching for {diff} in {code_path.name} (backend block) ... ",end="")
            more_kvs = find_backend_kvs(code_path)
            for k,v in more_kvs.items():
                if k in diff:
                    init_vals[k] = v
                    print(f" -> found '{k}' ",end="")
        # round 2
        print()
        diff2 = EXPECTED_VALS.difference(init_vals.keys())
        if len(diff2) == 1 and "role_arn" in diff2:
            acc_num = vars.get('account',init_vals.get('account',"?????"))
            ask = "'role_arn' isn't specified in the code, please Enter"
            r = click.prompt(text=ask,default=f"arn:aws:iam::{acc_num}/role/admin")
            click.prompt
            init_vals["role_arn"] = r
        if len(diff2) > 2:
            txt = f"CRITICAL: Code parse of '{code_path.name}' still renders missing vals: {diff2} !"
            raise AssertionError(txt)

        print(init_vals)
                
@lru_cache()
def find_backend_kvs(code_dir:Path) -> Dict[str,str]:
    kvs_set = [q.parse_file(f).tf_backend_body_kv()
            for f in code_dir.iterdir() if f.suffix == ".tf"]
    hits = [itm for itm in kvs_set if itm != None] 
    print("[code-parsed]",end="")
    return hits[0] if len(hits)==1 else {}

