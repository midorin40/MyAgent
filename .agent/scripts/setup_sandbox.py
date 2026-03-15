import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OPEN_SANDBOX_DIR = ROOT / "OpenSandbox"


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run(command: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        output = (completed.stdout or completed.stderr).strip()
        return True, output
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    print("OpenSandbox setup helper")
    print(f"Workspace: {ROOT}")
    print(f"OpenSandbox repo: {OPEN_SANDBOX_DIR}")

    if OPEN_SANDBOX_DIR.exists():
        print("- OpenSandbox repository: present")
    else:
        print("- OpenSandbox repository: absent")

    for tool in ("docker", "uv", "python"):
        print(f"- {tool}: {'found' if command_exists(tool) else 'missing'}")

    if command_exists("docker"):
        ok, detail = run(["docker", "--version"])
        print(f"- docker version: {detail if ok else 'unavailable'}")

    print("")
    print("Recommended next steps:")
    print("  1. uv pip install opensandbox-server")
    print("  2. opensandbox-server init-config ~/.sandbox.toml --example docker")
    print("  3. opensandbox-server")
    print("  4. Read OpenSandbox/README.md for SDK and runtime examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
