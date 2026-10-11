"""
tests/test_config_gate.py
=======================
Test that config compatibility gate enforces version matching.
"""
import subprocess
import tempfile
import yaml
from pathlib import Path


def test_config_compatibility_gate_enforced():
    """Stale config version must fail fast with actionable error."""
    config_path = Path("configs/02_ta_ph_qc.yaml")
    with config_path.open() as f:
        config = yaml.safe_load(f)

    # Set to a version HIGHER than current (v0.2.0) to trigger failure
    config["compatible_pipeline_version"] = ">=1.0.0"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write modified config
        modified_config = Path(tmpdir) / "02_ta_ph_qc.yaml"
        with modified_config.open("w") as f:
            yaml.dump(config, f)

        # Try to run pipeline with stale config
        input_path = Path("examples/example_data.xlsx")
        output_dir = Path(tmpdir) / "outputs"

        # The pipeline should exit with clear error about version mismatch
        result = subprocess.run(
            ["pixi", "run", "./run_pipeline.sh", str(input_path), str(output_dir), "--config-dir", tmpdir],
            capture_output=True, text=True, timeout=60
        )

        # Should fail with version error
        assert result.returncode != 0, "Pipeline should fail with stale config"
        assert "version" in result.stderr.lower() or "compatible" in result.stderr.lower(), \
            f"Error should mention version/compatible: {result.stderr}"


def test_config_gate_version_parsing():
    """_version_satisfies and _parse_version handle specifiers correctly."""
    from roap.common import _version_satisfies, _parse_version

    # Parse version
    assert _parse_version("0.2.0") == (0, 2, 0)
    assert _parse_version("1.0.0") == (1, 0, 0)
    assert _parse_version("0.2.0.dev") == (0, 2, 0)  # truncates at 3 parts

    # Satisfies checks
    assert _version_satisfies("0.2.0", ">=0.1.0") == True
    assert _version_satisfies("0.2.0", ">=0.2.0") == True
    assert _version_satisfies("0.2.0", ">=0.3.0") == False
    assert _version_satisfies("0.2.0", "==0.2.0") == True
    assert _version_satisfies("0.2.0", "==0.1.0") == False
    assert _version_satisfies("0.2.0", "") == True  # no constraint = pass
    assert _version_satisfies("0.2.0", ">=1.0.0") == False


def test_config_compatibility_gate_allows_current_version():
    """Config with current version should pass."""
    config_path = Path("configs/02_ta_ph_qc.yaml")
    with config_path.open() as f:
        config = yaml.safe_load(f)

    # Current version is v0.2.0 (from pyproject.toml)
    config["compatible_pipeline_version"] = ">=0.2.0"

    with tempfile.TemporaryDirectory() as tmpdir:
        modified_config = Path(tmpdir) / "02_ta_ph_qc.yaml"
        with modified_config.open("w") as f:
            yaml.dump(config, f)

        input_path = Path("examples/example_data.xlsx")
        output_dir = Path(tmpdir) / "outputs"

        result = subprocess.run(
            ["pixi", "run", "./run_pipeline.sh", str(input_path), str(output_dir), "--config-dir", tmpdir],
            capture_output=True, text=True, timeout=120
        )

        # Should pass (or fail for other reasons, but not version)
        if result.returncode != 0:
            assert "version" not in result.stderr.lower(), \
                f"Should not fail on version with current version: {result.stderr}"