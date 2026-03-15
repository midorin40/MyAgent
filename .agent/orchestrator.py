import argparse
import json
import os
import re
import time
from datetime import UTC, datetime
from typing import Dict, List, Optional


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_FILE = os.path.join(BASE_DIR, "task.md")
ORDERS_DIR = os.path.join(BASE_DIR, "orders")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
REQUESTS_DIR = os.path.join(BASE_DIR, "requests")
REQUESTS_PROCESSED_DIR = os.path.join(REQUESTS_DIR, "processed")
STATE_DIR = os.path.join(BASE_DIR, "state")

POLL_SECONDS = 5
STATUS_PENDING = "pending"
STATUS_DISPATCHED = "dispatched"
STATUS_COMPLETED = "completed"
AGENT_ALIASES = {
    "claudecode": "claude",
    "geminicli": "gemini",
    "codexcli": "codex",
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] [ORCHESTRATOR] {msg}", flush=True)


def ensure_dirs() -> None:
    for path in [ORDERS_DIR, RESULTS_DIR, REQUESTS_DIR, REQUESTS_PROCESSED_DIR, STATE_DIR]:
        os.makedirs(path, exist_ok=True)


def atomic_write_text(path: str, content: str) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(tmp_path, path)


def atomic_write_json(path: str, payload: Dict) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def normalize_agent_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", name.lower())
    normalized = AGENT_ALIASES.get(normalized, normalized)
    if not normalized:
        raise ValueError(f"Invalid agent name: {name!r}")
    return normalized


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "task"


def result_filename(agent_name: str, task_id: str) -> str:
    return f"result_{normalize_agent_name(agent_name)}_{task_id}.md"


def result_path(agent_name: str, task_id: str) -> str:
    return os.path.join(RESULTS_DIR, result_filename(agent_name, task_id))


def order_path(agent_name: str, task_id: str) -> str:
    return os.path.join(ORDERS_DIR, f"{normalize_agent_name(agent_name)}_{task_id}.md")


def load_text_if_exists(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def get_task_state() -> List[Dict]:
    if not os.path.exists(TASK_FILE):
        return []

    try:
        with open(TASK_FILE, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except Exception as exc:
        log(f"Error reading task file: {exc}")
        return []

    tasks = []
    for line in lines:
        if "|" not in line:
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 6 or parts[1] == "#" or parts[1].startswith("---"):
            continue

        status_match = re.search(r"\[( |x|/|X)\]", parts[5])
        if not status_match:
            continue

        tasks.append(
            {
                "id": parts[1],
                "content": parts[2],
                "agent": parts[3],
                "deps": parts[4],
                "status": status_match.group(1),
            }
        )
    return tasks


def update_task_status(task_id: str, status: str) -> None:
    if not os.path.exists(TASK_FILE):
        return

    try:
        with open(TASK_FILE, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except Exception as exc:
        log(f"Error reading task file for update: {exc}")
        return

    new_lines = []
    for line in lines:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 6 and parts[1] == task_id:
            line = re.sub(r"\[( |x|/|X)\]", f"[{status}]", line)
        new_lines.append(line)

    try:
        atomic_write_text(TASK_FILE, "".join(new_lines))
    except Exception as exc:
        log(f"Error updating task status: {exc}")


def build_order_instruction(
    *,
    agent_name: str,
    task_id: str,
    content: str,
    parent_task_id: Optional[str] = None,
    request_id: Optional[str] = None,
    extra_context: Optional[List[str]] = None,
) -> str:
    extra_context = extra_context or []
    output_path = os.path.join(".agent", "results", result_filename(agent_name, task_id))

    lines = [
        f"# Task Order ({task_id})",
        "",
        f"- Agent: {agent_name}",
        f"- Task ID: {task_id}",
        f"- Parent Task ID: {parent_task_id or 'none'}",
        f"- Request ID: {request_id or 'none'}",
        f"- Result File: {output_path}",
        "",
        "## Objective",
        content,
        "",
    ]

    if extra_context:
        lines.extend(["## Context", *extra_context, ""])

    lines.extend(
        [
            "## Completion",
            f"Write your final report to `{output_path}`.",
            "If you need other agents to help, create a dispatch request instead of waiting interactively.",
        ]
    )
    return "\n".join(lines) + "\n"


def dispatch_order(
    *,
    agent_name: str,
    task_id: str,
    content: str,
    parent_task_id: Optional[str] = None,
    request_id: Optional[str] = None,
    extra_context: Optional[List[str]] = None,
) -> bool:
    target_order_path = order_path(agent_name, task_id)
    if os.path.exists(target_order_path):
        return False

    report_path = result_path(agent_name, task_id)
    if os.path.exists(report_path):
        return False

    instruction = build_order_instruction(
        agent_name=agent_name,
        task_id=task_id,
        content=content,
        parent_task_id=parent_task_id,
        request_id=request_id,
        extra_context=extra_context,
    )
    atomic_write_text(target_order_path, instruction)
    log(f"Dispatched {task_id} to {normalize_agent_name(agent_name)}")
    return True


def dispatch_static_task(task: Dict) -> None:
    if dispatch_order(
        agent_name=task["agent"],
        task_id=task["id"],
        content=task["content"],
    ):
        update_task_status(task["id"], "/")


def process_static_tasks() -> None:
    tasks = get_task_state()
    if not tasks:
        return

    completed_ids = [task["id"] for task in tasks if task["status"] in ["x", "X"]]

    for task in tasks:
        report_path = result_path(task["agent"], task["id"])
        if os.path.exists(report_path) and task["status"] not in ["x", "X"]:
            update_task_status(task["id"], "x")
            continue

        if task["status"] != " ":
            continue

        deps_raw = task["deps"].replace("#", "").strip()
        deps = [] if not deps_raw or deps_raw.lower() in {"なし", "none", "n/a"} else [d.strip() for d in deps_raw.split(",")]
        if all(dep in completed_ids for dep in deps):
            dispatch_static_task(task)


def make_request_state(manifest: Dict, fallback_name: str) -> Dict:
    request_id = slugify(str(manifest.get("request_id") or fallback_name))
    requester = normalize_agent_name(manifest["requester"])
    subtasks = manifest.get("subtasks")
    if not isinstance(subtasks, list) or not subtasks:
        raise ValueError("Request must include a non-empty subtasks list")

    label_to_task_id: Dict[str, str] = {}
    state_tasks = []
    for index, subtask in enumerate(subtasks, start=1):
        if "agent" not in subtask or "content" not in subtask:
            raise ValueError("Each subtask needs agent and content")

        label = slugify(str(subtask.get("label") or f"task_{index}"))
        task_id = f"{request_id}_{label}"
        if label in label_to_task_id:
            raise ValueError(f"Duplicate subtask label: {label}")

        label_to_task_id[label] = task_id
        state_tasks.append(
            {
                "label": label,
                "task_id": task_id,
                "agent": normalize_agent_name(str(subtask["agent"])),
                "content": str(subtask["content"]),
                "deps": [slugify(str(dep)) for dep in subtask.get("deps", [])],
                "status": STATUS_PENDING,
                "result_file": result_filename(str(subtask["agent"]), task_id),
            }
        )

    for task in state_tasks:
        task["dep_task_ids"] = [label_to_task_id[dep] for dep in task["deps"]]

    callback_manifest = manifest.get("callback")
    callback = None
    if callback_manifest:
        callback_agent = normalize_agent_name(str(callback_manifest.get("agent") or requester))
        callback = {
            "agent": callback_agent,
            "task_id": f"{request_id}_callback",
            "content": str(callback_manifest["content"]),
            "result_file": result_filename(callback_agent, f"{request_id}_callback"),
            "dispatched": False,
        }

    return {
        "request_id": request_id,
        "requester": requester,
        "parent_task_id": manifest.get("parent_task_id"),
        "fan_in": manifest.get("fan_in", "all"),
        "summary_file": f"request_{request_id}_summary.md",
        "status": "active",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tasks": state_tasks,
        "callback": callback,
    }


def process_request_files() -> None:
    for entry in sorted(os.listdir(REQUESTS_DIR)):
        if not entry.endswith(".json"):
            continue

        source_path = os.path.join(REQUESTS_DIR, entry)
        if not os.path.isfile(source_path):
            continue

        try:
            manifest = load_json(source_path)
            state = make_request_state(manifest, os.path.splitext(entry)[0])
            state_path = os.path.join(STATE_DIR, f"{state['request_id']}.json")
            if os.path.exists(state_path):
                raise ValueError(f"Request ID already exists: {state['request_id']}")

            atomic_write_json(state_path, state)
            os.replace(source_path, os.path.join(REQUESTS_PROCESSED_DIR, entry))
            log(f"Accepted dynamic dispatch request {state['request_id']}")
        except Exception as exc:
            log(f"Failed to accept request {entry}: {exc}")


def write_summary(state: Dict) -> str:
    summary_path = os.path.join(RESULTS_DIR, state["summary_file"])
    lines = [
        f"# Request Summary: {state['request_id']}",
        "",
        f"- Requester: {state['requester']}",
        f"- Parent Task ID: {state.get('parent_task_id') or 'none'}",
        "",
        "## Subtask Results",
    ]
    for task in state["tasks"]:
        lines.extend(
            [
                f"- `{task['task_id']}` ({task['agent']}): `.agent/results/{task['result_file']}`",
            ]
        )

    lines.extend(
        [
            "",
            "Read the listed result files before producing the final integration output.",
        ]
    )
    atomic_write_text(summary_path, "\n".join(lines) + "\n")
    return summary_path


def process_state_file(state_path: str) -> None:
    state = load_json(state_path)
    changed = False

    for task in state["tasks"]:
        report_path = os.path.join(RESULTS_DIR, task["result_file"])
        if os.path.exists(report_path) and task["status"] != STATUS_COMPLETED:
            task["status"] = STATUS_COMPLETED
            changed = True

    completed_task_ids = {task["task_id"] for task in state["tasks"] if task["status"] == STATUS_COMPLETED}

    for task in state["tasks"]:
        if task["status"] != STATUS_PENDING:
            continue

        if not all(dep_task_id in completed_task_ids for dep_task_id in task["dep_task_ids"]):
            continue

        dispatched = dispatch_order(
            agent_name=task["agent"],
            task_id=task["task_id"],
            content=task["content"],
            parent_task_id=state.get("parent_task_id") or state["request_id"],
            request_id=state["request_id"],
            extra_context=[
                f"This subtask was spawned by `{state['requester']}`.",
                "Do not block waiting for siblings. Finish your own subtask and write the result file.",
            ],
        )
        if dispatched:
            task["status"] = STATUS_DISPATCHED
            changed = True

    all_subtasks_completed = all(task["status"] == STATUS_COMPLETED for task in state["tasks"])
    callback = state.get("callback")

    if all_subtasks_completed:
        summary_path = write_summary(state)
        if callback:
            callback_result_path = os.path.join(RESULTS_DIR, callback["result_file"])
            if os.path.exists(callback_result_path):
                if state["status"] != "completed":
                    state["status"] = "completed"
                    changed = True
            elif not callback["dispatched"]:
                dispatched = dispatch_order(
                    agent_name=callback["agent"],
                    task_id=callback["task_id"],
                    content=callback["content"],
                    parent_task_id=state.get("parent_task_id") or state["request_id"],
                    request_id=state["request_id"],
                    extra_context=[
                        f"All subtasks for request `{state['request_id']}` are complete.",
                        f"Read `.agent/results/{os.path.basename(summary_path)}` and the referenced result files.",
                        "Produce the integration result for the parent flow.",
                    ],
                )
                if dispatched:
                    callback["dispatched"] = True
                    changed = True
        elif state["status"] != "completed":
            state["status"] = "completed"
            changed = True

    if changed:
        atomic_write_json(state_path, state)


def process_dynamic_requests() -> None:
    process_request_files()
    for entry in sorted(os.listdir(STATE_DIR)):
        if not entry.endswith(".json"):
            continue
        process_state_file(os.path.join(STATE_DIR, entry))


def monitor_once() -> None:
    ensure_dirs()
    process_static_tasks()
    process_dynamic_requests()


def monitor() -> None:
    ensure_dirs()
    log("Monitoring started")
    while True:
        try:
            monitor_once()
        except Exception as exc:
            log(f"Monitor loop error: {exc}")
        time.sleep(POLL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one orchestration cycle and exit")
    args = parser.parse_args()

    if args.once:
        monitor_once()
    else:
        monitor()


if __name__ == "__main__":
    main()
