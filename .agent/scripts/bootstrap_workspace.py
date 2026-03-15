import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / ".agent"

DIRECTORIES = [
    "orders",
    "processing",
    "results",
    "requests",
    "requests/processed",
    "state",
    "completed",
    "logs",
    "artifacts/drafts",
    "artifacts/logs",
    "artifacts/questions",
    "artifacts/screen",
]

GITKEEPS = [
    "orders/.gitkeep",
    "processing/.gitkeep",
    "results/.gitkeep",
    "requests/.gitkeep",
    "requests/processed/.gitkeep",
    "state/.gitkeep",
    "completed/.gitkeep",
    "artifacts/drafts/.gitkeep",
    "artifacts/logs/.gitkeep",
    "artifacts/questions/.gitkeep",
    "artifacts/screen/.gitkeep",
]

WORKSPACE_TEMPLATE = {
    "workspace_name": ROOT.name,
    "tools": {
        "python": "python",
        "uv": "uv",
        "docker": "docker",
        "claude": "claude",
        "gemini": "gemini",
        "codex": "codex",
    },
    "repositories": [
        {
            "name": "OpenSandbox",
            "path": "OpenSandbox",
            "required": False,
            "purpose": "Sandbox runtime and examples",
        },
        {
            "name": "deer-flow",
            "path": "deer-flow",
            "required": False,
            "purpose": "Reference repo for file-based multi-agent workflow patterns",
        },
    ],
}


def ensure_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def main() -> None:
    for directory in DIRECTORIES:
        (AGENT_DIR / directory).mkdir(parents=True, exist_ok=True)

    for relative_file in GITKEEPS:
        ensure_file(AGENT_DIR / relative_file)

    ensure_file(
        AGENT_DIR / "workspace.template.json",
        json.dumps(WORKSPACE_TEMPLATE, ensure_ascii=False, indent=2) + "\n",
    )

    print(f"Workspace bootstrapped at: {ROOT}")
    print("Next steps:")
    print("  1. python .agent/scripts/check_environment.py")
    print("  2. python .agent/orchestrator.py")
    print("  3. powershell -ExecutionPolicy Bypass -File .agent/codex_agent_loop.ps1")
    print("  4. powershell -ExecutionPolicy Bypass -File .agent/claude_agent_loop.ps1")
    print("  5. powershell -ExecutionPolicy Bypass -File .agent/gemini_agent_loop.ps1")


if __name__ == "__main__":
    main()
