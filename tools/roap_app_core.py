"""
roap_app_core.py — GUI-independent logic for the desktop launcher
========================================================================

These functions contain all the real behaviour of the desktop app (project
discovery, command building, environment checks, verdict summarising) with no
dependency on Tkinter, so they can be unit-tested in a headless environment and
reused by any front end. `roap_app.py` imports from here.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


STAGE_FILES = [
    "02_ta_ph_qc.ipynb",
    "04_stage1a.ipynb",
    "05_stage1b.ipynb",
    "06_stage2.ipynb",
    "07_stage3.ipynb",
    "08_stage4.ipynb",
]


def find_project_root(start: Path) -> Path | None:
    """Walk up from `start` looking for run_pipeline.sh + notebooks/."""
    for candidate in [start, *start.parents]:
        if (candidate / "run_pipeline.sh").exists() and (
            candidate / "notebooks"
        ).is_dir():
            return candidate
    return None


def find_bash() -> str | None:
    """Locate bash, preferring Git Bash over the WSL stub on Windows.

    On Windows, `shutil.which("bash")` usually resolves to
    C:\\WINDOWS\\system32\\bash.exe — the WSL launcher. That bash mangles
    Windows backslash paths during command-line tokenization, mounts C: at
    /mnt/c (not /c), and runs a Linux Python that cannot see a Windows
    .venv. Git Bash avoids all three problems, so we look for it first and
    only fall back to PATH bash if Git Bash is absent.
    """
    if os.name == "nt":
        for p in [
            Path("C:/Program Files/Git/bin/bash.exe"),
            Path("C:/Program Files/Git/usr/bin/bash.exe"),
            Path("C:/Program Files (x86)/Git/bin/bash.exe"),
        ]:
            if p.exists():
                return str(p)
    found = shutil.which("bash")
    if found and "System32" not in found and "system32" not in found:
        return found
    # Last resort: even the WSL stub is better than nothing; the path
    # conversion below still lets relative paths work.
    return found


def find_python() -> str:
    """Python interpreter the pipeline should use for Papermill."""
    return os.environ.get("PYTHON_BIN") or sys.executable or "python"


def package_importable(python_exe: str) -> bool:
    """Check roap is importable by the chosen interpreter."""
    try:
        r = subprocess.run(
            [python_exe, "-c", "import roap"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return r.returncode == 0
    except Exception:
        return False


def kernel_available(python_exe: str) -> bool:
    """Best-effort check that a Jupyter python3 kernel exists for Papermill."""
    try:
        r = subprocess.run(
            [python_exe, "-m", "jupyter", "kernelspec", "list"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return r.returncode == 0 and "python3" in r.stdout
    except Exception:
        return False


def process_group_kwargs() -> dict:
    """Popen kwargs that start the pipeline as the leader of its own group.

    Cancel and Quit then stop bash *and* everything it launched, instead of
    only bash (which used to leave papermill running, reparented to init).
    """
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _posix_descendants(pid: int) -> list[int]:
    """PIDs of every live descendant of `pid`, from one `ps` snapshot."""
    try:
        out = subprocess.run(
            ["ps", "-A", "-o", "pid=", "-o", "ppid="],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
    except Exception:
        return []
    children: dict[int, list[int]] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            children.setdefault(int(parts[1]), []).append(int(parts[0]))
    found: list[int] = []
    stack = [pid]
    while stack:
        for child in children.get(stack.pop(), []):
            found.append(child)
            stack.append(child)
    return found


# How long a stopped run gets to exit on SIGTERM before it is SIGKILLed.
STOP_GRACE_SECONDS = 5.0


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_tree(pgid: int, pids: list[int], sig: int) -> None:
    try:
        os.killpg(pgid, sig)
    except (ProcessLookupError, PermissionError):
        pass
    for pid in pids:
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass


def _escalate(proc: subprocess.Popen, pids: list[int], grace: float) -> None:
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        # The group check catches members born after the descendant snapshot,
        # e.g. started by a SIGTERM handler; the PID list catches the ones that
        # left the group (Jupyter kernels).
        if (
            proc.poll() is not None
            and not _group_alive(proc.pid)
            and not any(_pid_alive(p) for p in pids)
        ):
            return
        time.sleep(0.1)
    _signal_tree(proc.pid, [p for p in pids if _pid_alive(p)], signal.SIGKILL)


def stop_process_tree(proc: subprocess.Popen) -> threading.Thread | None:
    """Terminate a process started with `process_group_kwargs` and its tree.

    POSIX: SIGTERM the whole process group, plus any descendant that left it.
    Jupyter starts each kernel in its own session, so killing the group alone
    would leave the kernel executing a notebook cell until it noticed its
    parent was gone. Anything still alive after `STOP_GRACE_SECONDS` gets
    SIGKILL. That wait runs on a returned non-daemon thread, so it never blocks
    Tk and still finishes if the app quits meanwhile. The PIDs are captured
    up front because detached descendants are untraceable once bash exits.
    Windows: `taskkill /T /F` walks the tree by parent PID and kills outright.
    """
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
        )
        return None
    descendants = _posix_descendants(proc.pid)
    _signal_tree(proc.pid, descendants, signal.SIGTERM)
    escalation = threading.Thread(
        target=_escalate,
        args=(proc, descendants, STOP_GRACE_SECONDS),
        daemon=False,
    )
    escalation.start()
    return escalation


def to_bash_path(p: Path, bash_exe: str | None = None) -> str:
    """Normalize a path so BOTH bash and Windows Python accept it.

    The launcher hands a path to bash (`bash run_pipeline.sh PATH ...`),
    and run_pipeline.sh in turn hands that same string to a *Windows*
    Python interpreter via papermill (XLSX_PATH, OUT_DIR, ...). Those two
    consumers have conflicting needs:

      * bash strips backslashes during tokenization, so C:\\Users\\x became
        C:Usersx — the original launcher error.
      * Windows Python (the project's .venv) does NOT understand Git Bash
        mount paths: Path("/c/Users/x") parses as \\c\\Users\\x on the
        current drive, so a /c/... or /mnt/c/... path makes the notebook
        die with "File not found".

    A drive-letter path with FORWARD slashes satisfies both:
        C:\\Users\\x  ->  C:/Users/x
    bash sees no backslashes (drive letter passes through as a plain
    argument), and Windows Python resolves "C:/Users/x" correctly. POSIX
    paths are already forward-slash and pass through unchanged.

    `bash_exe` is accepted for signature stability but no longer affects
    the result: the forward-slash drive form works for Git Bash and the
    WSL stub alike, and avoids the mount-prefix mismatch entirely.
    """
    return str(p).replace("\\", "/")


def build_command(
    bash_exe: str,
    project_root: Path,
    xlsx: Path,
    out_dir: Path,
    sheet: str,
    no_parquet: bool,
    include_viewer: bool,
    include_review: bool,
    dry_run: bool,
    config_dir: Path | None = None,
) -> list[str]:
    """Assemble the run_pipeline.sh command."""
    cmd = [
        bash_exe,
        "./run_pipeline.sh",
        to_bash_path(xlsx, bash_exe),
        to_bash_path(out_dir, bash_exe),
        "--sheet",
        str(sheet),
    ]
    if config_dir is not None:
        cmd.extend(["--config-dir", to_bash_path(config_dir, bash_exe)])
    if no_parquet:
        cmd.append("--no-parquet")
    if include_viewer:
        cmd.append("--include-viewer")
    if include_review:
        cmd.append("--include-review")
    if dry_run:
        cmd.append("--dry-run")
    return cmd


def environment_problems(project_root: Path | None, bash_exe: str | None,
                         python_exe: str) -> list[str]:
    """Return a list of human-readable setup problems (empty if all good)."""
    problems: list[str] = []
    if not project_root:
        problems.append(
            "Could not find the project root (run_pipeline.sh + notebooks/). "
            "Keep tools/roap_app.py in the repository and launch it from "
            "the repository root with pixi run python tools/roap_app.py."
        )
        return problems
    if not bash_exe:
        problems.append(
            "bash was not found. On Windows install Git Bash; "
            "on macOS/Linux it is built in."
        )
    if not package_importable(python_exe):
        problems.append(
            f"roap is not importable by {python_exe}. "
            "From the repository root, run pixi install, then "
            "pixi run python tools/roap_app.py."
        )
    if not kernel_available(python_exe):
        problems.append(
            "No Jupyter 'python3' kernel detected. From the repository root, "
            "run pixi install, then pixi run python tools/roap_app.py."
        )
    return problems


def summarize_verdicts(out_dir: Path) -> str:
    """Read the final analysis_ready.csv and summarise verdict counts."""
    final = out_dir / "oa_stage4_outputs" / "data" / "analysis_ready.csv"
    if not final.exists():
        return "No final analysis_ready.csv was produced."
    try:
        import csv

        counts: dict[str, int] = {}
        with final.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            field = reader.fieldnames or []
            col = "analysis_audit_status" if "analysis_audit_status" in field else None
            if col is None:
                return f"Final file written: {final}"
            for row in reader:
                v = (row.get(col) or "").strip() or "(blank)"
                counts[v] = counts.get(v, 0) + 1
        total = sum(counts.values())
        parts = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        return f"Final verdicts ({total} sample rows) -> {parts}\nFile: {final}"
    except Exception as exc:
        return f"Final file written: {final} (could not summarise: {exc})"
