# analyze dirs
from typing import List
from pathlib import Path
import glob
import re
from dataclasses import dataclass

MK_FILE = "Makefile"
TF_CODE_DIR = "tf-code"
WILDCARD = "%"
NON_SLASH_GRP_MATCH = "([^/]*)"


def render_possible_placeholders(init_vals: dict, wrkspace_name) -> dict:
    """Very custom logic for custom edge-case, nevermind this mess"""

    ph_ = lambda id: "$(" + id + ")"
    data = {
        "SRC": TF_CODE_DIR,
        "s_account_n": wrkspace_name,
        "ENV": wrkspace_name,
        "s_proj_suffix": ("__dev" if wrkspace_name == "dev" else ""),
    }

    def render(val: str) -> str:
        data_keys = [ph_name for ph_name in data.keys() if ph_(ph_name) in val]
        if len(data_keys) > 0:
            for k in data_keys:
                val = val.replace(ph_(k), data[k])
        return val

    return {k: render(v) for k, v in init_vals.items()}


@dataclass
class TFWannabeWorkSpace:
    name: str
    input_file: Path
    init_file: Path = Path(".missing")  # removes it from _init_

    @classmethod
    def from_match(cls, match_pattern: str, input_file: Path) -> "TFWannabeWorkSpace":
        regex_ = match_pattern.replace(WILDCARD, NON_SLASH_GRP_MATCH)
        f = str(input_file.absolute())
        s_result = re.search(regex_, f)
        name = s_result.group(1)  # type: ignore (pyright fix)
        return TFWannabeWorkSpace(name, input_file)

    def append_init(self, glob_pattern: str):
        assert self.input_file.exists()
        results = list(self.input_file.parent.glob(glob_pattern))
        assert len(results) == 1, "Expected ONE match"
        self.init_file = results[0]


def scan_tf_dir(
    dir: Path, inputs_pattern: str, excludes: List[str] = []
) -> List[TFWannabeWorkSpace]:
    # first check for local patterns
    assert dir.is_dir()
    assert (
        WILDCARD in inputs_pattern
    ), f"Must have a single '{WILDCARD}' in match_pattern!"

    g_pattern = inputs_pattern.replace(WILDCARD, "*").lstrip("/")
    cand_files = [Path(f) for f in glob.glob(str(dir) + "/" + g_pattern)]
    matching_files = [f for f in cand_files if f.name not in excludes]
    return [TFWannabeWorkSpace.from_match(inputs_pattern, f) for f in matching_files]


@dataclass()
class LegacyProject:
    pattern: str
    init_file: str

    def set_workspaces(self, ws: List[TFWannabeWorkSpace]):
        self.workspaces = ws
        for w in self.workspaces:
            w.append_init(self.init_file)


GEN1 = LegacyProject("%/input.tfvars", "init.tfvars")
GEN2 = LegacyProject("input-%.tfvars", MK_FILE)


def get_legacy_project(root_dir: Path) -> LegacyProject:

    for p in [GEN1, GEN2]:
        ws_ = scan_tf_dir(root_dir, p.pattern, excludes=[TF_CODE_DIR])
        p.set_workspaces(ws_)

    # try?
    if len(GEN1.workspaces) > 0:
        return GEN1
    elif len(GEN2.workspaces) > 0:
        return GEN2
    else:
        raise LookupError("Not a Legacy_project dir")
