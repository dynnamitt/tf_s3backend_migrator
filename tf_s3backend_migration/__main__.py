import click
from tree_sitter_utils import parser

@click.group()
def cli():
    pass

@cli.command()
@click.argument("path", 
                type=click.Path(file_okay=False,resolve_path=True),
                nargs=1)
def test(path):
    print(path)
    parser.hcl(path)


if __name__ == '__main__':
    cli()
