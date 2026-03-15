import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

SCRIPT_MAP = {
    "bootstrap": ROOT / ".agent" / "scripts" / "bootstrap_workspace.py",
    "check": ROOT / ".agent" / "scripts" / "check_environment.py",
    "guide": ROOT / ".agent" / "scripts" / "generate_setup_guide.py",
    "sandbox": ROOT / ".agent" / "scripts" / "setup_sandbox.py",
    "orchestrator": ROOT / ".agent" / "orchestrator.py",
}

LOOP_MAP = {
    "claude": ROOT / ".agent" / "claude_agent_loop.ps1",
    "gemini": ROOT / ".agent" / "gemini_agent_loop.ps1",
    "codex": ROOT / ".agent" / "codex_agent_loop.ps1",
}


def run_command(command: list[str]) -> int:
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


def run_python(script_key: str, *extra_args: str) -> int:
    script_path = SCRIPT_MAP[script_key]
    return run_command([sys.executable, str(script_path), *extra_args])


def run_powershell(script_path: Path) -> int:
    return run_command(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ]
    )


def command_setup(include_sandbox: bool) -> int:
    for key in ("bootstrap", "check", "guide"):
        exit_code = run_python(key)
        if exit_code != 0:
            return exit_code
    if include_sandbox:
        return run_python("sandbox")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Bootstrap and operate the Universal Agent Hub template.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Bootstrap the template and run environment checks")
    setup_parser.add_argument("--with-sandbox", action="store_true", help="Also run the OpenSandbox helper")

    subparsers.add_parser("bootstrap", help="Create required directories and placeholder files")
    subparsers.add_parser("check", help="Check tools and colocated repositories")
    subparsers.add_parser("guide", help="Generate the machine-specific setup guide")
    subparsers.add_parser("sandbox", help="Run the OpenSandbox helper")

    orchestrator_parser = subparsers.add_parser("orchestrator", help="Run the orchestrator")
    orchestrator_parser.add_argument("--once", action="store_true", help="Run one cycle and exit")

    loop_parser = subparsers.add_parser("loop", help="Run an agent worker loop")
    loop_parser.add_argument("agent_name", choices=sorted(LOOP_MAP.keys()))

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "setup":
        return command_setup(include_sandbox=args.with_sandbox)
    if args.command == "bootstrap":
        return run_python("bootstrap")
    if args.command == "check":
        return run_python("check")
    if args.command == "guide":
        return run_python("guide")
    if args.command == "sandbox":
        return run_python("sandbox")
    if args.command == "orchestrator":
        extra_args = ["--once"] if args.once else []
        return run_python("orchestrator", *extra_args)
    if args.command == "loop":
        return run_powershell(LOOP_MAP[args.agent_name])

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
