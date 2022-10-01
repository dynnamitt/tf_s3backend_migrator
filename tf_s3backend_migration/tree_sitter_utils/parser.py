from tree_sitter import Language, Parser
import sys
LIB = 'build/my_langs.so'

def hcl(path):
    try:
        Language.build_library(LIB,[path])
    except FileNotFoundError as e:
        print(e)
        print(f"ERROR: Didn't you DOWNLOAD the tree-sitter-hcl to {path} ?")
        sys.exit(1)

    HCL_LANGUAGE = Language(LIB, 'hcl')
    parser = Parser()
    parser.set_language(HCL_LANGUAGE)
    return parser
