"""Generate deterministic task-tool SFT data with family-disjoint splits."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "studies" / "arxiv-2610.03213" / "experiments" / "task_tool_sft_family_split_v1.json"

FAMILIES = {
    "calendar": {
        "object": "calendar event",
        "tools": {
            "create": ("calendar_create_event", "create a calendar event with date time and attendees"),
            "delete": ("calendar_delete_event", "delete an existing calendar event"),
            "list": ("calendar_list_events", "list calendar events for a date range"),
        },
        "tasks": {
            "create": ["schedule {obj}", "add {obj}", "book {obj}", "make a new {obj}"],
            "delete": ["remove {obj}", "cancel {obj}", "delete {obj}", "erase {obj}"],
            "list": ["show my {obj}s", "list {obj}s", "find existing {obj}s", "display {obj}s"],
        },
    },
    "email": {
        "object": "email message",
        "tools": {
            "create": ("email_send", "send an email message to recipients"),
            "delete": ("email_delete", "delete an email message"),
            "list": ("email_search", "search and list email messages"),
        },
        "tasks": {
            "create": ["send an {obj}", "dispatch an {obj}", "write and send an {obj}", "deliver an {obj}"],
            "delete": ["remove an {obj}", "delete an {obj}", "erase an {obj}", "trash an {obj}"],
            "list": ["find {obj}s", "search {obj}s", "list {obj}s", "show matching {obj}s"],
        },
    },
    "files": {
        "object": "file",
        "tools": {
            "create": ("file_write", "write or create file contents at a path"),
            "delete": ("file_delete", "delete a file from storage"),
            "list": ("file_read", "read file contents from a path"),
        },
        "tasks": {
            "create": ["write a {obj}", "create a {obj}", "save a new {obj}", "store content in a {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "erase the {obj}", "discard the {obj}"],
            "list": ["read the {obj}", "open the {obj}", "show the {obj} contents", "retrieve the {obj} contents"],
        },
    },
    "crm": {
        "object": "customer record",
        "tools": {
            "create": ("crm_update_customer", "update or write customer record fields"),
            "delete": ("crm_delete_customer", "delete a customer record"),
            "list": ("crm_get_customer", "retrieve a customer record by identifier"),
        },
        "tasks": {
            "create": ["update the {obj}", "edit the {obj}", "change the {obj}", "write changes to the {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "erase the {obj}", "purge the {obj}"],
            "list": ["look up the {obj}", "get the {obj}", "retrieve the {obj}", "show the {obj}"],
        },
    },
    "billing": {
        "object": "invoice",
        "tools": {
            "create": ("billing_create_invoice", "create an invoice for an order"),
            "delete": ("billing_delete_invoice", "delete an invoice"),
            "list": ("billing_get_invoice", "retrieve invoice details"),
        },
        "tasks": {
            "create": ["create an {obj}", "issue an {obj}", "generate an {obj}", "make a new {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "void and delete the {obj}", "erase the {obj}"],
            "list": ["get the {obj}", "retrieve the {obj}", "show the {obj}", "look up the {obj}"],
        },
    },
    "slack": {
        "object": "slack message",
        "tools": {
            "create": ("slack_post_message", "post a message to a slack channel"),
            "delete": ("slack_delete_message", "delete a slack message"),
            "list": ("slack_search_messages", "search slack messages"),
        },
        "tasks": {
            "create": ["post a {obj}", "send a {obj}", "publish a {obj}", "write a {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "erase the {obj}", "take down the {obj}"],
            "list": ["find {obj}s", "search {obj}s", "list matching {obj}s", "look up {obj}s"],
        },
    },
    "github": {
        "object": "github issue",
        "tools": {
            "create": ("github_create_issue", "create a github issue"),
            "delete": ("github_close_issue", "close an existing github issue"),
            "list": ("github_search_issues", "search github issues"),
        },
        "tasks": {
            "create": ["create a {obj}", "open a {obj}", "file a {obj}", "add a new {obj}"],
            "delete": ["close the {obj}", "resolve and close the {obj}", "shut the {obj}", "mark the {obj} closed"],
            "list": ["find {obj}s", "search {obj}s", "list {obj}s", "look up {obj}s"],
        },
    },
    "travel": {
        "object": "hotel booking",
        "tools": {
            "create": ("travel_book_hotel", "book hotel accommodation"),
            "delete": ("travel_cancel_booking", "cancel a hotel booking"),
            "list": ("travel_search_hotels", "search available hotels"),
        },
        "tasks": {
            "create": ["make a {obj}", "reserve a hotel", "book accommodation", "create a {obj}"],
            "delete": ["cancel the {obj}", "remove the {obj}", "void the {obj}", "delete the {obj}"],
            "list": ["find hotels", "search hotels", "list available hotels", "show hotel options"],
        },
    },
    "weather": {
        "object": "weather alert",
        "tools": {
            "create": ("weather_alert_create", "create a weather alert"),
            "delete": ("weather_alert_delete", "delete a weather alert"),
            "list": ("weather_forecast", "retrieve weather forecast information"),
        },
        "tasks": {
            "create": ["create a {obj}", "set a {obj}", "add a {obj}", "make a new {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "cancel the {obj}", "erase the {obj}"],
            "list": ["get the weather forecast", "show the forecast", "retrieve weather information", "check the weather"],
        },
    },
    "storage": {
        "object": "storage object",
        "tools": {
            "create": ("storage_restore_backup", "restore an object or backup into storage"),
            "delete": ("storage_delete_object", "delete an object from storage"),
            "list": ("storage_list_objects", "list objects in storage"),
        },
        "tasks": {
            "create": ["restore the {obj}", "recover the {obj}", "put back the {obj}", "recreate the {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "erase the {obj}", "purge the {obj}"],
            "list": ["list {obj}s", "show {obj}s", "find {obj}s", "display stored objects"],
        },
    },
    "translate": {
        "object": "text",
        "tools": {
            "create": ("translate_text", "translate text into another language"),
            "delete": ("redact_text", "remove or redact text content"),
            "list": ("detect_language", "detect the language of text"),
        },
        "tasks": {
            "create": ["translate this {obj}", "convert this {obj} into french", "render this {obj} in another language", "translate the supplied {obj}"],
            "delete": ["redact this {obj}", "remove this {obj}", "erase the {obj}", "delete the supplied {obj}"],
            "list": ["detect the language of this {obj}", "identify this {obj}'s language", "tell me the language of this {obj}", "classify the language of this {obj}"],
        },
    },
    "database": {
        "object": "database row",
        "tools": {
            "create": ("database_insert_rows", "insert rows into a database table"),
            "delete": ("database_delete_rows", "delete rows from a database table"),
            "list": ("database_query", "query and retrieve rows from a database"),
        },
        "tasks": {
            "create": ["insert a {obj}", "add a {obj}", "create a {obj}", "write a new {obj}"],
            "delete": ["remove the {obj}", "delete the {obj}", "erase the {obj}", "purge the {obj}"],
            "list": ["query the {obj}s", "retrieve {obj}s", "list {obj}s", "find matching {obj}s"],
        },
    },
}

SPLITS = {
    "train": ["calendar", "email", "files", "crm", "billing", "slack", "github", "travel"],
    "dev": ["weather", "storage"],
    "test": ["translate", "database"],
}


def generate():
    rows = []
    for split, families in SPLITS.items():
        for family in families:
            spec = FAMILIES[family]
            for action, templates in spec["tasks"].items():
                for template_idx, template in enumerate(templates):
                    task = template.format(obj=spec["object"])
                    for candidate_action, (tool_name, tool_description) in spec["tools"].items():
                        rows.append(
                            {
                                "id": f"{split}-{family}-{action}-{template_idx}-{candidate_action}",
                                "split": split,
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
        "dataset_id": "task-tool-sft-family-split-v1",
        "purpose": "Independent deterministic synthetic SFT dataset; not author data.",
        "splits": SPLITS,
        "rows": rows,
    }


if __name__ == "__main__":
    data = generate()
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    counts = {
        split: sum(row["split"] == split for row in data["rows"])
        for split in SPLITS
    }
    print(json.dumps({"path": str(OUT), "counts": counts}, indent=2, sort_keys=True))
