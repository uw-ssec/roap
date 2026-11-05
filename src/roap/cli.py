"""ROAP CLI — Typer-based command line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from . import __version__

app = typer.Typer(
    name="roap",
    help="Reproducible Ocean Acidification Pipeline (ROAP)",
    add_completion=False,
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"roap {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit"
    ),
) -> None:
    """ROAP - Reproducible Ocean Acidification Pipeline."""


@app.command()
def run(
    input_xlsx: Path = typer.Argument(..., help="Path to the input Excel workbook"),
    output_root: Path = typer.Argument(..., help="Directory for every Stage's outputs"),
    config_dir: Optional[Path] = typer.Option(
        None, "--config-dir", "-c", help="Directory with per-Stage configs (02_ta_ph_qc.yaml ... 08_stage4.yaml)"
    ),
    sheet: int = typer.Option(0, "--sheet", min=0, help="Zero-based Excel sheet index"),
    start_from: str = typer.Option("02", "--start-from", help="Skip Stages before this one: 02, 04, 05, 06, 07 or 08"),
    no_parquet: bool = typer.Option(False, "--no-parquet", help="Write CSV only for Stages 1A to 4"),
    runs_dir: Optional[Path] = typer.Option(
        None, "--runs-dir", help="Where to write run_bundle_manifest.json (default: OUTPUT_ROOT/runs/<timestamp>)"
    ),
) -> None:
    """Run Stage QC and Stages 1A to 4 on one workbook, in process."""
    from .pipeline import run_pipeline

    try:
        result = run_pipeline(
            input_xlsx,
            output_root,
            config_dir,
            sheet=sheet,
            start_from=start_from,
            no_parquet=no_parquet,
            runs_dir=runs_dir,
            log=typer.echo,
        )
    except SystemExit as exc:
        if exc.code in (None, 0):
            raise
        if not isinstance(exc.code, int):
            typer.echo(f"Error: {exc.code}", err=True)
        raise typer.Exit(code=exc.code if isinstance(exc.code, int) else 2)

    typer.echo("Pipeline complete.")
    if result["final"] is not None:
        typer.echo(f"  Final deliverable : {result['final']}")
    typer.echo(f"  Run bundle        : {result['runs_dir'] / 'run_bundle_manifest.json'}")


@app.command()
def validate(
    input_xlsx: Path = typer.Argument(..., help="Path to input Excel workbook"),
    config_dir: Optional[Path] = typer.Option(None, "--config-dir", "-c", help="Directory containing stage config YAMLs"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
    gui: bool = typer.Option(False, "--gui", help="Open GUI validation window (requires display)"),
) -> None:
    """Pre-flight validation of input Excel workbook.

    Checks: required columns present (via aliases), dtypes plausible,
    CRM/std tags correct, CRM_BATCH in certified values.
    """
    if not input_xlsx.exists():
        typer.echo(f"Error: Input file not found: {input_xlsx}", err=True)
        raise typer.Exit(code=1)

    if config_dir and not config_dir.exists():
        typer.echo(f"Error: Config directory not found: {config_dir}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Validating: {input_xlsx}")
    if config_dir:
        typer.echo(f"Using configs from: {config_dir}")

    # TODO: Implement actual validation logic
    # For now, just check file exists and is readable
    try:
        import pandas as pd
        df = pd.read_excel(input_xlsx, sheet_name=0)
        typer.echo(f"  Sheets: {df.shape[1]} columns, {df.shape[0]} rows")
        typer.echo("  [STUB] Validation logic not yet implemented")
        if json_output:
            typer.echo(json.dumps({"status": "stub", "file": str(input_xlsx), "rows": df.shape[0], "cols": df.shape[1]}))
    except Exception as e:
        typer.echo(f"Error reading Excel: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def verify_bundle(
    run_dir: Path = typer.Argument(..., help="Path to run directory (outputs/<run> or runs/<timestamp>)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Verify run bundle integrity.

    Reads run_bundle_manifest.json and checks the SHA256 of the input file,
    every config file and every output file it records. Exits 0 when all
    match, 1 when any file is missing, changed or unreadable, or the manifest is
    missing or unreadable.
    """
    from .bundle import check_bundle

    report = check_bundle(run_dir)
    if report["error"]:
        typer.echo(f"Error: {report['error']}", err=True)
        if json_output:
            typer.echo(json.dumps(report, indent=2))
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(report, indent=2))
    else:
        manifest = json.loads(Path(report["manifest"]).read_text(encoding="utf-8"))
        # Stage notebooks write the package version under
        # manifest["package_versions"]["roap"]; accept a flat "roap_version" too so
        # a future run-bundle manifest can use either shape.
        _pkg_versions = manifest.get("package_versions") or {}
        _version = _pkg_versions.get("roap") or manifest.get("roap_version") or "unknown"

        typer.echo(f"Verifying bundle: {run_dir}")
        typer.echo(f"  Pipeline version: {_version}")
        typer.echo(f"  Git commit: {manifest.get('git_commit', 'unknown')}")
        typer.echo(f"  Timestamp: {manifest.get('timestamp', 'unknown')}")
        for check in report["checks"]:
            if check["status"] != "ok":
                detail = f" [{check['reason']}]" if check["reason"] else ""
                typer.echo(f"  {check['status'].upper()} ({check['kind']}): {check['path']}{detail}")
        ok = sum(c["status"] == "ok" for c in report["checks"])
        typer.echo(f"  {ok}/{len(report['checks'])} files match")
        typer.echo("Bundle OK" if report["valid"] else "Bundle FAILED verification")

    if not report["valid"]:
        raise typer.Exit(code=1)
