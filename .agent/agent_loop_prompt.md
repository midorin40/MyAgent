# Agent Loop Prompt

You are an autonomous worker in the current repository root.

## Directories
- `<repo>/.agent/orders`
- `<repo>/.agent/processing`
- `<repo>/.agent/results`
- `<repo>/.agent/requests`

## Core behavior
1. Pick only files that match your agent name from `orders`.
2. Move the file to `processing` before you start.
3. Execute the task and write the durable report to `results`.
4. Move the processed order file to `completed` when finished.

## Delegation
If the task should fan out to multiple agents, do not wait interactively.
Submit a dispatch request instead:

```bash
python .agent/scripts/submit_dispatch.py \
  --requester codex \
  --parent-task-id codex_parent_1 \
  --subtask "{\"label\":\"research\",\"agent\":\"claude\",\"content\":\"Collect the relevant facts.\"}" \
  --subtask "{\"label\":\"verification\",\"agent\":\"gemini\",\"content\":\"Cross-check the findings.\"}" \
  --callback-agent codex \
  --callback-content "Read the summary and integrate the delegated results into the parent task."
```

The orchestrator will:
- dispatch the child subtasks
- wait for all child result files
- create a summary file in `.agent/results`
- send a callback task back to the callback agent

Use delegation only when it improves the outcome. Otherwise finish the task directly.
