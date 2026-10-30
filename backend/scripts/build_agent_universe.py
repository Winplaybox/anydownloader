"""
Build backend/data/agent_universe_v3.json from AI_Agent_Universe_Master_Catalog.xlsx.

    pip install openpyxl
    python backend/scripts/build_agent_universe.py path/to/AI_Agent_Universe_Master_Catalog.xlsx

The workbook's per-row text for inputs/outputs/workflow/architecture/review is identical for every
agent, so it is stored once in "shared" instead of 1,200 times. Rich behaviour comes from the
playbooks in services/gravityclaw/agent_universe.py.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "agent_universe_v3.json")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def rows(ws):
    data = [r for r in ws.iter_rows(values_only=True)]
    hdr = [str(h).strip() if h is not None else "" for h in data[0]]
    return [dict(zip(hdr, r)) for r in data[1:] if any(c is not None for c in r)]


def common(values):
    c = Counter(values)
    return c.most_common(1)[0][0] if c else ""


def main(path: str) -> None:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    agents_raw = rows(wb["Agent Catalog"])
    scripts_raw = rows(wb["Script Agents"])
    domains_raw = rows(wb["Domains"])
    functions_raw = rows(wb["Functions"])
    outputs_raw = rows(wb["Output Types"])
    arch_raw = rows(wb["Architecture & Workflows"])

    config = defaultdict(list)
    for r in rows(wb["Configuration Lists"]):
        if r.get("Dimension") and r.get("Option"):
            config[str(r["Dimension"]).strip()].append(str(r["Option"]).strip())

    domains = [{"id": d["Domain ID"], "name": d["Domain"], "group": d["Domain Group"], "scope": d["Scope / Examples"]}
               for d in domains_raw]
    dom_by_name = {d["name"]: d["id"] for d in domains}

    agents = []
    for a in agents_raw:
        agents.append({
            "id": a["Agent ID"],
            "kind": "agent",
            "name": a["Agent Name"],
            "domain_id": dom_by_name.get(a["Domain"], ""),
            "domain": a["Domain"],
            "group": a["Domain Group"],
            "function": a["Agent Function"],
            "purpose": a["Primary Purpose"],
        })

    scripts = []
    for s in scripts_raw:
        scripts.append({
            "id": s["Script Agent ID"],
            "kind": "script",
            "name": s["Agent Name"],
            "family": s["Script Family"],
            "deliverable": s["Typical Deliverable"],
        })

    shared = {
        "agent": {
            "inputs": common(a["Typical Inputs"] for a in agents_raw),
            "outputs": common(a["Typical Outputs"] for a in agents_raw),
            "workflow": common(a["Suggested Workflow"] for a in agents_raw),
            "architecture": common(a["Architecture"] for a in agents_raw),
            "human_review": common(a["Human Review"] for a in agents_raw),
        },
        "script": {
            "workflow": common(s["Suggested Workflow"] for s in scripts_raw),
            "checks": common(s["Recommended Checks"] for s in scripts_raw),
            "customization": common(s["Customization Ideas"] for s in scripts_raw),
        },
    }

    catalog = {
        "version": "3.0.0",
        "source": os.path.basename(path),
        "counts": {"agents": len(agents), "script_agents": len(scripts), "domains": len(domains)},
        "shared": shared,
        "domains": domains,
        "functions": [{"id": f["Function ID"], "name": f["Agent Function"], "definition": f["Definition"]} for f in functions_raw],
        "output_types": [{"id": o["Output ID"], "name": o["Output Type"], "definition": o["Definition"]} for o in outputs_raw],
        "architectures": [{"name": r["Name"], "description": r["Description"]} for r in arch_raw if r["Kind"] == "Architecture"],
        "workflows": [{"name": r["Name"], "description": r["Description"]} for r in arch_raw if r["Kind"] == "Workflow"],
        "config": {k.lower() + "s": v for k, v in config.items()},
        "agents": agents,
        "script_agents": scripts,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT}: {len(agents)} agents, {len(scripts)} script agents, {len(domains)} domains, "
          f"{os.path.getsize(OUT) // 1024} KB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
