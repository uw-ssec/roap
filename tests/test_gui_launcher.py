"""Migration gate: GUI launcher is present and importable.

The launcher lives in ``tools/`` per the plan. ``oa_pipeline_app.py`` imports
``oa_pipeline_app_core`` as a sibling module with no sys.path manipulation, so
both files must stay in the same directory.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
APP = TOOLS / "oa_pipeline_app.py"
APP_CORE = TOOLS / "oa_pipeline_app_core.py"


def test_gui_app_exists() -> None:
    assert APP.exists(), f"Missing {APP}"
    assert APP_CORE.exists(), f"Missing {APP_CORE}"


def test_app_core_is_importable_without_display() -> None:
    """The core is GUI-independent, so it must import with no Tkinter/display."""
    result = subprocess.run(
        [sys.executable, "-c", "import oa_pipeline_app_core as c; print(c.find_project_root)"],
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
            "import oa_pipeline_app_core as c, pathlib;"
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

    It is not launched: a Tk mainloop needs a display and would hang CI.
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
    source = APP.read_text()
    assert "from oa_pipeline_app_core import" in source
    assert APP.parent == APP_CORE.parent, "app and app_core must share a directory"


@pytest.mark.parametrize("marker", ["run_pipeline.sh", "notebooks"])
def test_repo_root_has_launcher_markers(marker: str) -> None:
    """find_project_root keys off these two; both must exist at the root."""
    assert (REPO_ROOT / marker).exists(), f"Missing root marker: {marker}"
