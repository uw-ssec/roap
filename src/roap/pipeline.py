"""Run the whole pipeline in process: Stage QC, then Stages 1A to 4 (ADR-0011).

:func:`run_pipeline` owns the Stage order and the output layout under the
output root. Each Stage reads the previous Stage's files from disk, calls
its ``run`` and saves the result with
:func:`roap.stage_result.write_stage_result`, which also writes that
Stage's run bundle. A run-level bundle covering the workbook, the configs
and every Stage's data files is written last.

``roap run`` and ``run_pipeline.sh`` both call this module; notebooks
02 and 04 to 08 stay available for interactive runs of one Stage.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from . import __version__, qc_ta_ph, stage1a, stage1b, stage2, stage3, stage4
from .common import is_none_like, read_excel_sheets
from .stage_config import StageConfig, load_stage_config
from .stage_result import StageResult, write_stage_result

__all__ = ["STAGE_ORDER", "run_pipeline"]

PathLike = Union[str, Path]

# Stage id (the notebook number) -> (config file stem, output folder).
STAGE_ORDER = ("02", "04", "05", "06", "07", "08")
_STAGES: Dict[str, tuple] = {
    "02": ("02_ta_ph_qc", "oa_prelim_data__qc_outputs"),
    "04": ("04_stage1a", "oa_stage1a_outputs"),
    "05": ("05_stage1b", "oa_stage1b_outputs"),
    "06": ("06_stage2", "oa_stage2_outputs"),
    "07": ("07_stage3", "oa_stage3_outputs"),
    "08": ("08_stage4", "oa_stage4_outputs"),
}
_CRM_VALUES_FILE = "crm_certified_values.yaml"


def _stage_config_path(config_dir: Optional[Path], stem: str, log: Callable[[str], None]) -> Optional[str]:
    if config_dir is None:
        return None
    for ext in ("yaml", "yml", "json"):
        candidate = config_dir / f"{stem}.{ext}"
        if candidate.is_file():
            return str(candidate)
    log(f"WARNING: no per stage config found for {stem} in {config_dir}; using defaults.")
    return None


def _default_crm_values() -> Optional[Path]:
    """configs/crm_certified_values.yaml from the working directory or the checkout."""
    for root in (Path.cwd(), Path(__file__).resolve().parents[2]):
        candidate = root / qc_ta_ph.CRM_CERTIFIED_VALUES_CONFIG
        if candidate.is_file():
            return candidate
    return None


def _crm_values_path(
    params: Dict[str, Any], config_dir: Optional[Path], input_xlsx: Path
) -> Optional[Path]:
    """The CRM certified-values file Stage QC loads, as notebook 02 picks it.

    A ``CRM_VALUES_CONFIG`` in the QC config wins, then the config dir's
    crm_certified_values.yaml, then the checked-in configs/ file. A relative
    path that does not exist is tried next to the workbook.
    """
    if "CRM_VALUES_CONFIG" in params:
        value = params["CRM_VALUES_CONFIG"]
        if is_none_like(value):
            return None
        path = Path(str(value)).expanduser()
        if not path.is_absolute() and not path.exists() and (input_xlsx.parent / path).exists():
            path = input_xlsx.parent / path
        return path
    if config_dir is not None:
        return config_dir / _CRM_VALUES_FILE
    return _default_crm_values()


def _run_qc(
    input_xlsx: Path, sheet: Union[int, str], out_dir: Path, cfg: StageConfig, config_dir: Optional[Path]
) -> StageResult:
    params = dict(cfg.config.get("parameters") or {})
    qc_params = qc_ta_ph.qc_run_parameters(params)
    crm_path = _crm_values_path(params, config_dir, input_xlsx)
    if qc_params["CRM_CORRECT_TA"] and crm_path is not None:
        cfg.load_crm_values(crm_path)
    result = qc_ta_ph.run(read_excel_sheets(input_xlsx, sheet), cfg, qc_params, source=str(input_xlsx))
    qc_ta_ph.anchor_manifest_paths(result, out_dir)
    result.manifest["parameters"].update(
        {
            "XLSX_PATH": str(input_xlsx),
            "OUT_DIR": str(out_dir),
            "SHEET": sheet,
            "CONFIG_PATH": cfg.source,
            "CRM_VALUES_CONFIG": str(crm_path) if crm_path is not None else None,
        }
    )
    return result


def _qc_derived_csv(qc_out: Path, input_xlsx: Path, sheet: Union[int, str]) -> Path:
    """The derived.csv Stage 1A reads: the selected sheet's, else the only one."""
    from .common import safe_sheet_name

    names = pd.ExcelFile(input_xlsx, engine="openpyxl").sheet_names
    if isinstance(sheet, int):
        if not 0 <= sheet < len(names):
            raise SystemExit(f"Sheet index {sheet} is out of range. Workbook has {len(names)} sheets.")
        name = names[sheet]
    else:
        name = str(sheet)
    expected = qc_out / f"sheet_{safe_sheet_name(name)}" / "data" / "derived.csv"
    if expected.is_file():
        return expected
    matches = sorted(qc_out.glob("*/data/derived.csv"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"Could not find Stage QC's derived.csv under {qc_out}. Run Stage QC first.")
    raise SystemExit(
        f"Multiple derived.csv files found under {qc_out}: "
        + ", ".join(str(m) for m in matches)
        + ". Use --sheet or clean OUTPUT_ROOT so only one sheet output is present."
    )


def _require(path: Path, label: str) -> Path:
    if not path.is_file():
        raise SystemExit(
            f"Missing required input for {label}: {path}\n"
            "Run earlier stages first or use the correct OUTPUT_ROOT."
        )
    return path


def _stage_params(stage: str, cfg_path: Optional[str], out_dir: Path, input_csv: Path, no_parquet: bool) -> Dict:
    # The parameters each notebook recorded, for the manifest.
    params: Dict[str, Any] = {
        "INPUT_CSV": str(input_csv),
        "OUT_DIR": str(out_dir),
        "CONFIG_PATH": cfg_path,
        "NO_PARQUET": no_parquet,
        "DRY_RUN": False,
    }
    if stage != "04":
        params["config_path_resolved"] = cfg_path
    return params


def run_pipeline(
    input_xlsx: PathLike,
    out_root: PathLike,
    config_dir: Optional[PathLike] = None,
    *,
    sheet: Union[int, str] = 0,
    start_from: str = "02",
    no_parquet: bool = False,
    runs_dir: Optional[PathLike] = None,
    git_commit: Optional[str] = None,
    log: Callable[[str], None] = print,
) -> Dict[str, Any]:
    """Run Stage QC and Stages 1A to 4 on one workbook, in process.

    Writes each Stage under ``out_root/oa_*_outputs`` and a run bundle
    (``run_bundle_manifest.json``) under ``runs_dir``, which defaults to
    ``out_root/runs/<UTC timestamp>``. ``config_dir`` may hold one file per
    Stage (``02_ta_ph_qc.yaml`` ... ``08_stage4.yaml``, or ``.yml``/``.json``)
    and ``crm_certified_values.yaml``. ``start_from`` ("02", "04" ... "08")
    skips earlier Stages and reads their outputs from ``out_root``.

    Returns ``{"out_root", "runs_dir", "stages": {stage id: output dir},
    "final": path to Stage 4's analysis_ready.csv or None}``. A failed
    check stops with ``SystemExit`` naming the problem.
    """
    if start_from not in STAGE_ORDER:
        raise SystemExit(f"--start-from must be one of {', '.join(STAGE_ORDER)}. Got: {start_from}")
    input_xlsx = Path(input_xlsx).expanduser().resolve()
    if not input_xlsx.is_file():
        raise SystemExit(f"File not found: {input_xlsx}")
    out_root = Path(out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    cfg_dir = Path(config_dir).expanduser().resolve() if config_dir is not None else None
    if cfg_dir is not None and not cfg_dir.is_dir():
        raise SystemExit(f"Config directory not found: {cfg_dir}")
    if runs_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        runs_dir = out_root / "runs" / f"{stamp}_pid{os.getpid()}"
    run_path = Path(runs_dir).expanduser().resolve()
    run_path.mkdir(parents=True, exist_ok=True)

    if STAGE_ORDER.index(start_from) > STAGE_ORDER.index("06"):
        # AUDIT FIX N-5: Stage 4 needs depth_round_m, normally from Stage 2.
        log(
            f"WARNING: --start-from {start_from} skips Stage 2 (06_stage2). Stage 4's "
            "depth_round_m fallback (derived from depth_m) will be used if the upstream "
            "input lacks it; re-run from Stage 2 for proper depth keys before final delivery."
        )

    dirs = {stage: out_root / folder for stage, (_, folder) in _STAGES.items()}
    stages_run: Dict[str, Path] = {}
    todo: List[str] = list(STAGE_ORDER[STAGE_ORDER.index(start_from):])

    for stage in todo:
        stem, _ = _STAGES[stage]
        out_dir = dirs[stage]
        cfg_path = _stage_config_path(cfg_dir, stem, log)
        log(f"---- Stage {stage} ({stem}) -> {out_dir}")

        if stage == "02":
            cfg = load_stage_config("qc", cfg_path)
            result = _run_qc(input_xlsx, sheet, out_dir, cfg, cfg_dir)
            for warning in cfg.warnings:
                log(f"WARNING: {warning}")
            write_stage_result(result, out_dir, parquet=False)
            stages_run[stage] = out_dir
            continue

        if stage == "04":
            input_csv = _require(_qc_derived_csv(dirs["02"], input_xlsx, sheet), "Stage 04")
        else:
            input_csv = _require(
                {
                    "05": dirs["04"] / "data" / "staged.csv",
                    "06": dirs["05"] / "data" / "analysis_ready_samples.csv",
                    "07": dirs["06"] / "data" / "enhanced.csv",
                    "08": dirs["07"] / "data" / "enhanced.csv",
                }[stage],
                f"Stage {stage}",
            )
        stage_name = {"04": "stage1a", "05": "stage1b", "06": "stage2", "07": "stage3", "08": "stage4"}[stage]
        cfg = load_stage_config(stage_name, cfg_path)
        for warning in cfg.warnings:
            log(f"WARNING: {warning}")
        df = pd.read_csv(input_csv)
        source = str(input_csv)
        try:
            if stage == "04":
                result = stage1a.run(df, cfg, source=source)
            elif stage == "05":
                result = stage1b.run(df, cfg, source=source)
            elif stage == "06":
                result = stage2.run(df, cfg, source=source)
            elif stage == "07":
                result = stage3.run(df, cfg, source=source)
            else:
                result = stage4.run(df, cfg, source=source)
        except ValueError as exc:
            raise SystemExit(f"Stage {stage} failed: {exc}") from exc

        params = _stage_params(stage, cfg_path, out_dir, input_csv, no_parquet)
        if stage == "04":
            params.update({"DUPLICATE_KEYS": None, "PRINT_COLUMNS": False})
        elif stage == "05":
            params["PRINT_COLUMNS"] = False
        elif stage == "08":
            params.update({"NO_RANGE_CHECKS": False, "NO_DIC_SPECIES_CHECK": False})
        result.manifest["output_root"] = str(out_dir)
        result.manifest["parameters"].update(params)
        if stage == "08":
            log(result.manifest["carbonate_calc"]["note"])
        write_stage_result(result, out_dir, parquet=not no_parquet)
        stages_run[stage] = out_dir

    final = dirs["08"] / "data" / "analysis_ready.csv"
    if "08" in stages_run:
        _require(final, "final Stage 4 deliverable")

    from .bundle import _current_git_commit, generate_run_bundle_manifest

    generate_run_bundle_manifest(
        run_dir=run_path,
        input_xlsx=input_xlsx,
        config_dir=cfg_dir,
        git_commit=git_commit or _current_git_commit(),
        pipeline_version=__version__,
        output_root=out_root,
    )
    return {
        "out_root": out_root,
        "runs_dir": run_path,
        "stages": stages_run,
        "final": final if final.is_file() else None,
    }
