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

    Reads run_bundle_manifest.json and verifies:
    - Input file SHA256 matches
    - Config SHA256s match
    - Code version (git sha) matches
    - Output file hashes match
    """
    manifest_path = run_dir / "run_bundle_manifest.json"
    if not manifest_path.exists():
        typer.echo(f"Error: Manifest not found: {manifest_path}", err=True)
        raise typer.Exit(code=1)

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing manifest: {e}", err=True)
        raise typer.Exit(code=1)

    # Stage notebooks write the package version under
    # manifest["package_versions"]["roap"]; accept a flat "roap_version" too so
    # a future run-bundle manifest can use either shape.
    _pkg_versions = manifest.get("package_versions") or {}
    _version = _pkg_versions.get("roap") or manifest.get("roap_version") or "unknown"

    typer.echo(f"Verifying bundle: {run_dir}")
    typer.echo(f"  Pipeline version: {_version}")
    typer.echo(f"  Git commit: {manifest.get('git_commit', 'unknown')}")
    typer.echo(f"  Timestamp: {manifest.get('timestamp', 'unknown')}")

    # TODO: Implement actual verification logic
    typer.echo("  [STUB] Verification logic not yet implemented")
    if json_output:
        typer.echo(json.dumps({"status": "stub", "run_dir": str(run_dir), "manifest": manifest}))
