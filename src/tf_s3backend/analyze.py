from . import psudo_workspaces as pw
from . import queries as q
from dataclasses import dataclass, field
from typing import List, Optional

from pathlib import Path
from pprint import pprint


@dataclass()
class TFProjectSummary:
    type: str = ""
    backend: List[dict] = field(default_factory=list)


def main(tf_dir: Path) -> Optional[TFProjectSummary]:
    WRK_SPC_KEY = "WRK_SPACE"
    ADMIN_ROLE_FALLBACK = "bfadmin"
    summary = TFProjectSummary()
    try:
        legacy_p = pw.get_legacy_project(tf_dir)
        summary.type = legacy_p.pattern

        for w in legacy_p.workspaces:
            fallback_acc_no = f"__{w.name.upper()}__"
            init_vals = q.init_vals(q.parse_file(w.init_file))
            if not init_vals.get("role_arn"):
                # do check

                normal_vars = q.parse_file(w.input_file).key_values()
                acc_ = normal_vars.get(
                    "account", init_vals.get("account", fallback_acc_no)
                )
                init_vals["role_arn"] = normal_vars.get(
                    "role_arn",
                    f"arn:aws:iam::{acc_}:role/{ADMIN_ROLE_FALLBACK}",
                )
            init_vals[WRK_SPC_KEY] = w.name
            summary.backend.append(init_vals)
        return summary

    except LookupError as e:
        b = q.scan_dir_backend_kvs(tf_dir)
        if len(b.keys()) > 0:
            summary.type = "WORKSPACES"
            b[WRK_SPC_KEY] = "_ALL_"
            summary.backend.append(b)
            return summary
        else:
            return None
