"""
tests/test_config_gate.py
=======================
Test that config compatibility gate enforces version matching.
"""
import tempfile
from pathlib import Path

import pytest
import yaml

from roap.pipeline import run_pipeline


def _write_qc_config(tmpdir: str, compatible: str) -> None:
    config_path = Path("configs/02_ta_ph_qc.yaml")
    with config_path.open() as f:
        config = yaml.safe_load(f)
    config["compatible_pipeline_version"] = compatible
    with (Path(tmpdir) / "02_ta_ph_qc.yaml").open("w") as f:
        yaml.dump(config, f)


def test_config_compatibility_gate_enforced():
    """Stale config version must fail fast with actionable error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # A version HIGHER than any current CalVer release triggers failure
        _write_qc_config(tmpdir, ">=9999.1.0")
        output_dir = Path(tmpdir) / "outputs"

        # The pipeline should exit with clear error about version mismatch
        with pytest.raises(SystemExit) as excinfo:
            run_pipeline("examples/example_data.xlsx", output_dir, tmpdir, log=lambda _: None)

        assert "requires pipeline version" in str(excinfo.value.code).lower(), (
            f"Error should explain the version mismatch: {excinfo.value.code}"
        )
        # It fails before Stage QC writes anything
        assert not (output_dir / "oa_prelim_data__qc_outputs").exists()


def test_config_compatibility_gate_allows_current_version():
    """Config with current version should pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Every release (legacy 0.2.0 and all CalVer) satisfies >=0.2.0
        _write_qc_config(tmpdir, ">=0.2.0")
        output_dir = Path(tmpdir) / "outputs"

        # Should pass (or fail for other reasons, but not version)
        try:
            run_pipeline("examples/example_data.xlsx", output_dir, tmpdir, log=lambda _: None)
        except SystemExit as exc:
            assert "requires pipeline version" not in str(exc.code).lower(), (
                f"Should not fail on version with current version: {exc.code}"
            )
