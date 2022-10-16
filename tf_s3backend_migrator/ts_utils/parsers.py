from tree_sitter import Language, Parser
from pathlib import Path
from typing import List,Tuple
import sys

OUT_LIB = 'build/my_langs.so'
TS_PARSERDIR_PRE = 'tree-sitter-'

hcl_q = {

    "attr_expr_kv" : lambda key: f"""
    (
        (attribute (identifier) @key
            (expression (expr_term (template_expr (quoted_template) @val) )))
        (#eq? @key "{key}" )
    )
    """
}

# https://stackoverflow.com/questions/63635500/how-to-get-the-values-from-nodes-in-tree-sitter
def get_text(bytes,node):
    return bytes[node.start_byte:node.end_byte].decode('utf8')


class TSParsers:

    def __init__(self,lang_names,top_path=None):
        self._top_path = top_path
        self._lang_names = lang_names
        try:
            self._init_langs()
        except OSError as e:
            sys.stderr.write(str(e)+"\n")
            sys.stderr.write(f"INFO: Failed to find {OUT_LIB}, will try to build ...\n")
            self._build()
            self._init_langs()

    def _init_langs(self):
        self._langs = { n : Language(OUT_LIB,n) for n in self._lang_names}

    def _build(self):
        if not self._top_path:
            raise NotADirectoryError("Could not build parser-lib without top_path\n")

        p0 = Path(self._top_path)
        all_parser_dirs = [p for p in p0.iterdir() 
                if p.is_dir() and p.name.startswith(TS_PARSERDIR_PRE)]
        parser_dirs = [d for d in all_parser_dirs 
            if d.name.removeprefix(TS_PARSERDIR_PRE) in self._lang_names] 

        if len(parser_dirs) != 2:
            raise AssertionError(f"Cannot find correct parsers in {p0.name}, should be {self._lang_names} !")

        Language.build_library(OUT_LIB, parser_dirs)
        # err FileNotFoundError as e:
    
    def get(self,lang:str) -> Tuple[Parser,Language] :
        p = Parser()
        l = self._langs.get(lang)
        p.set_language(l)
        return (p,l)
    



