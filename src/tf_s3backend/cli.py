import click
import sys
from pathlib import Path
from pprint import pprint
import ts_language_collection as ts
from . import queries as q
from . import psudo_workspaces as pw
from .migrate import main as migrate_main
from . import analyze


def die(s, code=1):
    sys.stderr.write(str(s) + "\n")
    sys.exit(code)


@click.group()
def cli_group():
    pass


@cli_group.command()
@click.argument(
    "tf_directory",
    type=click.Path(exists=True, resolve_path=True, dir_okay=True, file_okay=False),
    nargs=1,
)
@click.argument(
    "new_backend_tf",
    type=click.Path(exists=True, resolve_path=True, dir_okay=False, file_okay=True),
    nargs=1,
)
@click.option(
    "--tf_code_dir",
    type=str,
    nargs=1,
    default="tf-code"
)
def migrate(tf_directory: str, new_backend_tf: str, tf_code_dir:str):
    migrate_main(Path(tf_directory), Path(new_backend_tf), tf_code_dir)


@cli_group.command()
@click.argument(
    "tf_code_dir",
    type=click.Path(exists=True, resolve_path=True, dir_okay=True, file_okay=False),
    nargs=1,
)
def show(tf_code_dir: str):
    code_dir = Path(tf_code_dir)
    summary = analyze.main(code_dir)
    pprint(summary)


@cli_group.command()
@click.argument("file-path", type=click.Path(exists=True, resolve_path=True), nargs=1)
def hcl_backend(file_path):
    vs = q.parse_file(Path(file_path)).tf_backend_body_kv()
    pprint(vs)


@cli_group.command()
@click.argument("file-path", type=click.Path(exists=True, resolve_path=True), nargs=1)
def hcl_vars(file_path):
    vs = q.parse_file(Path(file_path)).key_values()
    pprint(vs)


@cli_group.command()
@click.argument("file-path", type=click.Path(exists=True, resolve_path=True), nargs=1)
def mk_vars(file_path):
    vs = q.parse_file(Path(file_path)).key_values()
    pprint(vs)


@cli_group.command()
@click.argument("file-path", type=click.Path(exists=True, resolve_path=True), nargs=1)
def hcl_full_tree(file_path):

    parser = ts.get_parser("hcl")

    # open file
    with open(file_path, "rb") as f:
        code_buf = f.read()
        tree = parser.parse(code_buf)

    print(tree.root_node.sexp())


@cli_group.command()
@click.argument("file-path", type=click.Path(exists=True, resolve_path=True), nargs=1)
def mk_full_tree(file_path):

    parser = ts.get_parser("make")

    # open file
    with open(file_path, "rb") as f:
        code_buf = f.read()
        tree = parser.parse(code_buf)

    print(tree.root_node.sexp())
