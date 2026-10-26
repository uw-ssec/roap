"""Migration gate: GUI launcher is present and importable.

The launcher lives in ``tools/`` per the plan. ``roap_app.py`` imports
``roap_app_core`` as a sibling module with no sys.path manipulation, so
both files must stay in the same directory.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
APP = TOOLS / "roap_app.py"
APP_CORE = TOOLS / "roap_app_core.py"


def test_gui_app_exists() -> None:
    assert APP.exists(), f"Missing {APP}"
    assert APP_CORE.exists(), f"Missing {APP_CORE}"


def test_app_core_is_importable_without_display() -> None:
    """The core is GUI-independent, so it must import with no Tkinter/display."""
    result = subprocess.run(
        [sys.executable, "-c", "import roap_app_core as c; print(c.find_project_root)"],
        capture_output=True,
        text=True,
        cwd=TOOLS,
        timeout=60,
    )
    assert result.returncode == 0, f"app core import failed:\n{result.stderr}"


def test_app_core_finds_repo_root_from_tools() -> None:
    """find_project_root walks up from tools/ to the repo root.

    Guards the tools/ placement: the launcher shells out to ./run_pipeline.sh
    relative to whatever this returns.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import roap_app_core as c, pathlib;"
            "print(c.find_project_root(pathlib.Path('.').resolve()))",
        ],
        capture_output=True,
        text=True,
        cwd=TOOLS,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(REPO_ROOT), (
        f"find_project_root returned {result.stdout.strip()!r}, expected {REPO_ROOT}"
    )


def test_gui_app_compiles() -> None:
    """The Tkinter app parses and byte-compiles.

    Launching is covered separately by test_gui_app_launches_and_closes.
    """
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(APP)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"GUI app failed to compile:\n{result.stderr}"


def test_gui_app_imports_core_as_sibling() -> None:
    """Both files must live together; a split would break the bare import."""
    source = APP.read_text(encoding="utf-8")
    assert "from roap_app_core import" in source
    assert APP.parent == APP_CORE.parent, "app and app_core must share a directory"


@pytest.mark.parametrize("marker", ["run_pipeline.sh", "notebooks"])
def test_repo_root_has_launcher_markers(marker: str) -> None:
    """find_project_root keys off these two; both must exist at the root."""
    assert (REPO_ROOT / marker).exists(), f"Missing root marker: {marker}"


# Builds the real window, runs the Tk mainloop briefly, then closes it. Runs in
# a subprocess so a hang hits the timeout instead of stalling the test session.
LAUNCH_SCRIPT = """
import tkinter as tk
import roap_app

root = tk.Tk()
app = roap_app.PipelineApp(root)
root.update()
assert root.title() == roap_app.APP_TITLE, root.title()
root.after(1500, root.destroy)
root.mainloop()
print("GUI_SMOKE_OK")
"""


def run_gui_script(script: str, *args: str) -> subprocess.CompletedProcess:
    """Run a Tk script from tools/ and fail on any callback exception.

    Needs a display. Without one the test skips, unless ROAP_REQUIRE_GUI=1
    (set by CI), where a missing display is a failure rather than a skip.
    """
    result = subprocess.run(
        [sys.executable, "-c", script, *args],
        capture_output=True,
        text=True,
        cwd=TOOLS,
        timeout=120,
    )
    no_display = "TclError" in result.stderr and "display" in result.stderr.lower()
    if no_display and os.environ.get("ROAP_REQUIRE_GUI") != "1":
        pytest.skip("no display available for Tk")
    assert result.returncode == 0, f"GUI script failed:\n{result.stderr}"
    # Tk reports exceptions raised in callbacks (e.g. _drain_log) on stderr
    # without changing the exit code.
    assert "Exception in Tkinter callback" not in result.stderr, result.stderr
    return result


def test_gui_app_launches_and_closes() -> None:
    """The launcher opens its window, runs the event loop, and closes cleanly."""
    result = run_gui_script(LAUNCH_SCRIPT)
    assert "GUI_SMOKE_OK" in result.stdout


# Clicks Run with Dry run ticked and waits, inside the real mainloop, for the
# worker thread to finish. Covers the subprocess, log queue and finish path.
DRY_RUN_SCRIPT = """
import sys
import tkinter as tk
import roap_app

roap_app.messagebox.showerror = lambda *a, **k: print("ERROR_DIALOG", a)
root = tk.Tk()
app = roap_app.PipelineApp(root)
app.out_var.set(sys.argv[1])
app.dry_run_var.set(True)
app._run()

def poll(left=600):
    if app.run_btn.instate(["!disabled"]) or left == 0:
        root.destroy()
    else:
        root.after(100, poll, left - 1)

root.after(100, poll)
root.mainloop()
print("STATUS", app.status_var.get())
"""


def test_gui_dry_run_click_finishes(tmp_path: Path) -> None:
    result = run_gui_script(DRY_RUN_SCRIPT, str(tmp_path / "out"))
    assert "ERROR_DIALOG" not in result.stdout, result.stdout
    assert "STATUS Done." in result.stdout, result.stdout + result.stderr


# Replaces the pipeline with a stand-in tree: a child in the run's process
# group (papermill) and a grandchild in its own session (a Jupyter kernel).
FAKE_PIPELINE = """
import subprocess, sys, time
sleep = [sys.executable, "-c", "import time; time.sleep(120)"]
child = subprocess.Popen(sleep)
kernel = subprocess.Popen(sleep, start_new_session=True)
with open(sys.argv[1], "w") as f:
    f.write(f"{child.pid} {kernel.pid}")
print("stage running", flush=True)
time.sleep(120)
"""

# argv: pid file, output dir, action ("cancel" or "quit").
STOP_SCRIPT = """
import os, sys
import tkinter as tk
import roap_app

pid_file, out_dir, action = sys.argv[1:4]
fake = sys.argv[4]
roap_app.build_command = lambda *a, **k: [sys.executable, "-c", fake, pid_file]
asked = []
def askyesno(*a, **k):
    asked.append(a)
    return len(asked) > 1  # decline the first quit, accept the second
roap_app.messagebox.askyesno = askyesno

root = tk.Tk()
app = roap_app.PipelineApp(root)
app.out_var.set(out_dir)
app._run()

def stop():
    if not (os.path.exists(pid_file) and open(pid_file).read().strip()):
        root.after(100, stop)
        return
    if action == "cancel":
        app._cancel()
        root.after(100, wait_cancelled)
    else:
        app._quit()
        print("RUNNING_AFTER_DECLINE", app._running())
        app._quit()

def wait_cancelled(left=300):
    if app.run_btn.instate(["!disabled"]) or left == 0:
        root.destroy()
    else:
        root.after(100, wait_cancelled, left - 1)

root.after(100, stop)
root.mainloop()
print("PIDS", app.proc.pid, open(pid_file).read())
print("STATUS", app.status_var.get() if action == "cancel" else "")
"""


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    state = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


def _assert_no_survivors(stdout: str) -> None:
    line = next(x for x in stdout.splitlines() if x.startswith("PIDS "))
    pids = [int(p) for p in line.split()[1:]]
    deadline = time.monotonic() + 10
    while any(_alive(p) for p in pids) and time.monotonic() < deadline:
        time.sleep(0.1)
    survivors = [p for p in pids if _alive(p)]
    for p in survivors:
        os.kill(p, signal.SIGKILL)
    assert not survivors, f"pipeline processes survived: {survivors}"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX process groups")
def test_stop_process_tree_leaves_no_survivors(tmp_path: Path) -> None:
    """The core helper alone, no display needed: the tree, kernel included, dies."""
    sys.path.insert(0, str(TOOLS))
    import roap_app_core as core

    pid_file = tmp_path / "pids"
    proc = subprocess.Popen(
        [sys.executable, "-c", FAKE_PIPELINE, str(pid_file)],
        stdout=subprocess.DEVNULL,
        **core.process_group_kwargs(),
    )
    try:
        deadline = time.monotonic() + 30
        while not (pid_file.exists() and pid_file.read_text().strip()):
            assert time.monotonic() < deadline, "tree never started"
            time.sleep(0.05)
        core.stop_process_tree(proc)
        proc.wait(timeout=10)
        _assert_no_survivors(f"PIDS {proc.pid} {pid_file.read_text()}")
    finally:
        if proc.poll() is None:
            proc.kill()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX process check")
def test_gui_cancel_stops_whole_tree_and_flags_outputs(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = run_gui_script(
        STOP_SCRIPT, str(tmp_path / "pids"), str(out), "cancel", FAKE_PIPELINE
    )
    _assert_no_survivors(result.stdout)
    status = next(x for x in result.stdout.splitlines() if x.startswith("STATUS"))
    assert "Cancelled" in status and "incomplete" in status, status
    assert str(out) in status, status


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX process check")
def test_gui_quit_mid_run_confirms_then_stops_whole_tree(tmp_path: Path) -> None:
    result = run_gui_script(
        STOP_SCRIPT, str(tmp_path / "pids"), str(tmp_path / "out"), "quit",
        FAKE_PIPELINE,
    )
    assert "RUNNING_AFTER_DECLINE True" in result.stdout, result.stdout
    _assert_no_survivors(result.stdout)
