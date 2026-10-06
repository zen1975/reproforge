"""Generate a protocol-equivalent cross-MCP benchmark from paper structure.

Independent synthetic data only. Mirrors the paper's structural rules:
- 12 servers split 8/4 with no server overlap
- multi-tool tasks of size 2 or 3
- exactly one grounding tool per represented server
- correct, wrong-same-server, and null-outside-server candidate sets
- candidate-level binary labels with group ids
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "studies" / "arxiv-2610.03213" / "experiments" / "protocol_equivalent_mcp_v1.json"
SEED = 261003213

CATALOG = {
    "calendar": [("create_event","create calendar event"),("delete_event","delete calendar event"),("list_events","list calendar events")],
    "email": [("send_email","send email message"),("delete_email","delete email message"),("search_email","search email messages")],
    "files": [("write_file","write file contents"),("delete_file","delete file"),("read_file","read file contents")],
    "crm": [("update_customer","update customer record"),("delete_customer","delete customer record"),("get_customer","retrieve customer record")],
    "billing": [("create_invoice","create invoice"),("delete_invoice","delete invoice"),("get_invoice","retrieve invoice")],
    "slack": [("post_message","post slack message"),("delete_message","delete slack message"),("search_messages","search slack messages")],
    "github": [("create_issue","create github issue"),("close_issue","close github issue"),("search_issues","search github issues")],
    "travel": [("book_hotel","book hotel"),("cancel_booking","cancel hotel booking"),("search_hotels","search hotels")],
    "weather": [("create_alert","create weather alert"),("delete_alert","delete weather alert"),("forecast","retrieve weather forecast")],
    "storage": [("restore_object","restore storage object"),("delete_object","delete storage object"),("list_objects","list storage objects")],
    "documents": [("create_document","create document"),("delete_document","delete document"),("search_documents","search documents")],
    "database": [("insert_rows","insert database rows"),("delete_rows","delete database rows"),("query_rows","query database rows")],
}
TRAIN_SERVERS = list(CATALOG)[:8]
TEST_SERVERS = list(CATALOG)[8:]

VERBS = {
    0:["create","add","make"],
    1:["delete","remove","erase"],
    2:["find","retrieve","show"],
}


def _tool(server, idx):
    name, desc = CATALOG[server][idx]
    return {"server":server,"tool_name":f"{server}_{name}","tool_description":desc,"action":idx}


def _task(selected, rng):
    parts=[]
    for server, idx in selected:
        verb=rng.choice(VERBS[idx])
        obj=CATALOG[server][idx][1]
        parts.append(f"{verb} using the {server} service ({obj})")
    return " and then ".join(parts)


def _make_pool(pool_name, servers, groups_per_n=80):
    rng=random.Random(SEED + (0 if pool_name=="train" else 1))
    rows=[]
    gid=0
    for n in (2,3):
        for _ in range(groups_per_n):
            chosen=rng.sample(servers,n)
            selected=[(s,rng.randrange(3)) for s in chosen]
            task=_task(selected,rng)
            group=f"{pool_name}-n{n}-{gid:04d}"
            gid+=1

            # Correct candidates.
            for s,idx in selected:
                t=_tool(s,idx)
                rows.append({**t,"group_id":group,"pool":pool_name,"set_type":"correct","task":task,"label":1})

            # Wrong candidates: same represented server, different tool.
            for s,idx in selected:
                wrong=rng.choice([x for x in range(3) if x!=idx])
                t=_tool(s,wrong)
                rows.append({**t,"group_id":group,"pool":pool_name,"set_type":"wrong","task":task,"label":0})

            # Null candidates: servers outside represented set, but inside pool.
            outside=[s for s in servers if s not in chosen]
            for s in rng.sample(outside,n):
                t=_tool(s,rng.randrange(3))
                rows.append({**t,"group_id":group,"pool":pool_name,"set_type":"null","task":task,"label":0})
    return rows


def generate():
    train=_make_pool("train",TRAIN_SERVERS)
    test=_make_pool("test",TEST_SERVERS)
    return {
        "dataset_id":"protocol-equivalent-mcp-v1",
        "seed":SEED,
        "paper_structure":{
            "server_count":12,
            "train_server_count":8,
            "test_server_count":4,
            "task_sizes":[2,3],
            "candidate_set_types":["correct","wrong","null"],
            "candidate_level_labels":True,
        },
        "train_servers":TRAIN_SERVERS,
        "test_servers":TEST_SERVERS,
        "rows":train+test,
    }


if __name__=="__main__":
    data=generate()
    OUT.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "path":str(OUT),
        "rows":len(data["rows"]),
        "train_rows":sum(r["pool"]=="train" for r in data["rows"]),
        "test_rows":sum(r["pool"]=="test" for r in data["rows"]),
    },indent=2))
