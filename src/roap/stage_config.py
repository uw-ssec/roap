"""Stage config: one precedence rule for every Stage (#41).

``load_stage_config(stage, path)`` is the only place a Stage's config is
resolved. The rule is the same for every Stage: the Stage's built-in defaults,
deep-merged with that Stage's optional YAML/JSON file, and nothing else. No
Stage merges in another Stage's defaults, so the Stage 1 Range policy can no
longer leak into Stage 4.

The loader also owns the ``compatible_pipeline_version`` check (missing is a
warning, an unsupported operator or an unmet requirement is an error), rejects
unknown keys, and builds the Stage's ``RangePolicy`` from that Stage's own
defaults plus an explicit ``range_policy`` block in that Stage's file only.

Stage QC (notebook 02) keeps its settings under a ``parameters:`` block whose
keys are the notebook's parameter names; its CRM Certified values are loaded
and version-checked here too.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .common import check_config_compatibility, deep_update
from .policy import STAGE1_RANGE_DEFAULTS, STAGE4_RANGE_DEFAULTS, RangePolicy

__all__ = [
    "QC_PARAMETERS",
    "STAGES",
    "StageConfig",
    "load_stage_config",
    "stage_defaults",
]

VERSION_KEY = "compatible_pipeline_version"

# Notebook 02's parameter names a Stage QC config may set under `parameters:`.
# Kept in step with the notebook's parameters cell by a test.
QC_PARAMETERS = frozenset(
    {
        "XLSX_PATH", "OUT_DIR", "SHEET", "PREVIEW_ROWS", "HTML_MAX_ROWS", "OPEN_HTML",
        "WRITE_DERIVED_CSV", "WRITE_HTML_TABLE", "WRITE_PLOTS", "TA_COL", "PH_COL",
        "PH_TEMP_COL", "SAMPLE_TAG_COL", "ROW_ROLE_PREFIXES", "CRM_CORRECT_TA",
        "CRM_BATCH", "CRM_VALUES_CONFIG", "CRM_TA_OVERRIDE", "NO_REQUIRE_TA_FOR_CRM",
        "GROUP_BY", "MIN_CRM_N", "TA_MAD_K", "TA_MAX_ABS_DIFF", "CORRECT_CRM_TOO",
        "TA_NO_ADJUST", "TA_REJECT", "TA_PLOT_TITLE", "TA_PLOT_NO_LABELS", "PHSTD_QC",
        "PH_BUFFER", "PHSTD_CORRECT_SAMPLES", "MIN_PHSTD_N", "PH_MAD_K",
        "PH_MAX_ABS_DIFF", "PH_OK", "PH_WARN", "PH_PLOT_TITLE", "PH_PLOT_NO_LABELS",
    }
)

# Parameters removed by #40, rejected with a pointer to the replacement.
REMOVED_QC_PARAMETERS = {
    "CRM_TAG_PREFIX": "set ROW_ROLE_PREFIXES: {CRM: <prefix>} instead.",
    "PHSTD_TAG_PREFIX": "set ROW_ROLE_PREFIXES: {STANDARD: <prefix>} instead.",
    "ALLOW_CRM_FLAG_COL": "the Tag prefix is the only CRM signal; remove it.",
    "CRM_OR_SAMPLE_COL": "the Tag prefix is the only row-role signal; remove it.",
}

STAGES = ("qc", "stage1a", "stage1b", "stage2", "stage3", "stage4")

# Range policy defaults per Stage; Stages without one have no range checks.
_RANGE_DEFAULTS: Dict[str, Optional[Mapping[str, float]]] = {
    "qc": None,
    "stage1a": STAGE1_RANGE_DEFAULTS,
    "stage1b": STAGE1_RANGE_DEFAULTS,
    "stage2": None,
    "stage3": None,
    "stage4": STAGE4_RANGE_DEFAULTS,
}


# Keys a Stage reads that have no built-in default, so they are valid in that
# Stage's file even though stage_defaults() does not list them.
_OPTIONAL_KEYS: Dict[str, frozenset] = {
    "qc": frozenset(),
    "stage1a": frozenset(),
    "stage1b": frozenset(),
    "stage2": frozenset({"required_stage2_input_columns", "required_stage1b_columns"}),
    "stage3": frozenset(),
    "stage4": frozenset({"carbonate_calc"}),
}


def stage_defaults(stage: str) -> Dict[str, Any]:
    """A fresh copy of one Stage's built-in config defaults."""
    stage = _check_stage(stage)
    # Imported here: the stage modules are heavy and some import this module's
    # neighbours, so a module-level import would load every Stage up front.
    if stage == "qc":
        return {"parameters": {}}
    if stage == "stage1a":
        from .schema import DEFAULT_CONFIG

        return deepcopy(DEFAULT_CONFIG)
    if stage == "stage1b":
        from .schema import DEFAULT_CONFIG
        from .stage1b import STAGE1B_DEFAULTS

        return deep_update(deepcopy(DEFAULT_CONFIG), STAGE1B_DEFAULTS)
    if stage == "stage2":
        from .stage2 import STAGE2_DEFAULTS

        return deepcopy(STAGE2_DEFAULTS)
    if stage == "stage3":
        from .stage3 import STAGE3_DEFAULTS

        return deepcopy(STAGE3_DEFAULTS)
    from .stage4 import STAGE4_DEFAULTS

    return deepcopy(STAGE4_DEFAULTS)


@dataclass
class StageConfig:
    """A Stage's resolved config and where it came from."""

    stage: str
    config: Dict[str, Any]
    range_policy: Optional[RangePolicy]
    source: Optional[str]
    warnings: List[str] = field(default_factory=list)
    crm_certified_values: Optional[Dict[str, float]] = None
    crm_values_source: Optional[str] = None

    def load_crm_values(self, path: str | Path) -> Dict[str, float]:
        """Load Stage QC's CRM Certified values file, with the version check.

        A missing ``compatible_pipeline_version`` in the file is recorded in
        ``warnings``, as for the Stage's own config file.
        """
        if self.stage != "qc":
            raise ValueError(f"CRM Certified values belong to Stage QC, not {self.stage}.")
        from .qc_ta_ph import load_crm_certified_values

        source = str(Path(path).expanduser().resolve())
        if Path(source).exists():  # a missing file is reported by the loader
            _check_version(_read_mapping(Path(source)), source, self.warnings)
        self.crm_certified_values = load_crm_certified_values(source)
        self.crm_values_source = source
        return self.crm_certified_values


def load_stage_config(
    stage: str,
    path: Optional[str | Path] = None,
) -> StageConfig:
    """Resolve one Stage's config: built-in defaults <- the Stage's own file.

    ``path`` may be None or a None-like string ("", "None", "null") for no
    file. Stage QC's CRM Certified values are loaded with
    ``StageConfig.load_crm_values`` once the notebook has resolved their path.

    Raises ``SystemExit`` with a message naming the file for an
    unreadable file, an unknown key, or a failed version check.
    """
    stage = _check_stage(stage)
    defaults = stage_defaults(stage)
    source = _optional_path(path)
    warnings: List[str] = []

    user: Dict[str, Any] = {}
    if source is not None:
        user = _read_mapping(Path(source))
        _check_version(user, source, warnings)
        _check_keys(stage, user, defaults, source)

    config = deep_update(defaults, user)

    range_policy = None
    if _RANGE_DEFAULTS[stage] is not None:
        overrides = user.get("range_policy") or {}
        if not isinstance(overrides, Mapping):
            _fail(f"{source}: range_policy must be a mapping, got {type(overrides).__name__}.")
        try:
            range_policy = RangePolicy.from_mapping({**_RANGE_DEFAULTS[stage], **overrides})
        except (TypeError, ValueError) as exc:
            _fail(f"{source}: invalid range_policy: {exc}")

    return StageConfig(
        stage=stage, config=config, range_policy=range_policy, source=source, warnings=warnings
    )


# =============================================================================
# Helpers
# =============================================================================


def _fail(message: str) -> None:
    """Stop with ``message`` on the exception, so callers and tests can read it."""
    raise SystemExit(f"ERROR: {message}")


def _check_stage(stage: str) -> str:
    key = str(stage).strip().lower()
    if key not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}; expected one of {list(STAGES)}.")
    return key


def _optional_path(value: Optional[str | Path]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "none", "null"}:
        return None
    return str(Path(text).expanduser().resolve())


def _read_mapping(path: Path) -> Dict[str, Any]:
    if not path.exists():
        _fail(f"Config file not found: {path}")
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
        if suffix == ".json":
            loaded = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            import yaml

            loaded = yaml.safe_load(text)
        else:
            _fail(f"Unsupported config format {path.suffix!r}: {path}. Use .yaml, .yml or .json.")
    except SystemExit:
        raise
    except Exception as exc:
        _fail(f"Could not read config file {path}: {exc}")
    if loaded is None:
        return {}
    if not isinstance(loaded, Mapping):
        _fail(f"Config file must contain a mapping at the top level: {path}")
    return dict(loaded)


def _check_version(config: Mapping[str, Any], source: str, warnings: List[str]) -> None:
    if not config.get(VERSION_KEY):
        warnings.append(
            f"{source} has no {VERSION_KEY}; it was not checked against this pipeline version."
        )
        return
    check_config_compatibility(dict(config), source)


def _check_keys(
    stage: str, user: Mapping[str, Any], defaults: Mapping[str, Any], source: str
) -> None:
    allowed = set(defaults) | _OPTIONAL_KEYS[stage] | {VERSION_KEY}
    if _RANGE_DEFAULTS[stage] is not None:
        allowed.add("range_policy")
    unknown = sorted(set(user) - allowed)
    if unknown:
        _fail(
            f"{source}: unknown key(s) {unknown} for {stage}. "
            f"Allowed keys: {sorted(allowed)}."
        )

    if stage != "qc":
        return
    params = user.get("parameters") or {}
    if not isinstance(params, Mapping):
        _fail(f"{source}: 'parameters' must be a mapping, got {type(params).__name__}.")
    for key in params:
        if key in REMOVED_QC_PARAMETERS:
            _fail(f"{source}: parameter {key} was removed: {REMOVED_QC_PARAMETERS[key]}")
    unknown = sorted(set(params) - QC_PARAMETERS)
    if unknown:
        _fail(
            f"{source}: unknown parameter(s) {unknown} under 'parameters'. "
            f"Allowed: {sorted(QC_PARAMETERS)}."
        )
