import click
from ts_utils import parsers
from pathlib import Path

@click.group()
def cli():
    pass

@cli.command()
@click.argument("parsers-dir", 
                type=click.Path(exists=True,file_okay=False,resolve_path=True),
                nargs=1)
@click.argument("file-path", 
                type=click.Path(exists=True,resolve_path=True),
                nargs=1)
def hcl_tfvars(parsers_dir,file_path):

    ps = parsers.TSParsers(Path(parsers_dir))
    p = ps.get_parser("hcl")

    # open file
    with open(file_path,"rb") as f:
        tree = p.parse(f.read())


    print(tree.root_node.sexp()) 
    print("querying..")

    query = ps.get_language("hcl").query("""
    (attribute (identifier) @property)
    (one_line_block (identifier) @type)
    """)

    captures = query.captures(tree.root_node)
    for c in captures:
        print("len",len(c))
        print(c[0],c[1])


if __name__ == '__main__':
    cli()
