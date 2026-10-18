# tests/test_run_bundle.py
import json
import tempfile
from pathlib import Path
from roap.bundle import compute_file_hash, generate_run_bundle_manifest
import pytest

def test_generate_run_bundle_manifest(tmp_path):
    """Manifest generated with correct structure and hashes."""
    from roap.bundle import generate_run_bundle_manifest
    from roap import __version__
    
    # Create test files
    run_dir = tmp_path / "runs" / "2026-10-11T12-00-00Z_pid123"
    run_dir.mkdir(parents=True)
    input_xlsx = tmp_path / "input.xlsx"
    input_xlsx.write_bytes(b"fake excel content")
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "02_ta_ph_qc.yaml").write_text("compatible_pipeline_version: '>=0.2.0'\n")
    
    # Create output files
    out_data = run_dir / "oa_stage4_outputs" / "data"
    out_data.mkdir(parents=True)
    (out_data / "analysis_ready.csv").write_text("col1,col2\n1,2\n")
    
    manifest = generate_run_bundle_manifest(
        run_dir=run_dir,
        input_xlsx=input_xlsx,
        config_dir=config_dir,
        git_commit="abc123def456",
        pipeline_version=__version__
    )
    
    # Verify structure
    assert manifest["schema_version"] == "1.0"
    assert manifest["git_commit"] == "abc123def456"
    assert manifest["pipeline_version"] == __version__
    assert "timestamp" in manifest
    assert manifest["input_file"]["sha256"] == compute_file_hash(input_xlsx)
    assert len(manifest["config_files"]) == 1
    assert len(manifest["output_files"]) >= 1
    assert "roap" in manifest["package_versions"]