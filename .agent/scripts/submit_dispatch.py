import argparse
import json
import os
import re
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUESTS_DIR = os.path.join(BASE_DIR, "requests")
AGENT_ALIASES = {
    "claudecode": "claude",
    "geminicli": "gemini",
    "codexcli": "codex",
}


def normalize(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", value.lower())
    return AGENT_ALIASES.get(normalized, normalized)


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a dynamic multi-agent dispatch request")
    parser.add_argument("--request-id", default="", help="Optional stable request id")
    parser.add_argument("--requester", required=True, help="Agent issuing the request")
    parser.add_argument("--parent-task-id", default="", help="Parent task id")
    parser.add_argument("--fan-in", default="all", choices=["all"])
    parser.add_argument("--callback-agent", default="", help="Agent that should receive the callback")
    parser.add_argument("--callback-content", default="", help="Callback task content")
    parser.add_argument(
        "--subtask",
        action="append",
        required=True,
        help='JSON object, for example {"label":"research","agent":"claude","content":"Gather facts"}',
    )
    args = parser.parse_args()

    os.makedirs(REQUESTS_DIR, exist_ok=True)

    subtasks = []
    for raw in args.subtask:
        subtasks.append(json.loads(raw))

    request_id = slugify(args.request_id) if args.request_id else datetime.utcnow().strftime("req_%Y%m%d_%H%M%S_%f")
    manifest = {
        "request_id": request_id,
        "requester": normalize(args.requester),
        "parent_task_id": args.parent_task_id or None,
        "fan_in": args.fan_in,
        "subtasks": subtasks,
    }

    if args.callback_content:
        manifest["callback"] = {
            "agent": normalize(args.callback_agent or args.requester),
            "content": args.callback_content,
        }

    path = os.path.join(REQUESTS_DIR, f"{request_id}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(path)


if __name__ == "__main__":
    main()
