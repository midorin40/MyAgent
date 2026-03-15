# Agent Template

This directory is the reusable control plane for the multi-agent system.

## Goals
- Work from any repository root without hardcoded machine paths
- Support static and dynamic multi-agent task dispatch
- Keep setup reproducible across fresh environments
- Allow optional colocated repos such as `OpenSandbox/` and `deer-flow/`

## Quick Start
```bash
python .agent/scripts/bootstrap_workspace.py
python .agent/scripts/check_environment.py
python .agent/scripts/generate_setup_guide.py
python .agent/orchestrator.py
```

In separate terminals:

```powershell
powershell -ExecutionPolicy Bypass -File .agent/claude_agent_loop.ps1
powershell -ExecutionPolicy Bypass -File .agent/gemini_agent_loop.ps1
powershell -ExecutionPolicy Bypass -File .agent/codex_agent_loop.ps1
```

## Required Tools
- Python 3.10+

## Optional Tools
- Docker
- `uv`
- `claude`
- `gemini`
- `codex`

## Template Files
- `.agent/task_template.md`: starter task board
- `.agent/workspace.template.json`: example manifest for tools and colocated repos
- `.agent/scripts/bootstrap_workspace.py`: creates missing directories and placeholders
- `.agent/scripts/check_environment.py`: validates tool availability and writes a report
- `.agent/scripts/generate_setup_guide.py`: creates a Markdown setup guide for a new machine

## Notes
- Agent loops detect the repo root from their own location.
- Override CLI names with `CLAUDE_CMD`, `GEMINI_CMD`, and `CODEX_CMD` when needed.
- `OpenSandbox/` and `deer-flow/` are optional directories. The environment report records whether they are present.
- Create `.agent/workspace.json` to override the template manifest for a specific machine or project.
