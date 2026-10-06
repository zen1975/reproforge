"""Generate protocol-equivalent cross-MCP task/tool pairs inspired by arXiv:2610.03213.

Independent synthetic data only. Does not use or reproduce the authors' dataset.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "studies" / "arxiv-2610.03213" / "experiments" / "protocol_equivalent_cross_mcp_v1.json"
SEED = 261003213

CATALOG = {
    "calendar": [
        ("create_event", "create a calendar event"),
        ("delete_event", "delete a calendar event"),
        ("list_events", "list calendar events"),
    ],
    "email": [
        ("send_email", "send an email message"),
        ("delete_email", "delete an email message"),
        ("search_email", "search email messages"),
    ],
    "files": [
        ("write_file", "write a file"),
        ("delete_file", "delete a file"),
        ("read_file", "read a file"),
    ],
    "crm": [
        ("update_customer", "update a customer record"),
        ("delete_customer", "delete a customer record"),
        ("get_customer", "retrieve a customer record"),
    ],
    "billing": [
        ("create_invoice", "create an invoice"),
        ("delete_invoice", "delete an invoice"),
        ("get_invoice", "retrieve an invoice"),
    ],
    "slack": [
        ("post_message", "post a slack message"),
        ("delete_message", "delete a slack message"),
        ("search_messages", "search slack messages"),
    ],
    "github": [
        ("create_issue", "create a github issue"),
        ("close_issue", "close a github issue"),
        ("search_issues", "search github issues"),
    ],
    "travel": [
        ("book_hotel", "book a hotel"),
        ("cancel_booking", "cancel a hotel booking"),
        ("search_hotels", "search hotels"),
    ],
    "weather": [
        ("create_alert", "create a weather alert"),
        ("delete_alert", "delete a weather alert"),
        ("forecast", "retrieve a weather forecast"),
    ],
    "storage": [
        ("restore_backup", "restore a backup"),
        ("delete_object", "delete a storage object"),
        ("list_objects", "list storage objects"),
    ],
    "translate": [
        ("translate_text", "translate text to another language"),
        ("redact_text", "redact text"),
        ("detect_language", "detect text language"),
    ],
    "database": [
        ("insert_rows", "insert database rows"),
        ("delete_rows", "delete database rows"),
        ("query_rows", "query database rows"),
    ],
}

SPLITS = {
    "train": ["calendar", "email", "files", "crm", "billing", "slack", "github", "travel"],
    "validation": ["weather", "storage"],
    "test": ["translate", "database"],
}

TASK_VERBS = {
    "create_event": "schedule a meeting",
    "delete_event": "cancel a meeting",
    "list_events": "show upcoming meetings",
    "send_email": "send a project update",
    "delete_email": "remove an old email",
    "search_email": "find an email about oauth",
    "write_file": "save a report file",
    "delete_file": "remove an obsolete file",
    "read_file": "read a quarterly report",
    "update_customer": "update customer 42",
    "delete_customer": "remove customer 42",
    "get_customer": "look up customer 42",
    "create_invoice": "issue an invoice",
    "delete_invoice": "remove an invoice",
    "get_invoice": "retrieve an invoice",
    "post_message": "post a launch update",
    "delete_message": "remove a slack post",
    "search_messages": "find slack posts about release",
    "create_issue": "open a github issue",
    "close_issue": "close a github issue",
    "search_issues": "find github issues about oauth",
    "book_hotel": "book a hotel",
    "cancel_booking": "cancel a hotel reservation",
    "search_hotels": "find available hotels",
    "create_alert": "set a weather alert",
    "delete_alert": "remove a weather alert",
    "forecast": "check tomorrow's forecast",
    "restore_backup": "restore a storage backup",
    "delete_object": "remove a storage object",
    "list_objects": "show storage objects",
    "translate_text": "translate a note into french",
    "redact_text": "redact sensitive text",
    "detect_language": "identify a note's language",
    "insert_rows": "insert a database row",
    "delete_rows": "delete a database row",
    "query_rows": "find matching database rows",
}


def _tool(server, index):
    name, description = CATALOG[server][index]
    return {
        "server": server,
        "name": f"{server}_{name}",
        "description": description,
    }


def _task_for(tools):
    intents = [TASK_VERBS[t["name"].split("_", 1)[1]] for t in tools]
    return " and then ".join(intents)


def _row(group_id, split, task, candidate, relevant, set_type):
    return {
        "group_id": group_id,
        "split": split,
        "task": task,
        "server": candidate["server"],
        "tool_name": candidate["name"],
        "tool_description": candidate["description"],
        "label": int(relevant),
        "set_type": set_type,
        "target_response": {
            "reasoning": (
                "The candidate tool is directly required by the task."
                if relevant
                else "The candidate tool is not required by the task."
            ),
            "appropriate": bool(relevant),
        },
    }


def generate(groups_per_size_per_split=40):
    rng = random.Random(SEED)
    rows = []
    for split, servers in SPLITS.items():
        all_servers = list(servers)
        for n_tools in (2, 3):
            for group_idx in range(groups_per_size_per_split):
                selected_servers = rng.sample(all_servers, n_tools)
                grounding = [_tool(server, rng.randrange(len(CATALOG[server]))) for server in selected_servers]
                task = _task_for(grounding)
                base = f"{split}-n{n_tools}-{group_idx:04d}"

                for candidate in grounding:
                    rows.append(_row(base+"-correct", split, task, candidate, True, "correct"))

                wrong = []
                for candidate in grounding:
                    options = [
                        _tool(candidate["server"], i)
                        for i in range(len(CATALOG[candidate["server"]]))
                        if _tool(candidate["server"], i)["name"] != candidate["name"]
                    ]
                    wrong.append(rng.choice(options))
                for candidate in wrong:
                    rows.append(_row(base+"-wrong", split, task, candidate, False, "wrong"))

                null_servers = [s for s in all_servers if s not in selected_servers]
                if len(null_servers) >= n_tools:
                    chosen_null = rng.sample(null_servers, n_tools)
                else:
                    chosen_null = [rng.choice(null_servers) for _ in range(n_tools)]
                null = [_tool(server, rng.randrange(len(CATALOG[server]))) for server in chosen_null]
                for candidate in null:
                    rows.append(_row(base+"-null", split, task, candidate, False, "null"))

    payload = {
        "dataset_id": "protocol-equivalent-cross-mcp-v1",
        "seed": SEED,
        "protocol": {
            "task_tool_counts": [2, 3],
            "exactly_one_grounding_tool_per_represented_server": True,
            "candidate_set_types": ["correct", "wrong", "null"],
            "wrong_replacement_same_server": True,
            "null_servers_disjoint_from_grounding_servers_when_possible": True,
            "candidate_level_labels": True,
            "structured_target": {"reasoning": "string", "appropriate": "boolean"},
        },
        "splits": SPLITS,
        "rows": rows,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


if __name__ == "__main__":
    data = generate()
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    counts = {
        split: sum(r["split"] == split for r in data["rows"])
        for split in SPLITS
    }
    print(json.dumps({"path": str(OUT), "counts": counts, "sha256": data["content_sha256"]}, indent=2))
