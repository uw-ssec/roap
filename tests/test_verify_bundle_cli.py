# tests/test_verify_bundle_cli.py
import subprocess
import tempfile
from pathlib import Path
import json

def test_verify_bundle_cli_valid(tmp_path):
    """CLI verify-bundle exits 0 for valid bundle."""
    from roap.bundle import generate_run_bundle_manifest
    
    # Setup valid bundle
    run_dir = tmp_path / "runs" / "2026-10-11T12-00-00Z_pid123"
    run_dir.mkdir(parents=True)
    input_xlsx = tmp_path / "input.xlsx"
    input_xlsx.write_bytes(b"original")
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "02_ta_ph_qc.yaml").write_text("compatible_pipeline_version: '>=0.2.0'\n")
    
    out_data = run_dir / "oa_stage4_outputs" / "data"
    out_data.mkdir(parents=True)
    output_csv = out_data / "analysis_ready.csv"
    output_csv.write_text("col1,col2\n1,2\n")
    
    # Generate manifest
    manifest = generate_run_bundle_manifest(
        run_dir, input_xlsx, config_dir, "abc123", "0.2.0"
    )
    manifest_path = run_dir / "run_bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    # CLI verify-bundle should exit 0
    result = subprocess.run(
        ["roap", "verify-bundle", str(run_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "valid" in result.stdout.lower() or "verified" in result.stdout.lower()

def test_verify_bundle_cli_invalid(tmp_path):
    """CLI verify-bundle exits 1 for corrupted bundle."""
    from roap.bundle import generate_run_bundle_manifest
    
    # Setup valid bundle
    run_dir = tmp_path / "runs" / "2026-10-11T12-00-00Z_pid123"
    run_dir.mkdir(parents=True)
    input_xlsx = tmp_path / "input.xlsx"
    input_xlsx.write_bytes(b"original")
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "02_ta_ph_qc.yaml").write_text("compatible_pipeline_version: '>=0.2.0'\n")
    
    out_data = run_dir / "oa_stage4_outputs" / "data"
    out_data.mkdir(parents=True)
    output_csv = out_data / "analysis_ready.csv"
    output_csv.write_text("col1,col2\n1,2\n")
    
    # Generate manifest
    manifest = generate_run_bundle_manifest(run_dir, input_xlsx, config_dir, "abc123", "0.2.0")
    manifest_path = run_dir / "run_bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    # Corrupt output file
    output_csv.write_text("col1,col2\n999,999\n")
    
    # CLI verify-bundle should exit 1
    result = subprocess.run(
        ["roap", "verify-bundle", str(run_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "error" in result.stderr.lower() or "corrupt" in result.stdout.lower() or "mismatch" in result.stdout.lower()