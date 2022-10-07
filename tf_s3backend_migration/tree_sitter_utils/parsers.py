from tree_sitter import Language, Parser
from pathlib import Path
import sys

OUT_LIB = 'build/my_langs.so'
TS_PARSERDIR_PRE = 'tree-sitter-'

class Parsers:

    def __init__(self,top_path:Path):
        print(str(top_path))
        self._parser_dirs = [p for p in top_path.iterdir() 
            if p.is_dir() and p.name.startswith(TS_PARSERDIR_PRE)]
        self._lang_names = [d.name.removeprefix(TS_PARSERDIR_PRE) for d in self._parser_dirs]
        print("names",self._lang_names)
        self._langs = { n : Language(OUT_LIB,n) for n in self._lang_names}

    #try:
    #    Language.build_library(OUT_LIB,[f"{top_path}/{TS_PARSERDIR_PREFIX}{lib}" for lib in LIBS])
    #except FileNotFoundError as e:
    #    print(e)
    #    print(f"ERROR: Didn't you DOWNLOAD 'tree-sitter-{LIBS}' to {top_path} ?")
    #    sys.exit(1)
    
    def get_parser(self,lang):
        print(self._lang_names)
        p = Parser()
        p.set_language(self._langs.get(lang))
        return p
