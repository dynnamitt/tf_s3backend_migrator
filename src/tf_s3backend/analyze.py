from . import psudo_workspaces as pw

from pathlib import Path


def main(tf_dir: Path):
    legacy = pw.get_legacy_project(tf_dir)
    print(legacy)
