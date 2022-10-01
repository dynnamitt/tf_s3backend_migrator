from tree_sitter import Language, Parser
import sys
OUT_LIB = 'build/my_langs.so'

TS_LIBDIR_PREFIX = 'tree-sitter-'
LIBS = ['hcl','make']

def init(top_path):
    try:
        Language.build_library(OUT_LIB,[f"{top_path}/{TS_LIBDIR_PREFIX}{lib}" for lib in LIBS])
    except FileNotFoundError as e:
        print(e)
        print(f"ERROR: Didn't you DOWNLOAD 'tree-sitter-{LIBS}' to {top_path} ?")
        sys.exit(1)

    HCL_LANGUAGE = Language(OUT_LIB, LIBS[0])
    MAKE_LANGUAGE = Language(OUT_LIB, LIBS[1])
    parser = Parser()
    parser.set_language(HCL_LANGUAGE)
    return parser
