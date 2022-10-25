from dataclasses import dataclass
from typing import Optional,Dict
import ts_language_collection as ts_coll
from pathlib import Path
from pprint import pprint

CAP_NODE = 0
CAP_ID = 1

QResult = Dict[str,str]|None

@dataclass()
class TSResult:
    """Abstract class w Tree-sitter main values"""

    code: bytes
    tree: ts_coll.Tree
    lang: ts_coll.Language
    parser: ts_coll.Parser

    def key_values(self,key_name:Optional[str]=None) -> QResult:
        raise NotImplemented("Use subclass")

    def tf_backend_body_kv(self, backend_type:str="s3") -> QResult:
        raise NotImplemented("Use subclass")

    def wrap_kvs(self,scm_query) -> Optional[Dict[str,str]]:
        query = self.lang.query(scm_query)
        # clever zip_from_i*2
        i_captures = iter(query.captures(self.tree.root_node))
        cap_paired = zip(i_captures, i_captures)
        return {
                self.node_text(k[CAP_NODE]): self.node_text(v[CAP_NODE]) 
                for k,v in cap_paired }

    
    # https://stackoverflow.com/questions
    #       /63635500/how-to-get-the-values-from-nodes-in-tree-sitter
    def node_text(self,node:ts_coll.Node) -> str:
        DBL_Q = '"'
        q_txt = self.code[node.start_byte:node.end_byte].decode('utf8')
        return q_txt.strip(DBL_Q)


class HCLQueries(TSResult):
    """Hashicorp HCL queries"""

    def key_values(self, key_name:Optional[str]=None)-> QResult:
        only_key_name = f'( #eq? @key "{key_name}" )' if key_name else ''
        scm = f"""
        (
            (attribute (identifier) @key
            (expression (expr_term (template_expr (quoted_template) @val) )))
            {only_key_name}
        )
        """
        return self.wrap_kvs(scm)

    def tf_backend_body_kv(self, backend_type:str="s3") -> QResult:
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
            return parse_txt(body_txt,"hcl").key_values()

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
        STATE_PRE = 's_'
        all_keys = self.key_values()
        # hack in place 
        if all_keys:
            res = { k.removeprefix(STATE_PRE):v for k,v in all_keys.items() if k.startswith(STATE_PRE)}
            if 'table' in res.keys():
                res['dynamodb_table'] = res['table']
            return res

UN_SUPP_LANG = "That language is not supported here!"



def parse_txt(txt:str,lang:str) -> TSResult:
    """Factory from string"""
    l = ts_coll.get_language(lang)
    parser = ts_coll.get_parser(lang)
    code_buf = bytes(txt,"UTF-8")
    tree = parser.parse(code_buf)
    match lang:
        case "hcl":
            return HCLQueries(code_buf,tree,l,parser)
        case "make":
            return MakeQueries(code_buf,tree,l,parser)
        case _:
            raise AssertionError(UN_SUPP_LANG)

def parse_file(file_path:Path) -> TSResult:
    """Factory from string"""

    lang = "hcl" if file_path.suffix in [".tfvars",".tf"] else "make"
    l = ts_coll.get_language(lang)
    parser = ts_coll.get_parser(lang) 

    # open file
    with open(file_path,"rb") as f:
        code_buf = f.read()
        tree = parser.parse(code_buf)

    match lang:
        case "hcl":
            return HCLQueries(code_buf,tree,l,parser)
        case "make":
            return MakeQueries(code_buf,tree,l,parser)




