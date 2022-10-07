from tree_sitter import Language, Parser
from pathlib import Path
from typing import List
import sys

OUT_LIB = 'build/my_langs.so'
TS_PARSERDIR_PRE = 'tree-sitter-'

class TSParsers:

    def __init__(self,top_path:Path):
        self._parser_dirs = [p for p in top_path.iterdir() 
            if p.is_dir() and p.name.startswith(TS_PARSERDIR_PRE)]
        self._lang_names = [d.name.removeprefix(TS_PARSERDIR_PRE) for d in self._parser_dirs]
        try:
            self._init_langs()
        except OSError as e:
            print(e)
            print(f"WARN: Failed to find {OUT_LIB}, will try to build ...")
            self._build()
            self._init_langs()

    def _init_langs(self):
        self._langs = { n : Language(OUT_LIB,n) for n in self._lang_names}

    def _build(self):
        try:
            Language.build_library(OUT_LIB,self._parser_dirs)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
    
    def get_parser(self,lang:str) -> Parser :
        p = Parser()
        p.set_language(self._langs.get(lang))
        return p
    
    def get_language(self,lang:str) -> Language:
        return self._langs.get(lang)


