from dataclasses import dataclass
from typing import Optional
import ts_language_collection as ts_coll
from pathlib import Path


@dataclass()
class TSResult:
    code: bytes
    tree: ts_coll.Tree
    lang: ts_coll.Language
    parser: ts_coll.Parser
    
    # https://stackoverflow.com/questions
    #       /63635500/how-to-get-the-values-from-nodes-in-tree-sitter
    def node_text(self,node:ts_coll.Node) -> str:
        return self.code[node.start_byte:node.end_byte].decode('utf8')



class HCLQueries(TSResult):

    def attr_expr(self, key_name:Optional[str]=None):
        key_name_q = f'(#eq? @key "{key_name}" )' if key_name else ''
        scm = f"""(
        (attribute (identifier) @key
            (expression (expr_term (template_expr (quoted_template) @val) )))
        {key_name_q}
        )
        """
        query = self.lang.query(scm)
        # clever zip_from_i*2
        i_captures = iter(query.captures(self.tree.root_node))
        cap_paired = zip(i_captures,i_captures)
    
        return [(self.node_text(k[0]), self.node_text(v[0])) 
                for k,v in cap_paired]


def parse_file(file_path:Path) -> TSResult:
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
            return TSResult(code_buf,tree,l,parser)
            # pass basically that
        case default:
            raise AssertionError("That language is not supported here!")




