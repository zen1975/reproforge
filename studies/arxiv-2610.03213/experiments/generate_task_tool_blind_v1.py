"""Generate a frozen blind task-tool benchmark with unseen tool families."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "studies" / "arxiv-2610.03213" / "experiments" / "task_tool_blind_v1.json"

FAMILIES = {
    "documents": {
        "object": "document",
        "tools": {
            "create": ("docs_create", "create a new document"),
            "delete": ("docs_delete", "delete an existing document"),
            "list": ("docs_search", "search and retrieve documents"),
        },
        "tasks": {
            "create": ["create a {obj}", "write a new {obj}", "make a {obj}", "start a fresh {obj}"],
            "delete": ["delete the {obj}", "remove the {obj}", "erase the {obj}", "discard the {obj}"],
            "list": ["find the {obj}", "search {obj}s", "retrieve the {obj}", "show matching {obj}s"],
        },
    },
    "commerce": {
        "object": "product listing",
        "tools": {
            "create": ("commerce_create_listing", "create a product listing"),
            "delete": ("commerce_delete_listing", "delete a product listing"),
            "list": ("commerce_search_listings", "search product listings"),
        },
        "tasks": {
            "create": ["create a {obj}", "publish a {obj}", "add a {obj}", "make a new {obj}"],
            "delete": ["delete the {obj}", "remove the {obj}", "unpublish and delete the {obj}", "erase the {obj}"],
            "list": ["find {obj}s", "search {obj}s", "list {obj}s", "show matching {obj}s"],
        },
    },
    "identity": {
        "object": "user account",
        "tools": {
            "create": ("identity_create_user", "create a user account"),
            "delete": ("identity_delete_user", "delete a user account"),
            "list": ("identity_get_user", "retrieve a user account"),
        },
        "tasks": {
            "create": ["create a {obj}", "add a {obj}", "register a {obj}", "provision a {obj}"],
            "delete": ["delete the {obj}", "remove the {obj}", "deprovision the {obj}", "erase the {obj}"],
            "list": ["get the {obj}", "retrieve the {obj}", "look up the {obj}", "show the {obj}"],
        },
    },
    "notifications": {
        "object": "notification",
        "tools": {
            "create": ("notify_send", "send a notification to a recipient"),
            "delete": ("notify_delete", "delete a notification"),
            "list": ("notify_list", "list notifications"),
        },
        "tasks": {
            "create": ["send a {obj}", "dispatch a {obj}", "create and send a {obj}", "deliver a {obj}"],
            "delete": ["delete the {obj}", "remove the {obj}", "erase the {obj}", "clear the {obj}"],
            "list": ["list {obj}s", "show {obj}s", "find {obj}s", "retrieve {obj}s"],
        },
    },
}


def generate():
    rows = []
    for family, spec in FAMILIES.items():
        for action, templates in spec["tasks"].items():
            for template_idx, template in enumerate(templates):
                task = template.format(obj=spec["object"])
                for candidate_action, (tool_name, tool_description) in spec["tools"].items():
                    rows.append(
                        {
                            "id": f"blind-{family}-{action}-{template_idx}-{candidate_action}",
                            "family": family,
                            "target_action": action,
                            "candidate_action": candidate_action,
                            "task": task,
                            "tool_name": tool_name,
                            "tool_description": tool_description,
                            "label": 1 if action == candidate_action else 0,
                        }
                    )
    return {
        "dataset_id": "task-tool-blind-v1",
        "frozen_at": "2026-10-06",
        "purpose": "Frozen unseen-family benchmark created before evaluation; not author data.",
        "families": sorted(FAMILIES),
        "rows": rows,
    }


if __name__ == "__main__":
    data = generate()
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": str(OUT), "count": len(data["rows"])}, indent=2))
