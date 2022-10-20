import click
import sys
import ts_language_collection as ts
import queries as q_set

def die(s,code=1):
    sys.stderr.write(str(s)+"\n")
    sys.exit(code)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("file-path", 
                type=click.Path(exists=True,resolve_path=True),
                nargs=1)
def hcl_tfvars(file_path):

    hcl = ts.get_language("hcl")
    parser = ts.get_parser("hcl") 

    # open file
    with open(file_path,"rb") as f:
        code_buf = f.read()
        tree = parser.parse(code_buf)

    print(tree.root_node.sexp()) 
    print("-------------")

    part_queries = [q_set.hcl_q["attr_expr_kv"](k) 
        for k in ["role_arn","region","bucket","dynamodb_table"]]

    q1 = "\n".join(part_queries)
    
    query = hcl.query(q1)

    # clever zip_from_i*2
    i_captures = iter(query.captures(tree.root_node))
    cap_paired = zip(i_captures,i_captures)
    
    for k,v in cap_paired: #

        k_ = q_set.get_text(code_buf,k[0])
        v_ = q_set.get_text(code_buf,v[0])
        print(k_,v_)


if __name__ == '__main__':
    cli()
