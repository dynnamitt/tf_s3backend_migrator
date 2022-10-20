from ts_language_collection import Node
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
def get_text(buf:bytes,node:Node) -> str:
    return buf[node.start_byte:node.end_byte].decode('utf8')


