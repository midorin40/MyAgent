import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / ".agent"
WORKSPACE_CONFIG = AGENT_DIR / "workspace.json"
WORKSPACE_TEMPLATE = AGENT_DIR / "workspace.template.json"
ENV_REPORT = AGENT_DIR / "artifacts" / "logs" / "environment_report.json"
OUTPUT = AGENT_DIR / "artifacts" / "logs" / "setup_guide.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = WORKSPACE_CONFIG if WORKSPACE_CONFIG.exists() else WORKSPACE_TEMPLATE
    config = load_json(config_path)
    report = load_json(ENV_REPORT) if ENV_REPORT.exists() else {"tools": {}, "repositories": {}}

    lines = [
        f"# Setup Guide: {config.get('workspace_name', ROOT.name)}",
        "",
        f"- Workspace root: `{ROOT}`",
        f"- Config source: `{config_path}`",
        "",
        "## Bootstrap",
        "```bash",
        "python .agent/scripts/bootstrap_workspace.py",
        "python .agent/scripts/check_environment.py",
        "```",
        "",
        "## Tool Status",
    ]

    for tool, detail in report.get("tools", {}).items():
        status = "OK" if detail.get("available") else "MISSING"
        resolved = detail.get("resolved_path") or "n/a"
        lines.append(f"- `{tool}`: {status} ({detail.get('detail', 'unknown')}) [{resolved}]")

    lines.extend(["", "## Repositories"])
    for repo in config.get("repositories", []):
        name = repo["name"]
        path = repo["path"]
        required = "required" if repo.get("required") else "optional"
        exists = report.get("repositories", {}).get(name, {}).get("exists", False)
        status = "present" if exists else "absent"
        lines.append(f"- `{name}`: {status}, {required}, path `{path}`")
        purpose = repo.get("purpose", "")
        if purpose:
            lines.append(f"  Purpose: {purpose}")
        source_url = repo.get("source_url", "")
        if source_url:
            lines.append(f"  Source: `{source_url}`")

    lines.extend(
        [
            "",
            "## New Machine Checklist",
            "- Install Python 3.10+.",
            "- Install the agent CLIs you intend to use: `claude`, `gemini`, `codex`.",
            "- Install Docker if you plan to run OpenSandbox locally.",
            "- Place optional repos next to this template, for example `OpenSandbox/` and `deer-flow/`.",
            "- Re-run `python .agent/scripts/check_environment.py` after installing tools.",
            "",
            "## Clone Commands",
            "```bash",
            "git clone https://github.com/alibaba/OpenSandbox.git",
            "git clone https://github.com/bytedance/deer-flow.git",
            "```",
            "",
            "## OpenSandbox",
            "```bash",
            "uv pip install opensandbox-server",
            "opensandbox-server init-config ~/.sandbox.toml --example docker",
            "opensandbox-server",
            "```",
            "",
            "## Run",
            "```bash",
            "python .agent/orchestrator.py",
            "```",
            "```powershell",
            "powershell -ExecutionPolicy Bypass -File .agent/codex_agent_loop.ps1",
            "powershell -ExecutionPolicy Bypass -File .agent/claude_agent_loop.ps1",
            "powershell -ExecutionPolicy Bypass -File .agent/gemini_agent_loop.ps1",
            "```",
            "",
            "## Notes",
            "- If `codex exec` fails with an access error on Windows, run the worker in a context that has permission to launch Codex outside the sandbox.",
            "- This guide is generated from `.agent/workspace.json` or `.agent/workspace.template.json` plus the latest environment report.",
            "",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
