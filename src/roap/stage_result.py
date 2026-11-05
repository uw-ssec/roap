"""What a Stage's ``run`` returns, and the two writers that save it (ADR-0011).

A Stage's ``run(inputs, config)`` does no disk IO. It returns a
:class:`StageResult` holding everything the Stage produced, keyed by the
output path relative to the Stage's output directory (today's file names):

- ``data``: the Stage's output DataFrames, the files the next Stage reads.
  Each is saved as CSV and, unless disabled, Parquet beside it.
- ``tables``: other named DataFrames (QC tables, inventories), saved as CSV.
- ``reports``: markdown text.
- ``figures``: matplotlib Figure objects, saved in the format their suffix
  names.
- ``texts``: other text files (an HTML table, ``logs/effective_config.json``).
- ``manifest``: the entries for ``logs/manifest.json``.

:func:`render_stage_result` turns a result into file bytes.
:func:`write_stage_result` saves those bytes under an output directory and
writes the Stage's run bundle; :func:`write_stage_result_to_memory` returns
them as a dict, so tests can inspect a Stage's files without touching disk.
"""

from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

__all__ = [
    "MANIFEST_PATH",
    "StageResult",
    "json_text",
    "package_versions",
    "render_stage_result",
    "write_stage_result",
    "write_stage_result_to_memory",
]

MANIFEST_PATH = "logs/manifest.json"


@dataclass
class StageResult:
    """Everything one Stage run produced, keyed by relative output path."""

    stage: str
    data: Dict[str, pd.DataFrame] = field(default_factory=dict)
    tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    reports: Dict[str, str] = field(default_factory=dict)
    figures: Dict[str, Any] = field(default_factory=dict)
    texts: Dict[str, str] = field(default_factory=dict)
    manifest: Dict[str, Any] = field(default_factory=dict)
    # Provenance for the run bundle: the file the inputs were read from and
    # each config file the caller loaded. Labels only; run() never opens them.
    input_file: Optional[str] = None
    config_files: List[Optional[str]] = field(default_factory=list)
    # The manifest's "notebook" name, which the run bundle also records.
    bundle_name: Optional[str] = None
    figure_dpi: int = 240


def package_versions() -> Dict[str, Optional[str]]:
    """Versions of the packages a Stage run depends on, for its manifest."""
    import importlib

    versions: Dict[str, Optional[str]] = {
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
    }
    for name in ("numpy", "matplotlib", "openpyxl", "pyarrow"):
        try:
            versions[name] = importlib.import_module(name).__version__
        except Exception:
            versions[name] = None
    try:
        from roap import __version__ as roap_version

        versions["roap"] = roap_version
    except Exception:
        versions["roap"] = None
    return versions


def _parquet_path(rel: str) -> str:
    return str(PurePosixPath(rel).with_suffix(".parquet"))


def _check_rel(rel: str) -> str:
    path = PurePosixPath(rel)
    if path.is_absolute() or ".." in path.parts or not path.suffix:
        raise ValueError(f"StageResult paths must be relative file paths, got {rel!r}")
    return rel


def json_text(obj: Any) -> str:
    """JSON text with the same layout as ``roap.common.write_json``."""
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _json_bytes(obj: Any) -> bytes:
    return json_text(obj).encode("utf-8")


def _data_csv_bytes(df: pd.DataFrame) -> bytes:
    # Same CSV settings as roap.common.write_csv_and_parquet.
    return df.to_csv(
        index=False,
        encoding="utf-8",
        na_rep="",
        lineterminator="\n",
        date_format="%Y-%m-%dT%H:%M:%SZ",
    ).encode("utf-8")


def _table_csv_bytes(df: pd.DataFrame) -> bytes:
    # Same as DataFrame.to_csv(path, index=False), which the notebooks used.
    return df.to_csv(index=False).encode("utf-8")


def _figure_bytes(fig: Any, rel: str, dpi: int) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format=PurePosixPath(rel).suffix.lstrip("."), dpi=dpi, bbox_inches="tight")
    return buf.getvalue()


def _render_outputs(
    result: StageResult, parquet: bool
) -> Tuple[Dict[str, bytes], Dict[str, Dict[str, Any]]]:
    files: Dict[str, bytes] = {}
    parquet_status: Dict[str, Dict[str, Any]] = {}

    for rel, df in result.data.items():
        files[_check_rel(rel)] = _data_csv_bytes(df)
        status: Dict[str, Any] = {"written": False, "error": "Parquet disabled by user"}
        if parquet:
            try:
                buf = io.BytesIO()
                df.to_parquet(buf, index=False)
                files[_parquet_path(rel)] = buf.getvalue()
                status = {"written": True, "error": None}
            except Exception as exc:  # same policy as write_csv_and_parquet
                print(f"\nWARNING: Parquet encoding failed for {rel}: {exc}\n", file=sys.stderr)
                status = {"written": False, "error": str(exc)}
        parquet_status[rel] = status

    for rel, df in result.tables.items():
        files[_check_rel(rel)] = _table_csv_bytes(df)
    for rel, text in result.reports.items():
        files[_check_rel(rel)] = text.encode("utf-8")
    for rel, fig in result.figures.items():
        files[_check_rel(rel)] = _figure_bytes(fig, rel, result.figure_dpi)
    for rel, text in result.texts.items():
        files[_check_rel(rel)] = text.encode("utf-8")

    if MANIFEST_PATH in files:
        raise ValueError(f"{MANIFEST_PATH} is written from StageResult.manifest")
    return files, parquet_status


def _manifest_bytes(
    result: StageResult, outputs: List[str], parquet_status: Dict[str, Dict[str, Any]]
) -> bytes:
    manifest = dict(result.manifest)
    manifest["outputs"] = outputs
    if parquet_status:
        manifest["parquet"] = parquet_status
    return _json_bytes(manifest)


def render_stage_result(result: StageResult, *, parquet: bool = True) -> Dict[str, bytes]:
    """Return ``{relative path: file bytes}`` for every file ``result`` saves.

    Includes ``logs/manifest.json``: the result's manifest plus an
    ``outputs`` list of relative paths and each data file's Parquet status
    under ``parquet``. A Parquet file that fails to encode is left out and
    its error recorded, as ``write_csv_and_parquet`` did.
    """
    files, parquet_status = _render_outputs(result, parquet)
    files[MANIFEST_PATH] = _manifest_bytes(result, list(files), parquet_status)
    return files


def write_stage_result_to_memory(result: StageResult, *, parquet: bool = True) -> Dict[str, bytes]:
    """The in-memory writer: the files ``write_stage_result`` would save."""
    return render_stage_result(result, parquet=parquet)


def write_stage_result(
    result: StageResult,
    out_dir: Union[str, Path],
    *,
    parquet: bool = True,
    bundle: bool = True,
) -> Dict[str, Path]:
    """The disk writer: save ``result`` under ``out_dir`` and return the paths.

    The manifest's ``outputs`` lists absolute paths. With ``bundle`` (the
    default), writes ``run_bundle_manifest.json`` last, hashing the input,
    the configs and every file this call wrote, so
    ``roap verify-bundle <out_dir>`` can check them later.
    """
    from roap.bundle import generate_stage_bundle_manifest, snapshot_out_dir

    out_root = Path(out_dir).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    before = snapshot_out_dir(out_root)

    files, parquet_status = _render_outputs(result, parquet)
    outputs = [str(out_root / rel) for rel in files]
    files[MANIFEST_PATH] = _manifest_bytes(result, outputs, parquet_status)

    written: Dict[str, Path] = {}
    for rel, payload in files.items():
        path = out_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(payload)
        tmp.replace(path)
        written[rel] = path

    if bundle:
        if result.input_file is None or result.bundle_name is None:
            raise ValueError("A run bundle needs StageResult.input_file and bundle_name")
        generate_stage_bundle_manifest(
            out_root,
            notebook=result.bundle_name,
            input_file=Path(result.input_file),
            config_files=result.config_files,
            before=before,
        )
    return written
