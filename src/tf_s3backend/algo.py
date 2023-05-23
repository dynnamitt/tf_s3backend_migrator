from typing import Optional,Tuple

ConfTree = dict[str, dict[str, str]]

def flatten(ls):
    return [itm  for sublist in ls for itm in sublist]

def extract_dups(data: ConfTree) -> Tuple[ConfTree,dict]:

    union_prop_names = set([n for conf in data.values() for n in conf])
    # print(f"{union_prop_names=}")
    
    def identical_across(prop:str)-> Optional[str]:
        val_set = {wconf.get(prop) for wconf in data.values()}
        if len(val_set) == 1:
            return prop

    identical_props = {identical_across(kn) for kn in union_prop_names }
    # print(f"{identical_props=}") 
    
    w1_vals = list(data.values())[0]
    common_result = { k:v for k,v in w1_vals.items() if k in identical_props} 
    dup_free_data = { wrkspc:{k:v for k,v in conf.items() if k not in identical_props } for wrkspc,conf in data.items()}
    return (dup_free_data,common_result)
