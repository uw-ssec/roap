"""Tests for roap.stage_config: one config precedence rule per Stage (#41).

All in-process: no notebook or pipeline subprocess.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

from roap import stage_config as sc
from roap.alka.config_writer import write_stage_configs
from roap.policy import STAGE1_RANGE_DEFAULTS, STAGE4_RANGE_DEFAULTS
from roap.stage4 import STAGE4_DEFAULTS

REPO_ROOT = Path(__file__).resolve().parent.parent
OK_VERSION = {"compatible_pipeline_version": ">=0.2.0"}


def _write(tmp_path: Path, data: dict, name: str = "cfg.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# =============================================================================
# Precedence: built-in defaults <- the Stage's own file, nothing else
# =============================================================================


@pytest.mark.parametrize("stage", sc.STAGES)
@pytest.mark.parametrize("path", [None, "", "None", "null"])
def test_no_file_gives_the_stage_defaults(stage, path) -> None:
    result = sc.load_stage_config(stage, path)
    assert result.config == sc.stage_defaults(stage)
    assert result.source is None
    assert result.warnings == []


def test_stage_defaults_are_independent_copies() -> None:
    a = sc.stage_defaults("stage4")
    a["range_policy"]["ph_min"] = -1
    assert sc.stage_defaults("stage4")["range_policy"]["ph_min"] == 6.0


@pytest.mark.parametrize("stage", ["stage2", "stage3", "stage4"])
def test_later_stages_do_not_merge_schema_defaults(tmp_path, stage) -> None:
    result = sc.load_stage_config(stage, _write(tmp_path, OK_VERSION))
    for schema_key in ("canonical_candidates", "canonical_export_order", "required_columns"):
        assert schema_key not in result.config


def test_stage1b_defaults_layer_stage1b_over_schema(tmp_path) -> None:
    path = _write(tmp_path, {**OK_VERSION, "analysis_policy": {"phstd_fail_blocks_corrected_ph": True}})
    config = sc.load_stage_config("stage1b", path).config
    defaults = sc.stage_defaults("stage1b")
    assert "canonical_candidates" in config and "ta_precedence" in config
    # A nested override deep-merges: the other analysis_policy keys survive.
    assert config["analysis_policy"]["phstd_fail_blocks_corrected_ph"] is True
    assert set(config["analysis_policy"]) == set(defaults["analysis_policy"])


def test_stage2_keeps_user_only_keys(tmp_path) -> None:
    """#39: a key Stage 2 reads with no default is kept."""
    path = _write(tmp_path, {**OK_VERSION, "required_stage2_input_columns": ["sample_id"]})
    config = sc.load_stage_config("stage2", path).config
    assert config["required_stage2_input_columns"] == ["sample_id"]


# =============================================================================
# Range policy: each Stage owns its defaults
# =============================================================================


def test_stage4_range_policy_ignores_stage1_defaults_when_a_file_is_passed(tmp_path) -> None:
    """The bug: any Stage 4 file used to pull in the Stage 1 pH 7-9 / TA 1000-3000."""
    path = _write(tmp_path, {**OK_VERSION, "carbonate_calc": {"enabled": True}})
    policy = sc.load_stage_config("stage4", path).range_policy
    assert (policy.ph_min, policy.ph_max) == (6.0, 9.5)
    assert (policy.ta_min, policy.ta_max) == (0.0, 3500.0)


@pytest.mark.parametrize(
    ("stage", "defaults"),
    [("stage1a", STAGE1_RANGE_DEFAULTS), ("stage1b", STAGE1_RANGE_DEFAULTS), ("stage4", STAGE4_RANGE_DEFAULTS)],
)
def test_range_policy_defaults_and_explicit_override(tmp_path, stage, defaults) -> None:
    default_policy = sc.load_stage_config(stage).range_policy
    assert (default_policy.ph_min, default_policy.ph_max) == (defaults["ph_min"], defaults["ph_max"])

    path = _write(tmp_path, {**OK_VERSION, "range_policy": {"ph_min": 6.5}})
    policy = sc.load_stage_config(stage, path).range_policy
    assert policy.ph_min == 6.5
    assert policy.ph_max == defaults["ph_max"]


@pytest.mark.parametrize("stage", ["qc", "stage2", "stage3"])
def test_stages_without_range_checks_have_no_policy_and_reject_one(tmp_path, stage) -> None:
    assert sc.load_stage_config(stage).range_policy is None
    with pytest.raises(SystemExit, match="unknown key"):
        sc.load_stage_config(stage, _write(tmp_path, {**OK_VERSION, "range_policy": {"ph_min": 6.5}}))


def test_invalid_range_policy_is_an_error(tmp_path) -> None:
    with pytest.raises(SystemExit, match="range_policy"):
        sc.load_stage_config("stage4", _write(tmp_path, {**OK_VERSION, "range_policy": {"ph_minn": 1}}))


def test_stage4_range_defaults_agree_with_stage4_module() -> None:
    """STAGE4_DEFAULTS['range_policy'] and policy.STAGE4_RANGE_DEFAULTS must not drift."""
    for key, value in STAGE4_DEFAULTS["range_policy"].items():
        assert STAGE4_RANGE_DEFAULTS[key] == value, key


# =============================================================================
# Unknown keys
# =============================================================================


@pytest.mark.parametrize("stage", ["stage1a", "stage1b", "stage2", "stage3", "stage4"])
def test_unknown_top_level_key_is_an_error(tmp_path, stage) -> None:
    with pytest.raises(SystemExit, match=r"unknown key\(s\) \['not_a_key'\]"):
        sc.load_stage_config(stage, _write(tmp_path, {**OK_VERSION, "not_a_key": 1}))


def test_qc_unknown_top_level_and_parameter_keys_are_errors(tmp_path) -> None:
    with pytest.raises(SystemExit, match="unknown key"):
        sc.load_stage_config("qc", _write(tmp_path, {**OK_VERSION, "PH_COL": "x"}))
    with pytest.raises(SystemExit, match=r"unknown parameter\(s\) \['PH_COLL'\]"):
        sc.load_stage_config("qc", _write(tmp_path, {**OK_VERSION, "parameters": {"PH_COLL": "x"}}))
    with pytest.raises(SystemExit, match="must be a mapping"):
        sc.load_stage_config("qc", _write(tmp_path, {**OK_VERSION, "parameters": ["PH_COL"]}))


@pytest.mark.parametrize("key", sorted(sc.REMOVED_QC_PARAMETERS))
def test_qc_removed_parameters_name_their_replacement(tmp_path, key) -> None:
    with pytest.raises(SystemExit, match=f"{key} was removed"):
        sc.load_stage_config("qc", _write(tmp_path, {**OK_VERSION, "parameters": {key: "x"}}))


def test_qc_parameters_override_and_are_returned(tmp_path) -> None:
    path = _write(tmp_path, {**OK_VERSION, "parameters": {"PH_COL": "ph_observed", "MIN_CRM_N": 3}})
    assert sc.load_stage_config("qc", path).config["parameters"] == {"PH_COL": "ph_observed", "MIN_CRM_N": 3}


def test_qc_empty_parameters_block_means_defaults(tmp_path) -> None:
    path = tmp_path / "02_ta_ph_qc.yaml"
    path.write_text('compatible_pipeline_version: ">=0.2.0"\nparameters:\n', encoding="utf-8")
    assert sc.load_stage_config("qc", path).config["parameters"] == {}


@pytest.mark.parametrize("value", [[], False, 0, "", ["PH_COL"], "PH_COL"])
def test_qc_non_mapping_parameters_are_errors_even_when_falsy(tmp_path, value) -> None:
    with pytest.raises(SystemExit, match="'parameters' must be a mapping"):
        sc.load_stage_config("qc", _write(tmp_path, {**OK_VERSION, "parameters": value}))


@pytest.mark.parametrize("stage", ["stage1a", "stage1b", "stage4"])
def test_empty_range_policy_block_means_stage_defaults(tmp_path, stage) -> None:
    path = tmp_path / "cfg.yaml"
    path.write_text('compatible_pipeline_version: ">=0.2.0"\nrange_policy:\n', encoding="utf-8")
    resolved = sc.load_stage_config(stage, path)
    assert resolved.range_policy == sc.load_stage_config(stage).range_policy
    if "range_policy" in sc.stage_defaults(stage):
        assert resolved.config["range_policy"] == sc.stage_defaults(stage)["range_policy"]


@pytest.mark.parametrize("value", [[], False, 0, "", [1]])
def test_non_mapping_range_policy_is_an_error_even_when_falsy(tmp_path, value) -> None:
    with pytest.raises(SystemExit, match="'range_policy' must be a mapping"):
        sc.load_stage_config("stage4", _write(tmp_path, {**OK_VERSION, "range_policy": value}))


def test_qc_parameters_match_notebook_02_parameters_cell() -> None:
    nb = json.loads((REPO_ROOT / "notebooks" / "02_ta_ph_qc.ipynb").read_text(encoding="utf-8"))
    cell = next(c for c in nb["cells"] if "parameters" in c.get("metadata", {}).get("tags", []))
    tree = ast.parse("".join(cell["source"]))
    names = {node.targets[0].id for node in tree.body if isinstance(node, ast.Assign)}
    # REPO_ROOT is a helper and CONFIG_PATH names the file itself.
    assert sc.QC_PARAMETERS == names - {"REPO_ROOT", "CONFIG_PATH"}


def test_unknown_stage_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown stage"):
        sc.load_stage_config("stage5")


# =============================================================================
# compatible_pipeline_version
# =============================================================================


def test_missing_version_is_a_warning(tmp_path) -> None:
    path = _write(tmp_path, {"carbonate_calc": {"enabled": True}})
    result = sc.load_stage_config("stage4", path)
    assert len(result.warnings) == 1
    assert "compatible_pipeline_version" in result.warnings[0]
    assert str(path.resolve()) in result.warnings[0]


@pytest.mark.parametrize(
    ("required", "message"),
    [
        (">=9999.1.0", "requires pipeline version"),
        ("==0.0.1", "requires pipeline version"),
        ("<2", "invalid compatible_pipeline_version"),
        ("~=2026.11", "invalid compatible_pipeline_version"),
        ("2026.11.0", "invalid compatible_pipeline_version"),
        (">=not-a-version", "invalid compatible_pipeline_version"),
    ],
)
def test_unmet_or_unsupported_version_is_an_error(tmp_path, required, message) -> None:
    path = _write(tmp_path, {"compatible_pipeline_version": required})
    with pytest.raises(SystemExit, match=message):
        sc.load_stage_config("stage3", path)


def test_json_config_and_unreadable_files(tmp_path) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({**OK_VERSION, "thresholds": {}}), encoding="utf-8")
    assert sc.load_stage_config("stage3", path).source == str(path.resolve())

    with pytest.raises(SystemExit, match="not found"):
        sc.load_stage_config("stage3", tmp_path / "missing.yaml")
    bad = tmp_path / "cfg.toml"
    bad.write_text("x = 1", encoding="utf-8")
    with pytest.raises(SystemExit, match="Unsupported config format"):
        sc.load_stage_config("stage3", bad)
    top = _write(tmp_path, ["a"], name="list.yaml")
    with pytest.raises(SystemExit, match="mapping at the top level"):
        sc.load_stage_config("stage3", top)


# =============================================================================
# CRM Certified values (Stage QC)
# =============================================================================


def _crm_file(tmp_path: Path, version: bool) -> Path:
    data = {"batches": {"213": {"total_alkalinity_umol_kg": 2203.56}}}
    if version:
        data.update(OK_VERSION)
    return _write(tmp_path, data, name="crm.yaml")


def test_crm_values_are_loaded_and_version_checked(tmp_path) -> None:
    result = sc.load_stage_config("qc")
    values = result.load_crm_values(_crm_file(tmp_path, version=False))
    assert values["213"] == pytest.approx(2203.56)
    assert result.crm_certified_values == values
    assert result.crm_values_source == str((tmp_path / "crm.yaml").resolve())
    assert len(result.warnings) == 1 and "crm.yaml" in result.warnings[0]

    bad = _write(tmp_path, {"compatible_pipeline_version": "<1", "batches": {}}, name="bad.yaml")
    with pytest.raises(SystemExit, match="invalid compatible_pipeline_version"):
        sc.load_stage_config("qc").load_crm_values(bad)


def test_crm_values_belong_to_stage_qc(tmp_path) -> None:
    with pytest.raises(ValueError, match="Stage QC"):
        sc.load_stage_config("stage4").load_crm_values(_crm_file(tmp_path, version=True))


# =============================================================================
# Checked-in configs and the Alka config writer
# =============================================================================


@pytest.mark.parametrize(
    ("stage", "name"), [("qc", "02_ta_ph_qc.yaml"), ("stage3", "07_stage3.yaml"), ("stage4", "08_stage4.yaml")]
)
def test_checked_in_configs_load_cleanly(stage, name) -> None:
    result = sc.load_stage_config(stage, REPO_ROOT / "configs" / name)
    assert result.warnings == []


def test_checked_in_crm_values_load_cleanly() -> None:
    result = sc.load_stage_config("qc")
    result.load_crm_values(REPO_ROOT / "configs" / "crm_certified_values.yaml")
    assert result.warnings == []


def test_config_writer_keeps_version_and_other_keys(tmp_path) -> None:
    path = tmp_path / "configs" / "08_stage4.yaml"
    path.parent.mkdir()
    path.write_text(
        yaml.safe_dump(
            {
                "compatible_pipeline_version": ">=2026.11.0",
                "range_policy": {"ph_min": 6.5},
                "carbonate_calc": {"enabled": False, "opt_k_carbonic": 10},
            }
        ),
        encoding="utf-8",
    )

    result = write_stage_configs(tmp_path, compute_carbonate_internally=True)
    assert result.written == [path]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["compatible_pipeline_version"] == ">=2026.11.0"
    assert data["range_policy"] == {"ph_min": 6.5}
    assert data["carbonate_calc"]["enabled"] is True
    assert data["carbonate_calc"]["opt_k_carbonic"] == 10
    assert sc.load_stage_config("stage4", path).warnings == []

    # Same content again: nothing is rewritten.
    assert write_stage_configs(tmp_path, compute_carbonate_internally=True).written == []


def test_config_writer_new_file_has_a_version_and_passes_the_loader(tmp_path) -> None:
    write_stage_configs(tmp_path, compute_carbonate_internally=True)
    path = tmp_path / "configs" / "08_stage4.yaml"
    result = sc.load_stage_config("stage4", path)
    assert result.warnings == []
    assert result.config["carbonate_calc"]["enabled"] is True


def test_config_writer_leaves_the_checked_in_file_untouched() -> None:
    path = REPO_ROOT / "configs" / "08_stage4.yaml"
    before = path.read_text(encoding="utf-8")
    result = write_stage_configs(REPO_ROOT, compute_carbonate_internally=True)
    assert result.written == []
    assert path.read_text(encoding="utf-8") == before


def test_config_writer_refuses_to_overwrite_an_invalid_file(tmp_path) -> None:
    path = tmp_path / "configs" / "08_stage4.yaml"
    path.parent.mkdir()
    path.write_text("compatible_pipeline_version: '>=0.2.0'\nnot_a_key: 1\n", encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="unknown key"):
        write_stage_configs(tmp_path, compute_carbonate_internally=True)
    assert path.read_text(encoding="utf-8") == before
