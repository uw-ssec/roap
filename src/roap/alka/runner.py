"""
alka.runner — build and run the pipeline, reusing the existing core module.

This is a thin adapter. It does NOT reimplement command-building, bash
discovery, or verdict summarising — those already live in
`tools/roap_app_core.py` and are tested and working. Alka imports them and
adds exactly one new step: writing the config files implied by the GUI options
(via config_writer) before assembling the command.

Keeping this as an adapter means:
  * the existing launcher (tools/roap_app.py) keeps working unchanged;
  * there is one source of truth for how the pipeline is invoked;
  * when a run misbehaves, you look here for the Alka-specific wiring and in
    the core module for the invocation itself — not one tangled file.
"""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

from .state import AppState
from . import config_writer

# Import the existing, tested core. It lives in `tools/roap_app_core.py`, which
# is deliberately OUTSIDE the installed package: `tools/roap_app.py` imports it
# as a bare sibling (see tests/test_gui_launcher.py), so it must stay there.
#
# Alka therefore locates it by path rather than by package import. The GUI is
# inherently repo-bound anyway — it shells out to ./run_pipeline.sh — so
# resolving relative to the source tree is correct, not a workaround.
#
# Import errors are deliberately NOT swallowed: a missing core means the GUI
# cannot run at all, and a silent failure here previously hid a dead launcher.
def _load_app_core():  # pragma: no cover - import resolution differs by context
    import importlib
    import importlib.util
    import sys

    # src/roap/alka/runner.py -> parents[3] == repo root
    tools_dir = Path(__file__).resolve().parents[3] / "tools"
    core_path = tools_dir / "roap_app_core.py"

    if core_path.is_file():
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        spec = importlib.util.spec_from_file_location("roap_app_core", core_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {core_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("roap_app_core", module)
        spec.loader.exec_module(module)
        return module

    # Already importable (e.g. launched from tools/, or installed on sys.path).
    return importlib.import_module("roap_app_core")


core = _load_app_core()


def resolve_environment(state: AppState) -> list[str]:
    """Fill in bash/python/project_root on the state; return any problems."""
    start = Path(__file__).resolve()
    state.project_root = core.find_project_root(start) or core.find_project_root(Path.cwd())
    state.bash_exe = core.find_bash()
    state.python_exe = core.find_python()
    return core.environment_problems(state.project_root, state.bash_exe, state.python_exe)


def build_run_command(state: AppState) -> tuple[list[str], list[str]]:
    """Write configs from the GUI options, then assemble the pipeline command.

    Returns (command, notes). `notes` are human-readable lines about what the
    config step did, for the log.
    """
    # 1) translate GUI options into config files (the new Alka step)
    cfg_res = config_writer.write_stage_configs(
        project_root=state.project_root,
        compute_carbonate_internally=state.compute_carbonate_internally,
    )
    state.last_config_dir = cfg_res.config_dir

    # 2) hand off to the existing, tested command builder
    cmd = core.build_command(
        bash_exe=state.bash_exe,
        project_root=state.project_root,
        xlsx=Path(state.input_xlsx),
        out_dir=Path(state.output_dir),
        sheet=state.sheet,
        no_parquet=state.no_parquet,
        include_viewer=state.include_viewer,
        include_review=state.include_review,
        dry_run=state.dry_run,
        config_dir=cfg_res.config_dir,
    )
    return cmd, cfg_res.notes


def run_pipeline(
    state: AppState,
    on_output: Callable[[str], None],
    on_finish: Callable[[int, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> threading.Thread:
    """Run the pipeline in a background thread, streaming output.

    on_output(line)   — called for each line of stdout/stderr.
    on_finish(rc, summary) — called once when done, with return code and a
                             verdict summary string.
    Returns the started Thread so the caller can join/track it.
    """
    def _work():
        try:
            cmd, notes = build_run_command(state)
        except Exception as exc:  # noqa: BLE001
            on_finish(-1, f"Could not build command: {exc}")
            return

        for n in notes:
            on_output(f"[config] {n}")
        on_output("[run] " + " ".join(cmd))

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(state.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:  # noqa: BLE001
            on_finish(-1, f"Failed to start pipeline: {exc}")
            return

        assert proc.stdout is not None
        for line in proc.stdout:
            if cancel_event is not None and cancel_event.is_set():
                proc.terminate()
                on_output("[run] cancelled by user")
                break
            on_output(line.rstrip("\n"))
        rc = proc.wait()

        summary = ""
        if rc == 0 and not state.dry_run:
            try:
                summary = core.summarize_verdicts(Path(state.output_dir))
            except Exception as exc:  # noqa: BLE001
                summary = f"(could not summarise verdicts: {exc})"
        on_finish(rc, summary)

    state.is_running = True
    t = threading.Thread(target=_work, daemon=True)
    t.start()
    return t