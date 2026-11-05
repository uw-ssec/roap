"""
alka.config_writer — translate GUI choices into pipeline config files.

This module is deliberately GUI-free: it takes plain values (booleans, strings)
and writes/updates the per-stage YAML files the pipeline reads. Keeping it
separate means it can be unit-tested without launching any window — call the
function, inspect the file it produced.

The main job today: when the user ticks "compute carbonate chemistry
internally", write `configs/08_stage4.yaml` with `carbonate_calc.enabled: true`
so the pipeline's Stage 4 runs the internal PyCO2SYS calculation from
RM-corrected TA (instead of requiring the user to hand-edit YAML).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from roap.stage_config import load_stage_config

# Written when the file has no compatible_pipeline_version of its own, so the
# file Alka writes passes the same version check as the checked-in configs.
DEFAULT_COMPATIBLE_VERSION = ">=0.2.0"

_STAGE4_HEADER = (
    "# configs/08_stage4.yaml\n"
    "# Written by Alka (do not hand-edit unless you know why).\n"
    "# Enables the internal PyCO2SYS carbonate calculation in Stage 4:\n"
    "# DIC / Omega / pCO2 computed from RM-corrected TA + measured pH, at the\n"
    "# lab-temperature input / in-situ-temperature output convention.\n"
    "# Settings are pinned/validated (Lueker 2000; Dickson KSO4; Lee 2010\n"
    "# borate; Perez & Fraga KF; total pH scale). See carbonate_calc_design.md.\n"
)


def _read_stage4(path: Path) -> dict[str, Any]:
    """The existing Stage 4 file's own keys, after roap.stage_config checks it.

    Raises ValueError instead of exiting, so the GUI can report a bad file
    rather than overwrite it.
    """
    if not path.exists():
        return {}
    try:
        load_stage_config("stage4", path)
    except SystemExit as exc:
        raise ValueError(f"Not updating {path}: {exc}") from exc
    return dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _stage4_data(existing: dict[str, Any], carbonate_calc: dict[str, Any]) -> dict[str, Any]:
    """The existing keys with carbonate_calc updated; nothing else is dropped."""
    data = dict(existing)
    data["carbonate_calc"] = {**(data.get("carbonate_calc") or {}), **carbonate_calc}
    data.setdefault("compatible_pipeline_version", DEFAULT_COMPATIBLE_VERSION)
    return data


def _write_stage4(path: Path, existing: dict[str, Any], data: dict[str, Any]) -> bool:
    """Write ``data`` unless the file already holds it; True if written.

    Comparing parsed content (not text) leaves a hand-commented file that
    already says the same thing untouched.
    """
    if path.exists() and existing == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_STAGE4_HEADER + yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return True


@dataclass
class ConfigResult:
    """What the writer did, so the GUI can report it and the runner can use it."""
    config_dir: Optional[Path]   # dir to pass to --config-dir, or None
    written: list[Path]          # files written this call
    notes: list[str]             # human-readable summary lines


def write_stage_configs(
    project_root: Path,
    compute_carbonate_internally: bool,
    require_corrected_ta: bool = True,
    rm_reject_fraction_warn: float = 0.34,
    config_dir_name: str = "configs",
) -> ConfigResult:
    """Create/update the config files implied by the GUI options.

    Returns a ConfigResult whose `config_dir` should be passed to
    build_command(config_dir=...) when it is not None. When no options require
    a config, `config_dir` is None and the pipeline runs with built-in defaults.

    Only the files this call is responsible for are (re)written; other config
    files in the folder are left untouched.
    """
    config_dir = project_root / config_dir_name
    written: list[Path] = []
    notes: list[str] = []

    # Stage 4 carbonate calc toggle. Only carbonate_calc is changed; other
    # keys, including compatible_pipeline_version, are kept (#41).
    stage4_path = config_dir / "08_stage4.yaml"
    existing = _read_stage4(stage4_path)
    if compute_carbonate_internally:
        data = _stage4_data(
            existing,
            {
                "enabled": True,
                "require_corrected_ta": bool(require_corrected_ta),
                "rm_reject_fraction_warn": float(rm_reject_fraction_warn),
            },
        )
        if _write_stage4(stage4_path, existing, data):
            written.append(stage4_path)
            notes.append("Carbonate calculation ENABLED (wrote configs/08_stage4.yaml).")
        else:
            notes.append("Carbonate calculation already enabled (config unchanged).")
    elif stage4_path.exists():
        # Turned OFF with a file present: set enabled: false rather than
        # delete it, so the state is explicit and no file we didn't own is
        # removed.
        data = _stage4_data(existing, {"enabled": False})
        if _write_stage4(stage4_path, existing, data):
            written.append(stage4_path)
            notes.append("Carbonate calculation DISABLED (updated configs/08_stage4.yaml).")
        else:
            notes.append("Carbonate calculation off (config already disabled).")
    else:
        notes.append("Carbonate calculation off (using pipeline defaults).")

    # Decide whether a config dir needs to be passed at all: pass it if the
    # folder exists and contains any per-stage config the pipeline should read.
    has_configs = config_dir.exists() and any(config_dir.glob("*.yaml")) or \
        (config_dir.exists() and any(config_dir.glob("*.yml")))
    return ConfigResult(
        config_dir=config_dir if has_configs else None,
        written=written,
        notes=notes,
    )
