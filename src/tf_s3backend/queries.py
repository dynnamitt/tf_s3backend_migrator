from dataclasses import dataclass
from typing import Optional, Dict
import ts_language_collection as ts_coll
from functools import lru_cache
from pathlib import Path

CAP_NODE = 0
CAP_ID = 1

QResult = Dict[str, str]


class TSQueryError(Exception):
    pass


@dataclass()
class TSResult:
    """Abstract class w Tree-sitter main values"""

    code: bytes
    tree: ts_coll.Tree
    lang: ts_coll.Language
    parser: ts_coll.Parser

    def key_values(self, key_name: Optional[str] = None) -> QResult:
        raise NotImplementedError("Use subclass")

    def tf_backend_body_kv(self, backend_type: str = "s3") -> QResult:
        raise NotImplementedError("Use subclass")

    def wrap_kvs(self, scm_query) -> QResult:
        query = self.lang.query(scm_query)
        # clever zip_from_i*2
        i_captures = iter(query.captures(self.tree.root_node))
        cap_paired = zip(i_captures, i_captures)
        return {
            self.node_text(k[CAP_NODE]).strip(): self.node_text(v[CAP_NODE]).strip()
            for k, v in cap_paired
        }

    # https://stackoverflow.com/questions
    #       /63635500/how-to-get-the-values-from-nodes-in-tree-sitter
    def node_text(self, node: ts_coll.Node) -> str:
        DBL_Q = '"'
        q_txt = self.code[node.start_byte : node.end_byte].decode("utf8")
        return q_txt.strip(DBL_Q)


class HCLQueries(TSResult):
    """Hashicorp HCL queries"""

    def key_values(self, key_name: Optional[str] = None) -> QResult:
        only_key_name = f'( #eq? @key "{key_name}" )' if key_name else ""
        scm = f"""
        (
            (attribute (identifier) @key
            (expression (expr_term (template_expr (quoted_template) @val) )))
            {only_key_name}
        )
        """
        return self.wrap_kvs(scm)

    def tf_backend_body_kv(self, backend_type: str = "s3") -> QResult:
        scm = f"""
        (block (identifier) @block 
            (body (block 
                   (identifier) @sub_block 
                   (string_literal 
                    (quoted_template) @sub_name)
                        (#eq? @block "terraform")
                        (#eq? @sub_block "backend")
                        (#match? @sub_name "{backend_type}")
                     (body) @body
                   )))
        """
        query = self.lang.query(scm)
        captures = query.captures(self.tree.root_node)
        body_caps = [c for c in captures if c[CAP_ID] == "body"]
        if len(body_caps) == 1:
            body_txt = self.node_text(body_caps[0][CAP_NODE])
            return parse_txt(body_txt, "hcl").key_values()
        else:
            raise TSQueryError(f"No terraform.backend.{backend_type} block")


class MakeQueries(TSResult):
    """Gnu Make(file) queries"""

    def key_values(self, key_name: Optional[str] = None) -> QResult:
        scm = """
        (variable_assignment
         name: (word) @key
         value: (text) @val)
        """
        return self.wrap_kvs(scm)

    def tf_backend_body_kv(self, backend_type: str = "s3") -> QResult:
        STATE_PRE = "s_"
        all_keys = self.key_values()

        res = {
            k.removeprefix(STATE_PRE): v
            for k, v in all_keys.items()
            if k.startswith(STATE_PRE)
        }
        if "table" in res.keys():
            res["dynamodb_table"] = res["table"]
        return res


UN_SUPP_LANG = "That language is not supported here!"


def parse_txt(txt: str, lang: str) -> TSResult:
    """Factory from string"""
    l_obj = ts_coll.get_language(lang)
    parser = ts_coll.get_parser(lang)
    code_buf = bytes(txt, "UTF-8")
    tree = parser.parse(code_buf)
    if lang == "hcl":
        return HCLQueries(code_buf, tree, l_obj, parser)
    elif lang == "make":
        return MakeQueries(code_buf, tree, l_obj, parser)
    else:
        raise RuntimeError(UN_SUPP_LANG)


def parse_file(code_file: Path) -> TSResult:
    """Factory from string"""

    assert code_file.is_file()

    if code_file.suffix in [".tfvars", ".tf"]:
        lang = "hcl"
    elif code_file.suffix == ".mk" or code_file.name == "Makefile":
        lang = "make"
    else:
        raise NameError(f"'{code_file.name}' unrecognized filename/ext")

    l_obj = ts_coll.get_language(lang)
    parser = ts_coll.get_parser(lang)

    # open file
    with open(code_file, "rb") as f:
        code_buf = f.read()
        tree = parser.parse(code_buf)
    if lang == "hcl":
        return HCLQueries(code_buf, tree, l_obj, parser)
    elif lang == "make":
        return MakeQueries(code_buf, tree, l_obj, parser)
    else:
        raise RuntimeError(UN_SUPP_LANG)


def init_vals(ts_result: TSResult) -> QResult:
    if isinstance(ts_result, MakeQueries):
        return ts_result.tf_backend_body_kv()
    else:
        return ts_result.key_values()


@lru_cache()
def scan_dir_backend_kvs(code_dir: Path) -> QResult:
    tfs = [f for f in code_dir.iterdir() if f.suffix == ".tf"]

    for f in tfs:
        try:
            kvs = parse_file(f).tf_backend_body_kv()
            # indicate no-cache run:
            print("|code-dir-parsed|", end="")
            return kvs
        except TSQueryError:
            pass
            # just move on to next file
    return {}
