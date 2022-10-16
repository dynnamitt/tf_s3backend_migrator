import click
from ts_utils import parsers
import sys

LANGS = ["make","hcl"]

def die(s,code=1):
    sys.stderr.write(str(s)+"\n")
    sys.exit(code)

def get_ts_parsers(dir=None): 
    try:
        return parsers.TSParsers(LANGS,dir)
    except NotADirectoryError :
        die(f"--> Git-clone the parsers {LANGS} & use the 'compile' command to build a library")
    except Exception as e:
        die(e)


@click.group()
def cli():
    pass

@cli.command()
@click.argument("parsers-root-dir",
              type=click.Path(exists=True,resolve_path=True),
              nargs=1)
def compile(parsers_root_dir):
    get_ts_parsers(parsers_root_dir)
    

@cli.command()
@click.argument("file-path", 
                type=click.Path(exists=True,resolve_path=True),
                nargs=1)
def hcl_tfvars(file_path):

    p,hcl = get_ts_parsers().get("hcl")

    # open file
    with open(file_path,"rb") as f:
        code_buf = f.read()
        tree = p.parse(code_buf)

    print(tree.root_node.sexp()) 
    print("-------------")

    part_queries = [parsers.hcl_q["attr_expr_kv"](k) for k in ["role_arn","region","bucket","dynamodb_table"]]

    q1 = "\n".join(part_queries)
    
    query = hcl.query(q1)

    # clever zip_from_i*2
    i_captures = iter(query.captures(tree.root_node))
    cap_paired = zip(i_captures,i_captures)
    
    for k,v in cap_paired: #

        k_ = parsers.get_text(code_buf,k[0])
        v_ = parsers.get_text(code_buf,v[0])
        print(k_,v_)


if __name__ == '__main__':
    cli()
