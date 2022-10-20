# analyze dirs
from typing import List
from pathlib import Path
import glob
import re
from dataclasses import dataclass

WILDCARD = '%'
NON_SLASH_GRP_MATCH = '([^/]*)'

@dataclass
class TerraformPsudoWorkSpace:
    name: str
    input_file: Path

    @classmethod
    def from_match(cls,match_pattern:str,input_file:Path) -> 'TerraformPsudoWorkSpace':
        regex_ = match_pattern.replace(WILDCARD, NON_SLASH_GRP_MATCH)
        f = str(input_file.absolute())
        s_result = re.search(regex_, f)
        name = s_result.group(1)
        return TerraformPsudoWorkSpace(name,input_file)

def scan_tf_dir(dir:Path,
                    match_pattern:str,
                    excludes:List[str] = []) -> List[TerraformPsudoWorkSpace]:
    # first check for local patterns

    assert WILDCARD in match_pattern, f"Must have a single '{WILDCARD}' in match_pattern!"

    g_pattern = match_pattern.replace(WILDCARD,"*").lstrip("/")
    cand_files = [Path(f) for f in glob.glob(str(dir) + "/" + g_pattern)]
    matching_files = [f for f in cand_files if f.name not in excludes]
    return [TerraformPsudoWorkSpace.from_match(match_pattern,f) for f in matching_files]





