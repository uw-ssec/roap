# tests/test_verify_bundle_cli.py
import json
import subprocess
from pathlib import Path

import pytest


def _make_bundle(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Valid run bundle; returns (run_dir, input_xlsx, config_yaml, output_csv)."""
    from roap.bundle import generate_run_bundle_manifest

    run_dir = tmp_path / "runs" / "2026-10-11T12-00-00Z_pid123"
    run_dir.mkdir(parents=True)
    input_xlsx = tmp_path / "input.xlsx"
    input_xlsx.write_bytes(b"original")
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_yaml = config_dir / "02_ta_ph_qc.yaml"
    config_yaml.write_text("compatible_pipeline_version: '>=0.2.0'\n", encoding="utf-8")

    out_data = run_dir / "oa_stage4_outputs" / "data"
    out_data.mkdir(parents=True)
    output_csv = out_data / "analysis_ready.csv"
    output_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    generate_run_bundle_manifest(run_dir, input_xlsx, config_dir, "abc123", "0.2.0")
    return run_dir, input_xlsx, config_yaml, output_csv


def _verify(run_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["roap", "verify-bundle", str(run_dir), *args], capture_output=True, text=True, encoding="utf-8"
    )


def test_verify_bundle_cli_valid(tmp_path):
    """CLI verify-bundle exits 0 when every recorded hash matches."""
    run_dir, *_ = _make_bundle(tmp_path)

    result = _verify(run_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Bundle OK" in result.stdout
    assert "3/3 files match" in result.stdout
    assert "stub" not in result.stdout.lower()


@pytest.mark.parametrize("target", ["input", "config", "output"])
def test_verify_bundle_cli_detects_corruption(tmp_path, target):
    """CLI verify-bundle exits 1 and names the file when any recorded file changes."""
    run_dir, input_xlsx, config_yaml, output_csv = _make_bundle(tmp_path)
    changed = {"input": input_xlsx, "config": config_yaml, "output": output_csv}[target]
    changed.write_bytes(changed.read_bytes() + b"tampered")

    result = _verify(run_dir)

    assert result.returncode == 1
    assert f"MISMATCH ({target})" in result.stdout
    assert "Bundle FAILED verification" in result.stdout


def test_verify_bundle_cli_detects_missing_output(tmp_path):
    """CLI verify-bundle exits 1 when a recorded output file is deleted."""
    run_dir, _, _, output_csv = _make_bundle(tmp_path)
    output_csv.unlink()

    result = _verify(run_dir)

    assert result.returncode == 1
    assert "MISSING (output)" in result.stdout


def test_verify_bundle_cli_json_report(tmp_path):
    """--json prints a per-file report, and the exit code still reflects the result."""
    run_dir, _, _, output_csv = _make_bundle(tmp_path)
    output_csv.write_text("col1,col2\n999,999\n", encoding="utf-8")

    result = _verify(run_dir, "--json")

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert report["error"] is None
    statuses = {c["kind"]: c["status"] for c in report["checks"]}
    assert statuses == {"input": "ok", "config": "ok", "output": "mismatch"}


def test_verify_bundle_cli_unreadable_manifest(tmp_path):
    """A manifest that is not valid JSON fails with exit 1 and an error message."""
    run_dir, *_ = _make_bundle(tmp_path)
    (run_dir / "run_bundle_manifest.json").write_text("{not json", encoding="utf-8")

    result = _verify(run_dir)

    assert result.returncode == 1
    assert "error" in result.stderr.lower()
