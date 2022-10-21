import click
import sys
from pathlib import Path
from pprint import pprint
import ts_language_collection as ts
from . import queries as q
from . import psudo_workspaces as p_wrkspc


def die(s,code=1):
    sys.stderr.write(str(s)+"\n")
    sys.exit(code)

@click.group()
def cli_group():
    pass

@cli_group.command()
@click.argument("directory", 
                type=click.Path(exists=True,resolve_path=True,
                                dir_okay=True,file_okay=False),
                nargs=1)
def analyze(directory):
    excludes = ["tf-code"]
    pattern_pairs = [("%/input.tfvars","init.tfvars"),
                ("input-%.tfvars","Makefile")]
    for patt,init_glob in pattern_pairs:
        ws = p_wrkspc.scan_tf_dir(Path(directory),patt,excludes)
        if len(ws)>0 :
            print(f"project is of type {patt}")
            for w in ws:
                w.append_init(init_glob)
            pprint(ws)
            for w in ws:
                print(f"== {w.name} ==")
                pprint(q.parse_file(w.init_file).attr_expr())

@cli_group.command()
@click.argument("file-path", 
                type=click.Path(exists=True,resolve_path=True),
                nargs=1)
def hcl_tfvars(file_path):

    hcl = ts.get_language("hcl")
    parser = ts.get_parser("hcl") 

    # open file
    with open(file_path,"rb") as f:
        code_buf = f.read()
        tree = parser.parse(code_buf)

    print(tree.root_node.sexp()) 
    print("-------------")



