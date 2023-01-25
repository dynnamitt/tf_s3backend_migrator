from . import psudo_workspaces as pw
from . import queries as q

from pathlib import Path
from pprint import pprint


def main(tf_dir: Path):
    show = {}
    try:
        legacy_p = pw.get_legacy_project(tf_dir)
        pprint(legacy_p)
        for w in legacy_p.workspaces:
            init_vals = q.init_vals(q.parse_file(w.init_file))
            pprint(init_vals)

    except LookupError as e:
        print("normal?")
