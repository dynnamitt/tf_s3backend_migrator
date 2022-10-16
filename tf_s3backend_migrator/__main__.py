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
        tree = p.parse(f.read())


    print(tree.root_node.sexp()) 
    print("querying..")

    query = hcl.query("""
    (attribute (identifier) @property)
    (one_line_block (identifier) @type)
    """)

    captures = query.captures(tree.root_node)
    for c in captures:
        print("len",len(c))
        print(c[0],c[1])


if __name__ == '__main__':
    cli()
