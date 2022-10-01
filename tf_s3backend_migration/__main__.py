import click
from tree_sitter_utils import parsers

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
def hcl(parsers_dir,file_path):
    p = parsers.init(parsers_dir)

    # open file
    with open(file_path,"rb") as f:
        tree = p.parse(f.read())
    
    print(tree.root_node.sexp()) 

if __name__ == '__main__':
    cli()
