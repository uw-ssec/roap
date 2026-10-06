"""Migration gate: pipeline config YAML files are present and parseable."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "configs"

CONFIG_FILES = [
    "02_ta_ph_qc.yaml",
    "07_stage3.yaml",
    "08_stage4.yaml",
    "crm_certified_values.yaml",
    "cruise_grade_thresholds.yaml",
    "regional.yaml",
]


@pytest.mark.parametrize("fname", CONFIG_FILES)
def test_config_loads(fname: str) -> None:
    """Each migrated config exists and parses to a non-empty document."""
    path = CONFIG_DIR / fname
    assert path.exists(), f"Missing {fname}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data is not None, f"Empty config: {fname}"


def test_schema_aliases_placeholder_exists() -> None:
    """schema_aliases.yaml is reserved for P2; it may be empty for now."""
    assert (CONFIG_DIR / "schema_aliases.yaml").exists(), "Missing schema_aliases.yaml placeholder"
