# analyze dirs
from typing import List,Optional
from pathlib import Path
import glob
import re
from dataclasses import dataclass

WILDCARD = '%'
NON_SLASH_GRP_MATCH = '([^/]*)'

@dataclass
class TFWannabeWorkSpace:
    name: str
    input_file: Path
    init_file: Path = Path(".missing") # removes it from _init_

    @classmethod
    def from_match(cls,match_pattern:str,input_file:Path) -> 'TFWannabeWorkSpace':
        regex_ = match_pattern.replace(WILDCARD, NON_SLASH_GRP_MATCH)
        f = str(input_file.absolute())
        s_result = re.search(regex_, f)
        name = s_result.group(1) # type: ignore (pyright fix)
        return TFWannabeWorkSpace(name,input_file)

    def append_init(self,glob_pattern:str):
        assert self.input_file.exists()
        results = list(self.input_file.parent.glob(glob_pattern))
        assert len(results) == 1 , "Expected ONE match"
        self.init_file = results[0]
        

def scan_tf_dir(dir:Path,
                    inputs_pattern:str,
                    excludes:List[str] = []) -> List[TFWannabeWorkSpace]:
    # first check for local patterns
    assert dir.is_dir()
    assert WILDCARD in inputs_pattern, f"Must have a single '{WILDCARD}' in match_pattern!"

    g_pattern = inputs_pattern.replace(WILDCARD,"*").lstrip("/")
    cand_files = [Path(f) for f in glob.glob(str(dir) + "/" + g_pattern)]
    matching_files = [f for f in cand_files if f.name not in excludes]
    return [TFWannabeWorkSpace.from_match(inputs_pattern,f) for f in matching_files]



