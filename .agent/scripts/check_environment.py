import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / ".agent"
WORKSPACE_CONFIG = AGENT_DIR / "workspace.json"
WORKSPACE_TEMPLATE = AGENT_DIR / "workspace.template.json"

DEFAULT_TOOL_PROBES = {
    "python": ["python", "--version"],
    "uv": ["uv", "--version"],
    "docker": ["docker", "--version"],
    "claude": ["claude", "--version"],
    "gemini": ["gemini"],
    "codex": ["codex"],
}


def resolve_command(name: str) -> str | None:
    direct = shutil.which(name)
    if direct:
        return direct

    npm_roaming = Path(os.environ.get("APPDATA", "")) / "npm"
    candidates = [
        npm_roaming / f"{name}.cmd",
        npm_roaming / f"{name}.ps1",
        npm_roaming / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def run_version(command: list[str]) -> tuple[bool, str, str | None]:
    resolved = resolve_command(command[0])
    if not resolved:
        return False, "missing", None

    if len(command) == 1:
        return True, "installed", resolved

    probe = [resolved, *command[1:]]
    try:
        completed = subprocess.run(
            probe,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return True, "installed (version probe timed out)", resolved
    except Exception as exc:
        return True, f"installed (version probe failed: {exc})", resolved

    lines = (completed.stdout or completed.stderr).strip().splitlines()
    return True, lines[0] if lines else "ok", resolved


def load_workspace_config() -> dict:
    source = WORKSPACE_CONFIG if WORKSPACE_CONFIG.exists() else WORKSPACE_TEMPLATE
    if not source.exists():
        return {"workspace_name": ROOT.name, "tools": {}, "repositories": []}
    return json.loads(source.read_text(encoding="utf-8"))


def main() -> int:
    config = load_workspace_config()
    configured_tools = config.get("tools", {})
    repositories = config.get("repositories", [])
    report = {
        "workspace_name": config.get("workspace_name", ROOT.name),
        "platform": platform.platform(),
        "python_runtime": sys.version.split()[0],
        "config_source": str(WORKSPACE_CONFIG if WORKSPACE_CONFIG.exists() else WORKSPACE_TEMPLATE),
        "tools": {},
        "repositories": {},
    }

    print("Environment check")
    print(f"Workspace: {ROOT}")
    print(f"Workspace name: {report['workspace_name']}")
    print(f"Platform: {report['platform']}")

    tool_names = list(dict.fromkeys([*DEFAULT_TOOL_PROBES.keys(), *configured_tools.keys()]))
    for tool in tool_names:
        command_name = configured_tools.get(tool, tool)
        probe = DEFAULT_TOOL_PROBES.get(tool, [command_name])
        command = [command_name, *probe[1:]] if len(probe) > 1 else [command_name]
        ok, detail, resolved = run_version(command)
        report["tools"][tool] = {"available": ok, "detail": detail, "resolved_path": resolved}
        status = "OK" if ok else "MISSING"
        print(f"- {tool}: {status} ({detail})")

    for repository in repositories:
        name = repository["name"]
        path = ROOT / repository["path"]
        exists = path.exists()
        report["repositories"][name] = {
            "exists": exists,
            "path": str(path),
            "required": bool(repository.get("required", False)),
            "purpose": repository.get("purpose", ""),
        }
        status = "present" if exists else "absent"
        print(f"- repo {name}: {status} ({path})")

    report_path = AGENT_DIR / "artifacts" / "logs" / "environment_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Report written to: {report_path}")

    required_tools = ["python", "codex"]
    missing_tools = [tool for tool in required_tools if tool in report["tools"] and not report["tools"][tool]["available"]]
    missing_repos = [
        name for name, info in report["repositories"].items()
        if info.get("required") and not info["exists"]
    ]
    return 1 if missing_tools or missing_repos else 0


if __name__ == "__main__":
    raise SystemExit(main())
