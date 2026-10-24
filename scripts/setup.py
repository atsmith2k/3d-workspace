"""One-step setup: find a supported Python, create .venv, install, self-test.

    python scripts/setup.py          (any Python 3 works to launch it)

Safe to re-run. Prints "READY" on the last line when the workspace works.
Standard library only, so it runs before anything is installed.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
SUPPORTED = [(3, 12), (3, 13), (3, 14)]  # numpy 2.5 needs >=3.12, build123d needs <3.15
WINDOWS = os.name == "nt"
VENV_PY = VENV / ("Scripts/python.exe" if WINDOWS else "bin/python")


def step(msg):
    print(f"\n==> {msg}", flush=True)


def fail(msg):
    print(f"\nSETUP FAILED: {msg}", flush=True)
    sys.exit(1)


def version_of(cmd):
    try:
        out = subprocess.run(cmd + ["-c", "import sys; print(*sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=30)
        major, minor = map(int, out.stdout.split())
        return major, minor
    except Exception:
        return None


def find_python():
    """A command (list) that runs a supported Python, newest preferred."""
    if sys.version_info[:2] in SUPPORTED:
        return [sys.executable]
    candidates = []
    for major, minor in reversed(SUPPORTED):
        if WINDOWS and shutil.which("py"):
            candidates.append(["py", f"-{major}.{minor}"])
        exe = shutil.which(f"python{major}.{minor}")
        if exe:
            candidates.append([exe])
    for name in ("python3", "python"):
        exe = shutil.which(name)
        if exe:
            candidates.append([exe])
    for cmd in candidates:
        if version_of(cmd) in SUPPORTED:
            return cmd
    versions = ", ".join(f"{a}.{b}" for a, b in SUPPORTED)
    fail(f"no supported Python found (need {versions}; this is "
         f"{sys.version_info.major}.{sys.version_info.minor}). Install Python 3.12 from "
         "python.org (Windows: also `winget install Python.Python.3.12`; "
         "macOS: `brew install python@3.12`), then re-run this script.")


def run(cmd, **kw):
    print("   $ " + " ".join(str(c) for c in cmd), flush=True)
    result = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if result.returncode:
        fail(f"command exited with {result.returncode}: {' '.join(str(c) for c in cmd)}")


def main():
    step("Checking Python")
    if VENV_PY.exists() and version_of([str(VENV_PY)]) in SUPPORTED:
        print(f"   existing .venv uses Python {'.'.join(map(str, version_of([str(VENV_PY)])))}")
    else:
        if VENV.exists():
            print("   existing .venv is broken or uses an unsupported Python; recreating it")
            shutil.rmtree(VENV)
        py = find_python()
        print(f"   using {' '.join(py)} (Python {'.'.join(map(str, version_of(py)))})")
        step("Creating virtual environment in .venv")
        run(py + ["-m", "venv", str(VENV)])

    step("Installing packages (first run downloads ~150 MB, mostly the OpenCascade CAD kernel)")
    run([VENV_PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([VENV_PY, "-m", "pip", "install", "--quiet", "-r", ROOT / "requirements.txt"])

    if not WINDOWS:
        launcher = ROOT / "cad"
        launcher.chmod(launcher.stat().st_mode | 0o111)

    step("Self-test: building, checking and rendering a test part")
    run([VENV_PY, "-m", "cadkit", "selftest"])

    launcher = "cad.cmd" if WINDOWS else "./cad"
    print(f"\nSetup complete. Build a model with:  {launcher} build models/<name>.py")
    print("READY")


if __name__ == "__main__":
    main()
