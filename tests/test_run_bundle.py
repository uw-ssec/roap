# tests/test_run_bundle.py
import json
import subprocess
import sys
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
        git_commit="test-commit-abc123",
        pipeline_version=__version__
    )

    # Verify structure
    assert manifest["schema_version"] == "1.0"
    assert manifest["git_commit"] == "test-commit-abc123"
    assert manifest["pipeline_version"] == __version__
    assert "timestamp" in manifest
    assert manifest["input_file"]["sha256"] == compute_file_hash(input_xlsx)
    assert len(manifest["config_files"]) == 1
    assert len(manifest["output_files"]) >= 1
    assert "roap" in manifest["package_versions"]


# Under -X warn_default_encoding, any open()/read_text() without an explicit
# encoding emits EncodingWarning (PEP 597). Promoting it to an error makes a
# locale-dependent read fail on every OS, not just on Windows (cp1252).
_STRICT_ENCODING = [sys.executable, "-X", "warn_default_encoding", "-W", "error::EncodingWarning", "-c"]


def _bundle_with_non_ascii_paths(tmp_path: Path) -> Path:
    """Valid bundle whose manifest records non-ASCII absolute paths."""
    root = tmp_path / "José_données"
    run_dir = root / "runs" / "2026-10-11T12-00-00Z_pid123"
    run_dir.mkdir(parents=True)
    input_xlsx = root / "entrée.xlsx"
    input_xlsx.write_bytes(b"fake excel content")
    out_data = run_dir / "oa_stage4_outputs" / "data"
    out_data.mkdir(parents=True)
    (out_data / "analysis_ready.csv").write_text("col1,col2\n1,2\n", encoding="utf-8")
    generate_run_bundle_manifest(run_dir, input_xlsx, None, "abc123", "0.2.0")
    return run_dir


def test_verify_bundle_reads_manifest_as_utf8(tmp_path):
    """verify_bundle must not depend on the locale encoding (#34)."""
    run_dir = _bundle_with_non_ascii_paths(tmp_path)
    code = "import sys; from roap.bundle import verify_bundle; sys.exit(0 if verify_bundle(__import__('pathlib').Path(sys.argv[1])) else 3)"
    result = subprocess.run([*_STRICT_ENCODING, code, str(run_dir)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr


def test_verify_bundle_cli_reads_manifest_as_utf8(tmp_path):
    """`roap verify-bundle` must not depend on the locale encoding (#34)."""
    run_dir = _bundle_with_non_ascii_paths(tmp_path)
    code = "import sys; from roap.cli import app; sys.argv = ['roap', 'verify-bundle', sys.argv[1]]; app()"
    result = subprocess.run([*_STRICT_ENCODING, code, str(run_dir)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr


def _default_run_with_stage_logs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Run laid out like run_pipeline.sh with no --config-dir.

    Returns (run_dir, output_root, crm_yaml, effective_config).
    """
    run_dir = tmp_path / "runs" / "2026-11-04T12-00-00Z_pid1"
    run_dir.mkdir(parents=True)
    input_xlsx = tmp_path / "input.xlsx"
    input_xlsx.write_bytes(b"input")
    crm_yaml = tmp_path / "configs" / "crm_certified_values.yaml"
    crm_yaml.parent.mkdir()
    crm_yaml.write_text("213: 2210.0\n", encoding="utf-8")
    output_root = tmp_path / "out"

    prelim_logs = output_root / "oa_prelim_data__qc_outputs" / "logs"
    prelim_logs.mkdir(parents=True)
    (prelim_logs / "manifest.json").write_text(
        json.dumps({"config": {"config_path": None, "crm_values_path": str(crm_yaml)}}), encoding="utf-8"
    )
    stage4 = output_root / "oa_stage4_outputs"
    (stage4 / "logs").mkdir(parents=True)
    effective_config = stage4 / "logs" / "effective_config.json"
    effective_config.write_text('{"parameters": {"flag_strict": true}}', encoding="utf-8")
    (stage4 / "logs" / "manifest.json").write_text("{}", encoding="utf-8")
    (stage4 / "data").mkdir()
    (stage4 / "data" / "analysis_ready.csv").write_text("a\n1\n", encoding="utf-8")

    generate_run_bundle_manifest(run_dir, input_xlsx, None, "abc123", "2026.11.0", output_root=output_root)
    return run_dir, output_root, crm_yaml, effective_config


def test_default_run_records_config_files_stages_used(tmp_path):
    """With no --config-dir, the manifest still records the configs the stages used."""
    run_dir, _, crm_yaml, effective_config = _default_run_with_stage_logs(tmp_path)

    manifest = json.loads((run_dir / "run_bundle_manifest.json").read_text(encoding="utf-8"))

    recorded = {Path(c["path"]): c["sha256"] for c in manifest["config_files"]}
    assert recorded == {
        effective_config.resolve(): compute_file_hash(effective_config),
        crm_yaml.resolve(): compute_file_hash(crm_yaml),
    }


@pytest.mark.parametrize("which", ["crm_yaml", "effective_config"])
def test_default_run_config_change_fails_verification(tmp_path, which):
    """Changing a config the run used makes the bundle fail verification."""
    from roap.bundle import check_bundle

    run_dir, _, crm_yaml, effective_config = _default_run_with_stage_logs(tmp_path)
    changed = {"crm_yaml": crm_yaml, "effective_config": effective_config}[which]
    changed.write_bytes(changed.read_bytes() + b"\n")

    report = check_bundle(run_dir)

    assert report["valid"] is False
    bad = [c for c in report["checks"] if c["status"] != "ok"]
    assert [(c["kind"], Path(c["path"])) for c in bad] == [("config", changed.resolve())]
