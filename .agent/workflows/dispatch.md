---
description: Dispatch static and dynamic tasks to worker agents.
---

# Dispatch Workflow

## Static dispatch
1. Read `.agent/task.md`.
2. For each task whose dependencies are complete, create an order file in `.agent/orders`.
3. Mark the task as in progress in `.agent/task.md`.
4. When the matching result file appears in `.agent/results`, mark the task complete.

## Dynamic dispatch
1. A running agent submits a request file to `.agent/requests` with `python .agent/scripts/submit_dispatch.py`.
2. The orchestrator converts the request into request state under `.agent/state`.
3. Each child subtask is dispatched to the requested agent when its dependencies are satisfied.
4. After all child tasks finish, the orchestrator writes a summary file to `.agent/results`.
5. If a callback was requested, the orchestrator dispatches a callback task to the callback agent so the parent flow can resume.
