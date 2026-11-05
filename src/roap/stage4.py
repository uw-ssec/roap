"""
stage4.py
=========
Stage 4 logic for the OA pipeline.

Stage 4 is the analyst facing decision layer. Earlier stages create flags,
summary tables, and diagnostics. Stage 4 assigns a per row verdict:

    PASS
    REVIEW
    FAIL

and attaches explicit reason codes in analysis_audit_reason_codes.

Import as:

    from roap.stage4 import ...
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from . import row_roles
from .common import (
    empty_float_series,
    empty_string_series,
    first_existing,
    md_table_from_df,
    normalize_columns,
    safe_str_series,
    utc_stamp,
)
from .schema import DEFAULT_CONFIG, normalize_carbonate_unit, normalize_ph_scale
from .stage_result import StageResult, json_text, package_versions

if TYPE_CHECKING:
    from .stage_config import StageConfig

__all__ = [
    "NOTEBOOK",
    "STAGE4_DEFAULTS",
    "DicSpeciesAudit",
    "coerce_and_standardize",
    "missing_key_rows",
    "missing_analysis_rows",
    "detect_duplicates",
    "run_range_checks",
    "add_range_flag_count",
    "dic_species_audit",
    "add_readiness_status",
    "reason_count_table",
    "run",
]

NOTEBOOK = "08_stage4"


# =============================================================================
# Defaults
# =============================================================================

_SCHEMA_ALIASES: Dict[str, List[str]] = {
    key: list(value)
    for key, value in DEFAULT_CONFIG.get("canonical_candidates", {}).items()
}


STAGE4_DEFAULTS: Dict[str, Any] = {
    "canonical_aliases": {
        **_SCHEMA_ALIASES,
        "sample_date": ["sample_date", "sample_date_dt", "date", "Date", "datetime"],
        "sample_month": ["sample_month", "month"],
        "sample_day": ["sample_day"],
        "depth_round_m": ["depth_round_m"],
        "depth_bin_m": ["depth_bin_m"],
        "ta_best_umolkg": [
            "ta_best_umolkg",
            "ta_corrected_umolkg",
            "ta_corrected",
            "ta_umol_kg",
            "ta_umolkg",
            "ta_best",
            "ta",
            "TA",
        ],
        "ph_best": [
            "ph_best",
            "ph_corrected_from_phstd",
            "pH_corrected_from_std",
            "ph_observed",
            "pH_best",
            "pH_lab",
            "ph_lab",
            "pH",
            "ph",
        ],
        "ph_co2sys": [
            "ph_co2sys",
            "ph_calculated",
            "pH_co2sys",
            "pH_calc",
            "ph_calc",
        ],
        "pco2_best_uatm": [
            "pco2_best_uatm",
            "pco2_calc_uatm",
            "pco2_uatm",
            "pCO2",
            "pco2",
        ],
        "dic_best_umol_kg": [
            "dic_best_umol_kg",
            "dic_calculated_umol_kg",
            "dic_measured_umol_kg",
            "dic_umol_kg",
            "dic_umolkg",
            "dic_calc",
            "DIC",
            "dic",
        ],
        "co2aq_calc_umol_kg": [
            "co2aq_calc_umol_kg",
            "co2aq_umol_kg",
            "co2aq_umolkg",
            "co2_aq_umol_kg",
            "aqueous_co2_umol_kg",
        ],
        "hco3_calc_umol_kg": [
            "hco3_calc_umol_kg",
            "hco3_umol_kg",
            "hco3_umolkg",
            "bicarbonate_umol_kg",
        ],
        "co3_calc_umol_kg": [
            "co3_calc_umol_kg",
            "co3_umol_kg",
            "co3_umolkg",
            "carbonate_umol_kg",
        ],
        "omega_aragonite_calc": [
            "omega_aragonite_calc",
            "omega_ar",
            "omega_arag",
            "OmegaArag",
        ],
        "omega_calcite_calc": [
            "omega_calcite_calc",
            "omega_ca",
            "omega_calc",
            "OmegaCalc",
        ],
        "ph_scale_observed_normalized": [
            "ph_scale_observed_normalized",
            "ph_best_scale",
            "ph_scale_observed",
            "pH_scale_observed",
            "ph_scale",
        ],
        "ph_scale_calculated_normalized": [
            "ph_scale_calculated_normalized",
            "ph_co2sys_scale",
            "ph_scale_calculated",
            "ph_scale_calc",
            "pH_scale_calc",
            "ph_calc_scale",
        ],
        "dic_unit_normalized": ["dic_unit_normalized", "dic_unit", "DIC_unit"],
        "co2aq_unit_normalized": [
            "co2aq_unit_normalized",
            "co2aq_unit",
            "CO2aq_unit",
            "co2_unit",
            "CO2_unit",
        ],
        "hco3_unit_normalized": ["hco3_unit_normalized", "hco3_unit", "HCO3_unit"],
        "co3_unit_normalized": ["co3_unit_normalized", "co3_unit", "CO3_unit"],
        "carbonate_solver": ["carbonate_solver"],
        "carbon_input_pair_used": ["carbon_input_pair_used"],
        "ta_best_source": ["ta_best_source"],
        "ph_best_source": ["ph_best_source"],
        "ph_co2sys_source": ["ph_co2sys_source"],
        "pco2_best_source": ["pco2_best_source"],
        "dic_best_source": ["dic_best_source"],
        "flag_dic_unit_missing": ["flag_dic_unit_missing"],
        "flag_dic_inconsistent": ["flag_dic_inconsistent"],
        "flag_dic_inconsistent_robust": ["flag_dic_inconsistent_robust"],
        "flag_ph_scale_mismatch": ["flag_ph_scale_mismatch"],
        "flag_ph_best_scale_unexpected": ["flag_ph_best_scale_unexpected"],
        "flag_ph_co2sys_scale_unexpected": ["flag_ph_co2sys_scale_unexpected"],
        "flag_ph_diag_mismatch": ["flag_ph_diag_mismatch"],
        "flag_ph_diag_mismatch_strict": ["flag_ph_diag_mismatch_strict"],
        "flag_ph_diag_mismatch_robust": ["flag_ph_diag_mismatch_robust"],
        "flag_any_carbonate_issue": ["flag_any_carbonate_issue"],
        "flag_any_carbonate_issue_strict": ["flag_any_carbonate_issue_strict"],
        "flag_stage2_replicate_conflict_carried": ["flag_stage2_replicate_conflict_carried"],
        "flag_solver_unknown": ["flag_solver_unknown"],
        "flag_carbon_input_pair_unknown": ["flag_carbon_input_pair_unknown"],
        "flag_any_stage3_review_issue": ["flag_any_stage3_review_issue"],
    },
    "required_stage4_key_columns": [
        "sample_id",
        "sample_date",
        "station_id",
        "depth_round_m",
    ],
    "required_stage4_analysis_columns": [
        "ta_best_umolkg",
        "ph_best",
        "salinity",
        "temperature_insitu_c",
    ],
    "required_stage3_columns": [
        "sample_id",
        "sample_date",
        "station_id",
        "depth_round_m",
        "ta_best_umolkg",
        "ph_best",
        "salinity",
        "temperature_insitu_c",
    ],
    "expected_stage4_columns": [
        "record_id",
        "sample_month",
        "sample_day",
        "depth_m",
        "cruise_id",
        "transect_id",
        "replicate_id",
        "pressure_output_dbar",
        "ph_co2sys",
        "dic_best_umol_kg",
        "pco2_best_uatm",
        "co2aq_calc_umol_kg",
        "hco3_calc_umol_kg",
        "co3_calc_umol_kg",
        "omega_aragonite_calc",
        "omega_calcite_calc",
        "ph_scale_observed_normalized",
        "ph_scale_calculated_normalized",
        "carbonate_solver",
        "carbon_input_pair_used",
        "ta_best_source",
        "ph_best_source",
        "ph_co2sys_source",
        "pco2_best_source",
        "dic_best_source",
        "flag_any_carbonate_issue",
        "flag_any_carbonate_issue_strict",
        "flag_stage2_replicate_conflict_carried",
        "flag_solver_unknown",
        "flag_carbon_input_pair_unknown",
        "flag_dic_unit_missing",
        "flag_dic_inconsistent",
        "flag_dic_inconsistent_robust",
        "flag_ph_scale_mismatch",
        "flag_ph_best_scale_unexpected",
        "flag_ph_co2sys_scale_unexpected",
        "flag_ph_diag_mismatch",
        "flag_ph_diag_mismatch_strict",
        "flag_ph_diag_mismatch_robust",
    ],
    "expected_stage3_columns": [
        "record_id",
        "sample_month",
        "sample_day",
        "depth_m",
        "cruise_id",
        "transect_id",
        "replicate_id",
        "pressure_output_dbar",
        "ph_co2sys",
        "dic_best_umol_kg",
        "pco2_best_uatm",
        "co2aq_calc_umol_kg",
        "hco3_calc_umol_kg",
        "co3_calc_umol_kg",
        "omega_aragonite_calc",
        "omega_calcite_calc",
        "ph_scale_observed_normalized",
        "ph_scale_calculated_normalized",
        "carbonate_solver",
        "carbon_input_pair_used",
        "ta_best_source",
        "ph_best_source",
        "ph_co2sys_source",
        "pco2_best_source",
        "dic_best_source",
        "flag_any_carbonate_issue",
        "flag_any_carbonate_issue_strict",
        "flag_stage2_replicate_conflict_carried",
        "flag_solver_unknown",
        "flag_carbon_input_pair_unknown",
        "flag_dic_inconsistent",
        "flag_dic_inconsistent_robust",
        "flag_ph_scale_mismatch",
        "flag_ph_diag_mismatch",
        "flag_ph_diag_mismatch_strict",
        "flag_ph_diag_mismatch_robust",
    ],
    "duplicate_keys": [
        "sample_id",
        "sample_date",
        "station_id",
        "depth_round_m",
        "replicate_id",
    ],
    "range_policy": {
        "sal_min": 0.0,
        "sal_max": 42.0,
        "temp_min": -2.0,
        "temp_max": 40.0,
        "ph_min": 6.0,
        "ph_max": 9.5,
        "ta_min": 0.0,
        "ta_max": 3500.0,
        "dic_min": 0.0,
        "dic_max": 3500.0,
        "pco2_min": 0.0,
        "pco2_max": 10000.0,
        # FIX 3-B (scientific, downstream): Stage 4 now carries separate omega
        # limits for aragonite and calcite consistent with policy.py changes.
        # Legacy omega_min/max retained for RangePolicy backwards compatibility.
        "omega_min": 0.0,
        "omega_max": 20.0,
        "omega_ar_min": 0.0,
        "omega_ar_max": 20.0,
        "omega_ca_min": 0.0,
        "omega_ca_max": 20.0,
    },
    "dic_species_audit": {
        "enabled": True,
        "abs_tol_umolkg": 5.0,
        "rel_tol": 0.01,
        "require_matching_units": True,
    },
    "strict_dic_candidates": {
        "dic": [
            "dic_best_umol_kg",
            "dic_calculated_umol_kg",
            "dic_measured_umol_kg",
            "dic_umol_kg",
            "dic_umolkg",
            "dic_calc",
            "DIC",
            "dic",
        ],
        "co2aq": [
            "co2aq_calc_umol_kg",
            "co2aq_umol_kg",
            "co2aq_umolkg",
            "co2_aq_umol_kg",
            "aqueous_co2_umol_kg",
        ],
        "hco3": [
            "hco3_calc_umol_kg",
            "hco3_umol_kg",
            "hco3_umolkg",
            "bicarbonate_umol_kg",
        ],
        "co3": [
            "co3_calc_umol_kg",
            "co3_umol_kg",
            "co3_umolkg",
            "carbonate_umol_kg",
        ],
        "dic_unit": ["dic_unit_normalized", "dic_unit", "DIC_unit"],
        "co2aq_unit": ["co2aq_unit_normalized", "co2aq_unit", "CO2aq_unit", "co2_unit", "CO2_unit"],
        "hco3_unit": ["hco3_unit_normalized", "hco3_unit", "HCO3_unit"],
        "co3_unit": ["co3_unit_normalized", "co3_unit", "CO3_unit"],
    },
    "unit_equivalents": [
        "umol kg-1",
        "umol/kg",
        "UMOL/KG",
        "UMOLKG",
        "UMOLKG-1",
        "UMOLKG^-1",
        "UMOL/KG-1",
        "MICROMOL/KG",
        "MICROMOLKG",
        "µmol kg−1",
        "µmol/kg",
    ],
}


_ID_COLS: List[str] = [
    "record_id",
    "sample_id",
    "cruise_id",
    "transect_id",
    "station_id",
    "replicate_id",
    "depth_round_m",
    "sample_date",
    "sample_month",
]

_NUMERIC_COLS = [
    "depth_m",
    "depth_round_m",
    "depth_bin_m",
    "latitude_deg",
    "longitude_deg",
    "salinity",
    "temperature_measurement_c",
    "temperature_insitu_c",
    "pressure_measurement_dbar",
    "pressure_output_dbar",
    "ta_best_umolkg",
    "ph_best",
    "ph_co2sys",
    "pco2_best_uatm",
    "dic_best_umol_kg",
    "co2aq_calc_umol_kg",
    "hco3_calc_umol_kg",
    "co3_calc_umol_kg",
    "omega_aragonite_calc",
    "omega_calcite_calc",
]

_STRING_COLS = [
    "record_id",
    "sample_id",
    "cruise_id",
    "transect_id",
    "station_id",
    "replicate_id",
    "carbonate_solver",
    "carbon_input_pair_used",
    "ta_best_source",
    "ph_best_source",
    "ph_co2sys_source",
    "pco2_best_source",
    "dic_best_source",
]

_INHERITED_BOOL_COLS = [
    "flag_dic_unit_missing",
    "flag_dic_inconsistent",
    "flag_dic_inconsistent_robust",
    "flag_ph_scale_mismatch",
    "flag_ph_best_scale_unexpected",
    "flag_ph_co2sys_scale_unexpected",
    "flag_ph_diag_mismatch",
    "flag_ph_diag_mismatch_strict",
    "flag_ph_diag_mismatch_robust",
    "flag_any_carbonate_issue",
    "flag_any_carbonate_issue_strict",
    "flag_stage2_replicate_conflict_carried",
    "flag_solver_unknown",
    "flag_carbon_input_pair_unknown",
    "flag_any_stage3_review_issue",
    "flag_dic_species_nonpositive_dic_audit",
    "flag_dic_species_negative_co2aq_audit",
    "flag_dic_species_negative_hco3_audit",
    "flag_dic_species_negative_co3_audit",
]

_CALCULATED_CARBONATE_COLS = [
    "ph_co2sys",
    "pco2_best_uatm",
    "dic_best_umol_kg",
    "co2aq_calc_umol_kg",
    "hco3_calc_umol_kg",
    "co3_calc_umol_kg",
    "omega_aragonite_calc",
    "omega_calcite_calc",
]


# =============================================================================
# Small helpers
# =============================================================================


def _as_bool(value: Any) -> bool:
    """Convert common config boolean spellings to bool.

    Unknown strings raise a ValueError instead of being treated as truthy. This
    prevents typos such as "maybe" from silently enabling an audit option.
    """
    if isinstance(value, bool):
        return value

    if value is None or pd.isna(value):
        return False

    text = str(value).strip().lower()

    if text in {"true", "t", "yes", "y", "1", "on"}:
        return True

    if text in {"false", "f", "no", "n", "0", "off", "", "none", "null", "<na>", "nan"}:
        return False

    raise ValueError(f"Cannot parse boolean value: {value!r}")


def _has_value(series: pd.Series) -> pd.Series:
    """Return True where a Series has a non missing and non blank value.

    FIX 1-A (stage4.py copy): Use text.notna() instead of series.notna() in
    the string branch — consistent with the fix applied to common.has_value_series.
    """
    if pd.api.types.is_string_dtype(series) or series.dtype == object:
        text = series.astype("string").str.strip()
        return text.notna() & text.ne("")
    return series.notna()


def _bcol(df: pd.DataFrame, name: str) -> pd.Series:
    """Get a boolean column safely. Missing, blank, and unknown values become False."""
    if name not in df.columns:
        return pd.Series(False, index=df.index, dtype="boolean")

    series = df[name]

    if str(series.dtype) == "boolean":
        return series.fillna(False).astype("boolean")

    if series.dtype == bool:
        return pd.Series(series, index=df.index).astype("boolean")

    text = series.astype("string").str.strip().str.upper()
    true_values = {"TRUE", "T", "YES", "Y", "1", "ON"}
    false_values = {"FALSE", "F", "NO", "N", "0", "OFF", ""}

    out = pd.Series(False, index=df.index, dtype="boolean")
    out.loc[text.isin(true_values)] = True
    out.loc[text.isin(false_values) | text.isna()] = False
    return out


def _set_flag_for_existing_index(
    df: pd.DataFrame,
    index_values: pd.Index,
    flag_col: str,
) -> None:
    """Set a boolean audit flag only for index values present in df."""
    idx = pd.Index(index_values).intersection(df.index)

    if len(idx):
        df.loc[idx, flag_col] = True


def _calculated_output_present(df: pd.DataFrame) -> pd.Series:
    """Return True where any calculated carbonate output is present."""
    present = pd.Series(False, index=df.index, dtype=bool)

    for col in _CALCULATED_CARBONATE_COLS:
        if col in df.columns:
            present = present | pd.to_numeric(df[col], errors="coerce").notna()

    return present.astype("boolean")


def _merge_calculated_output_presence(df: pd.DataFrame) -> pd.Series:
    """Combine inherited and computed calculated carbonate output presence."""
    computed = _calculated_output_present(df).fillna(False)

    if "has_calculated_carbonate_output" in df.columns:
        inherited = _bcol(df, "has_calculated_carbonate_output").fillna(False)
        return (inherited | computed).astype("boolean")

    return computed.astype("boolean")


def _normalise_unit_equivalents(values: Sequence[Any]) -> set[str]:
    """Normalise configured unit equivalents through normalize_carbonate_unit."""
    out: set[str] = set()

    for value in values:
        normalised = normalize_carbonate_unit(value)
        if pd.isna(normalised):
            continue
        out.add(str(normalised))

    return out


def _series_missing(series: pd.Series) -> pd.Series:
    """Missing test that treats blank strings as missing."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.isna()
    return (~_has_value(series)).astype(bool)


def _empty_dic_audit_result(df: pd.DataFrame, audit_not_run: bool = False) -> pd.DataFrame:
    """Return an empty shaped DIC audit result with boolean audit flags."""
    return pd.DataFrame(
        {
            "flag_dic_species_audit_not_run": pd.Series(
                audit_not_run,
                index=df.index,
                dtype="boolean",
            ),
            "flag_dic_species_values_missing_audit": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_audit_strict": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_unit_mismatch_audit": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_unit_missing_audit": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_nonpositive_dic_audit": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_negative_co2aq_audit": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_negative_hco3_audit": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_negative_co3_audit": pd.Series(False, index=df.index, dtype="boolean"),
        },
        index=df.index,
    )


# =============================================================================
# Coerce and standardise
# =============================================================================


def coerce_and_standardize(df: pd.DataFrame, notes: List[str]) -> pd.DataFrame:
    """Coerce numerics, parse dates in UTC, and normalise units and scales."""
    out = df.copy()

    if "sample_date" in out.columns:
        out["sample_date"] = pd.to_datetime(out["sample_date"], errors="coerce", utc=True)
        sample_dt = out["sample_date"]

        if getattr(sample_dt.dt, "tz", None) is not None:
            sample_dt_for_period = sample_dt.dt.tz_convert("UTC").dt.tz_localize(None)
        else:
            sample_dt_for_period = sample_dt

        out["year"] = sample_dt_for_period.dt.year.astype("Int64")
        out["sample_month"] = sample_dt_for_period.dt.to_period("M").astype("string")
        out["sample_day"] = sample_dt_for_period.dt.date.astype("string")
        out.loc[out["sample_date"].isna(), "sample_day"] = pd.NA
    else:
        out["sample_date"] = pd.NaT
        out["year"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
        out["sample_month"] = empty_string_series(out.index)
        out["sample_day"] = empty_string_series(out.index)
        notes.append("No sample_date found. year, sample_month, and sample_day set to missing.")

    for col in _NUMERIC_COLS:
        if col in out.columns:
            raw = out[col]
            text = raw.astype("string").str.strip()
            missing = raw.isna() | text.eq("") | text.isna()
            numeric = pd.to_numeric(raw, errors="coerce")
            parse_failed = (~missing & numeric.isna()).astype("boolean")
            out[f"flag_non_numeric__{col}"] = parse_failed
            out[f"raw_non_numeric__{col}"] = raw.where(parse_failed, pd.NA).astype("string")
            out[col] = numeric

    # FIX 8-B: depth_round_m is a required Stage 4 key column but is only
    # created by Stage 2's add_time_and_depth_keys(). If a notebook feeds
    # Stage 1B output directly into Stage 4 (skipping Stage 2), depth_round_m
    # would be absent and missing_key_rows() would mark every row as having a
    # missing key, causing analysis_audit_status = "FAIL" for all rows.
    # This fallback creates depth_round_m from depth_m when it is absent or
    # fully missing, so Stage 4 works correctly whether or not Stage 2 ran.
    if "depth_round_m" not in out.columns or out["depth_round_m"].isna().all():
        if "depth_m" in out.columns:
            notes.append(
                "depth_round_m was absent or all-missing. Created from depth_m "
                "(rounded to 1 decimal). Run Stage 2 for proper depth binning."
            )
            out["depth_round_m"] = pd.to_numeric(out["depth_m"], errors="coerce").round(1)
        else:
            notes.append(
                "depth_round_m and depth_m are both absent. depth_round_m set to missing. "
                "Rows will be flagged as missing_key by missing_key_rows()."
            )
            out["depth_round_m"] = empty_float_series(out.index)

    out["lat"] = (
        pd.to_numeric(out["latitude_deg"], errors="coerce")
        if "latitude_deg" in out.columns
        else empty_float_series(out.index)
    )
    out["lon"] = (
        pd.to_numeric(out["longitude_deg"], errors="coerce")
        if "longitude_deg" in out.columns
        else empty_float_series(out.index)
    )

    for col in _STRING_COLS:
        if col in out.columns:
            out[col] = safe_str_series(out[col]).replace("", pd.NA)

    for col in ["ph_scale_observed_normalized", "ph_scale_calculated_normalized"]:
        if col in out.columns:
            out[col] = out[col].map(normalize_ph_scale).astype("string")
        else:
            out[col] = empty_string_series(out.index)

    for col in [
        "dic_unit_normalized",
        "co2aq_unit_normalized",
        "hco3_unit_normalized",
        "co3_unit_normalized",
    ]:
        if col in out.columns:
            out[col] = out[col].map(normalize_carbonate_unit).astype("string")
        else:
            out[col] = empty_string_series(out.index)

    for col in _INHERITED_BOOL_COLS:
        if col in out.columns:
            out[col] = _bcol(out, col)
        else:
            out[col] = pd.Series(False, index=out.index, dtype="boolean")

    out["has_calculated_carbonate_output"] = _merge_calculated_output_presence(out)

    has_calc = out["has_calculated_carbonate_output"].fillna(False)
    out["flag_solver_unknown"] = (
        has_calc & ~_has_value(out["carbonate_solver"])
        if "carbonate_solver" in out.columns
        else has_calc
    ).astype("boolean")
    out["flag_carbon_input_pair_unknown"] = (
        has_calc & ~_has_value(out["carbon_input_pair_used"])
        if "carbon_input_pair_used" in out.columns
        else has_calc
    ).astype("boolean")

    return out


# =============================================================================
# Key and analysis completeness
# =============================================================================


def missing_key_rows(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    """Return rows where any required key column is missing or absent."""
    flags = pd.DataFrame(index=df.index)

    for key in keys:
        flag_col = f"flag_missing_key__{key}"

        if key not in df.columns:
            flags[flag_col] = pd.Series(True, index=df.index)
            continue

        flags[flag_col] = _series_missing(df[key])

    if flags.empty:
        return pd.DataFrame()

    any_missing = flags.any(axis=1)
    id_cols = [col for col in _ID_COLS if col in df.columns]

    return pd.concat(
        [df.loc[any_missing, id_cols], flags.loc[any_missing]],
        axis=1,
    ).copy()


def missing_analysis_rows(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Return rows where required analysis columns are missing or absent."""
    flags = pd.DataFrame(index=df.index)

    for col in columns:
        flag_col = f"flag_missing_analysis__{col}"

        if col not in df.columns:
            flags[flag_col] = pd.Series(True, index=df.index)
            continue

        flags[flag_col] = _series_missing(df[col])

    if flags.empty:
        return pd.DataFrame()

    any_missing = flags.any(axis=1)
    id_cols = [col for col in _ID_COLS if col in df.columns]

    return pd.concat(
        [df.loc[any_missing, id_cols], flags.loc[any_missing]],
        axis=1,
    ).copy()


def _role_masks(df: pd.DataFrame) -> Optional[Tuple[pd.Series, pd.Series]]:
    """(CRM, Standard) row masks from ``row_role``, or ``None`` without roles.

    Inputs written before row_role existed fall back to the deprecated
    row_classification labels.
    """
    if row_roles.ROW_ROLE_COL in df.columns:
        return row_roles.is_crm(df), row_roles.is_standard(df)
    if "row_classification" in df.columns:
        return (
            df["row_classification"].isin(["CRM", "CRM_QC"]),
            df["row_classification"].isin(["STD", "STD_QC"]),
        )
    return None


def detect_duplicates(
    df: pd.DataFrame,
    keys: List[str],
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Detect duplicate Sample rows when all requested duplicate keys exist.

    Only Samples are compared (#44); CRM and Standard rows are never duplicates.
    An input with no row roles at all compares every row, as before.
    """
    present = [key for key in keys if key in df.columns]
    missing = [key for key in keys if key not in df.columns]
    messages: List[str] = []

    if missing:
        messages.append(f"Required duplicate key columns missing: {missing}")
        return pd.DataFrame(), messages, present

    if not present:
        return pd.DataFrame(), [f"No key columns found among: {keys}"], present

    valid = pd.Series(True, index=df.index)
    masks = _role_masks(df)
    if masks is not None:
        valid &= ~(masks[0] | masks[1])
    for key in present:
        valid &= ~_series_missing(df[key])

    dup_mask = pd.Series(False, index=df.index)
    if valid.any():
        dup_mask.loc[valid] = df.loc[valid].duplicated(subset=present, keep=False)

    messages.append(f"Keys used: {present}")
    return df.loc[dup_mask].copy(), messages, present


# =============================================================================
# Range checks
# =============================================================================


def run_range_checks(
    df: pd.DataFrame,
    policy: Any,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return Stage 4 range summary and long format range flags."""
    checks = [
        (["salinity"], policy.sal_min, policy.sal_max, "salinity"),
        (["temperature_insitu_c", "temperature_measurement_c"], policy.temp_min, policy.temp_max, "temperature"),
        (["ph_best"], policy.ph_min, policy.ph_max, "observed_ph"),
        (["ph_co2sys"], policy.ph_min, policy.ph_max, "co2sys_ph"),
        (["ta_best_umolkg"], policy.ta_min, policy.ta_max, "alkalinity"),
        (["dic_best_umol_kg"], policy.dic_min, policy.dic_max, "dic"),
        (["pco2_best_uatm"], policy.pco2_min, policy.pco2_max, "pco2"),
        # FIX 3-B (scientific, downstream): Use the mineral-specific omega policy
        # fields so aragonite and calcite can have independent plausible ranges.
        # Aragonite saturation state drops below 1 in polar/deep waters before
        # calcite does (Orr et al. 2005, Nature 437:681; Feely et al. 2004,
        # Science 305:362-366). Sharing one field prevented separate thresholds.
        (["omega_aragonite_calc"], policy.omega_ar_min, policy.omega_ar_max, "omega_aragonite"),
        (["omega_calcite_calc"], policy.omega_ca_min, policy.omega_ca_max, "omega_calcite"),
    ]

    id_cols = [col for col in _ID_COLS if col in df.columns]
    summary_rows: List[dict[str, Any]] = []
    flag_rows: List[dict[str, Any]] = []

    for candidates, low, high, logical_name in checks:
        col = first_existing(df, candidates)
        if col is None:
            continue

        raw = df[col]
        text = raw.astype("string").str.strip()
        missing = raw.isna() | text.isna() | text.eq("")
        values = pd.to_numeric(raw, errors="coerce")

        parse_flag_col = f"flag_non_numeric__{col}"
        if parse_flag_col in df.columns:
            non_numeric = _bcol(df, parse_flag_col)
        else:
            non_numeric = (~missing & values.isna()).astype("boolean")

        below = values.notna() & (values < float(low))
        above = values.notna() & (values > float(high))

        n_missing = int(missing.sum())
        n_non_numeric = int(non_numeric.fillna(False).sum())
        n_below = int(below.sum())
        n_above = int(above.sum())

        summary_rows.append(
            {
                "logical_variable": logical_name,
                "column_used": col,
                "min_allowed": float(low),
                "max_allowed": float(high),
                "n": len(df),
                "n_valid": int(values.notna().sum()),
                "n_missing": n_missing,
                "n_non_numeric": n_non_numeric,
                "n_below_min": n_below,
                "n_above_max": n_above,
                "n_flagged": n_non_numeric + n_below + n_above,
            }
        )

        tests = [
            ("non_numeric", non_numeric.fillna(False)),
            ("below_min", below),
            ("above_max", above),
        ]

        raw_non_numeric_col = f"raw_non_numeric__{col}"

        for flag_name, mask in tests:
            for idx in df.index[mask]:
                row: dict[str, Any] = {
                    "row_index": idx,
                    "logical_variable": logical_name,
                    "column_used": col,
                    "value": values.loc[idx] if pd.notna(values.loc[idx]) else pd.NA,
                    "raw_value": (
                        df.loc[idx, raw_non_numeric_col]
                        if raw_non_numeric_col in df.columns and flag_name == "non_numeric"
                        else df.loc[idx, col]
                    ),
                    "flag": flag_name,
                }
                for id_col in id_cols:
                    row[id_col] = df.loc[idx, id_col]
                flag_rows.append(row)

    return pd.DataFrame(summary_rows), pd.DataFrame(flag_rows)


def add_range_flag_count(df: pd.DataFrame, range_flags: pd.DataFrame) -> pd.DataFrame:
    """Attach the number of Stage 4 range flags per row."""
    out = df.copy()

    if range_flags.empty or "row_index" not in range_flags.columns:
        out["range_flag_count"] = pd.Series(0, index=out.index, dtype="Int64")
        return out

    counts = range_flags["row_index"].value_counts()
    out["range_flag_count"] = (
        pd.Series(out.index, index=out.index)
        .map(counts)
        .fillna(0)
        .astype("Int64")
    )

    return out


# =============================================================================
# Strict DIC species audit
# =============================================================================


@dataclass
class DicSpeciesAudit:
    """Configuration for the strict DIC versus species audit."""

    enabled: bool = True
    abs_tol_umolkg: float = 5.0
    rel_tol: float = 0.01
    require_matching_units: bool = True

    def __post_init__(self) -> None:
        self.enabled = _as_bool(self.enabled)
        self.require_matching_units = _as_bool(self.require_matching_units)

        self.abs_tol_umolkg = float(self.abs_tol_umolkg)
        self.rel_tol = float(self.rel_tol)

        if not math.isfinite(self.abs_tol_umolkg):
            raise ValueError(
                "DicSpeciesAudit.abs_tol_umolkg must be finite, "
                f"got {self.abs_tol_umolkg!r}."
            )

        if not math.isfinite(self.rel_tol):
            raise ValueError(
                "DicSpeciesAudit.rel_tol must be finite, "
                f"got {self.rel_tol!r}."
            )

        if self.abs_tol_umolkg < 0:
            raise ValueError("DicSpeciesAudit.abs_tol_umolkg must be non negative.")

        if self.rel_tol < 0:
            raise ValueError("DicSpeciesAudit.rel_tol must be non negative.")

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "DicSpeciesAudit":
        """Build a strict DIC audit config from a Stage 4 config dictionary."""
        raw = dict(config.get("dic_species_audit", {}))
        valid = set(cls.__dataclass_fields__.keys())
        unknown = sorted(set(raw) - valid)

        if unknown:
            raise ValueError("Unknown dic_species_audit keys: " + ", ".join(unknown))

        return cls(**raw)


def dic_species_audit(
    df: pd.DataFrame,
    check: DicSpeciesAudit,
    candidates: Dict[str, List[str]],
    unit_equivalents: set,
) -> Tuple[pd.DataFrame, str, Dict[str, Optional[str]]]:
    """Run the strict DIC species sum audit."""
    if not check.enabled:
        return (
            _empty_dic_audit_result(df, audit_not_run=False),
            "Strict DIC species audit disabled by config.",
            {},
        )

    dic_col = first_existing(df, candidates.get("dic", []))
    co2_col = first_existing(df, candidates.get("co2aq", []))
    hco3_col = first_existing(df, candidates.get("hco3", []))
    co3_col = first_existing(df, candidates.get("co3", []))
    dic_unit_col = first_existing(df, candidates.get("dic_unit", []))
    co2_unit_col = first_existing(df, candidates.get("co2aq_unit", []))
    hco3_unit_col = first_existing(df, candidates.get("hco3_unit", []))
    co3_unit_col = first_existing(df, candidates.get("co3_unit", []))

    colmeta: Dict[str, Optional[str]] = {
        "dic_col": dic_col,
        "co2aq_col": co2_col,
        "hco3_col": hco3_col,
        "co3_col": co3_col,
        "dic_unit_col": dic_unit_col,
        "co2aq_unit_col": co2_unit_col,
        "hco3_unit_col": hco3_unit_col,
        "co3_unit_col": co3_unit_col,
    }

    if not all([dic_col, co2_col, hco3_col, co3_col]):
        return (
            _empty_dic_audit_result(df, audit_not_run=True),
            "Skipped: one or more required DIC species columns missing.",
            colmeta,
        )

    dic = pd.to_numeric(df[dic_col], errors="coerce")
    co2 = pd.to_numeric(df[co2_col], errors="coerce")
    hco3 = pd.to_numeric(df[hco3_col], errors="coerce")
    co3 = pd.to_numeric(df[co3_col], errors="coerce")

    vals_ok = dic.notna() & co2.notna() & hco3.notna() & co3.notna()

    any_species_evidence = dic.notna() | co2.notna() | hco3.notna() | co3.notna()
    values_missing = any_species_evidence & ~vals_ok

    dic_nonpositive = dic.notna() & (dic <= 0)
    co2_negative = co2.notna() & (co2 < 0)
    hco3_negative = hco3.notna() & (hco3 < 0)
    co3_negative = co3.notna() & (co3 < 0)

    negative_species = (
        dic_nonpositive
        | co2_negative
        | hco3_negative
        | co3_negative
    )

    unit_missing = pd.Series(False, index=df.index, dtype="boolean")
    unit_mismatch = pd.Series(False, index=df.index, dtype="boolean")

    unit_equivalents_norm = _normalise_unit_equivalents(list(unit_equivalents))

    if check.require_matching_units and all([dic_unit_col, co2_unit_col, hco3_unit_col, co3_unit_col]):
        dic_unit = df[dic_unit_col].map(normalize_carbonate_unit).astype("string")
        co2_unit = df[co2_unit_col].map(normalize_carbonate_unit).astype("string")
        hco3_unit = df[hco3_unit_col].map(normalize_carbonate_unit).astype("string")
        co3_unit = df[co3_unit_col].map(normalize_carbonate_unit).astype("string")

        known = _has_value(dic_unit) & _has_value(co2_unit) & _has_value(hco3_unit) & _has_value(co3_unit)
        allowed = (
            dic_unit.isin(unit_equivalents_norm)
            & co2_unit.isin(unit_equivalents_norm)
            & hco3_unit.isin(unit_equivalents_norm)
            & co3_unit.isin(unit_equivalents_norm)
        )
        same = (dic_unit == co2_unit) & (dic_unit == hco3_unit) & (dic_unit == co3_unit)

        unit_missing = (vals_ok & ~known).astype("boolean")
        unit_mismatch = (vals_ok & known & (~same | ~allowed)).astype("boolean")
    elif check.require_matching_units:
        unit_missing = vals_ok.astype("boolean")

    checkable = vals_ok & ~unit_missing.fillna(False) & ~unit_mismatch.fillna(False)
    species_sum = co2 + hco3 + co3
    diff = dic - species_sum
    # FIX 8-C (scientific): Apply both lower and upper clips to the tolerance
    # formula. Without an upper clip, a DIC value of 3000 µmol/kg at 1%
    # relative tolerance allows a 30 µmol/kg species sum discrepancy, which is
    # far outside what CO2SYS should produce for internally consistent data
    # (Lewis & Wallace 1998; Orr et al. 2015 SOCAT protocols).
    # Upper clip = 10 × abs_tol_umolkg (configurable via abs_tol_umolkg in
    # dic_species_audit config block). This keeps the tolerance physically
    # meaningful across the full oceanic DIC range.
    _dic_tol_upper = check.abs_tol_umolkg * 10.0
    tol = (dic.abs() * check.rel_tol).clip(
        lower=check.abs_tol_umolkg,
        upper=_dic_tol_upper,
    )
    strict_fail = (
        negative_species
        | (checkable & (diff.abs() > tol))
    ).astype("boolean")

    result = pd.DataFrame(
        {
            "dic_best_umol_kg": dic,
            "co2aq_calc_umol_kg": co2,
            "hco3_calc_umol_kg": hco3,
            "co3_calc_umol_kg": co3,
            "dic_species_sum": species_sum,
            "dic_minus_sum": diff,
            "dic_sum_tol": tol,
            "flag_dic_species_audit_not_run": pd.Series(False, index=df.index, dtype="boolean"),
            "flag_dic_species_values_missing_audit": values_missing.astype("boolean"),
            "flag_dic_species_audit_strict": strict_fail,
            "flag_dic_species_unit_mismatch_audit": unit_mismatch,
            "flag_dic_species_unit_missing_audit": unit_missing,
            "flag_dic_species_nonpositive_dic_audit": dic_nonpositive.astype("boolean"),
            "flag_dic_species_negative_co2aq_audit": co2_negative.astype("boolean"),
            "flag_dic_species_negative_hco3_audit": hco3_negative.astype("boolean"),
            "flag_dic_species_negative_co3_audit": co3_negative.astype("boolean"),
        },
        index=df.index,
    )

    note = (
        f"Ran strict DIC vs species audit: abs_tol={check.abs_tol_umolkg} umol/kg, "
        f"rel_tol={check.rel_tol * 100:.1f}%."
    )
    return result, note, colmeta


# =============================================================================
# Readiness classification
# =============================================================================


def add_readiness_status(
    df: pd.DataFrame,
    dup_table: pd.DataFrame,
    missing_key_idx: pd.Index,
    required_analysis_missing_idx: Optional[pd.Index] = None,
) -> pd.DataFrame:
    """Assign PASS, REVIEW, or FAIL and attach reason codes per row."""
    out = df.copy()

    out["flag_audit_missing_key"] = pd.Series(False, index=out.index, dtype="boolean")
    out["flag_audit_required_analysis_missing"] = (
        _bcol(out, "flag_audit_required_analysis_missing")
        if "flag_audit_required_analysis_missing" in out.columns
        else pd.Series(False, index=out.index, dtype="boolean")
    )
    out["flag_audit_duplicate_complete_key"] = pd.Series(False, index=out.index, dtype="boolean")

    if "range_flag_count" in out.columns:
        range_count = pd.to_numeric(out["range_flag_count"], errors="coerce").fillna(0)
    else:
        range_count = pd.Series(0, index=out.index)
    out["flag_audit_range_issue"] = (range_count > 0).astype("boolean")

    out["flag_audit_stage3_issue"] = _bcol(out, "flag_any_carbonate_issue")
    out["flag_audit_stage3_issue_strict"] = _bcol(out, "flag_any_carbonate_issue_strict")
    out["flag_audit_replicate_conflict"] = _bcol(out, "flag_stage2_replicate_conflict_carried")

    has_calculated_output = _merge_calculated_output_presence(out).fillna(False)
    out["has_calculated_carbonate_output"] = has_calculated_output.astype("boolean")
    out["flag_audit_unknown_solver"] = (
        has_calculated_output & _bcol(out, "flag_solver_unknown").fillna(False)
    ).astype("boolean")
    out["flag_audit_unknown_input_pair"] = (
        has_calculated_output & _bcol(out, "flag_carbon_input_pair_unknown").fillna(False)
    ).astype("boolean")

    out["flag_audit_strict_dic_fail"] = _bcol(out, "flag_dic_species_audit_strict")
    out["flag_audit_dic_unit_mismatch"] = _bcol(out, "flag_dic_species_unit_mismatch_audit")
    out["flag_audit_dic_unit_missing"] = _bcol(out, "flag_dic_species_unit_missing_audit")
    out["flag_audit_dic_audit_not_run"] = _bcol(out, "flag_dic_species_audit_not_run")
    out["flag_audit_dic_values_missing"] = _bcol(out, "flag_dic_species_values_missing_audit")
    out["flag_audit_dic_nonpositive"] = _bcol(out, "flag_dic_species_nonpositive_dic_audit")
    out["flag_audit_negative_co2aq"] = _bcol(out, "flag_dic_species_negative_co2aq_audit")
    out["flag_audit_negative_hco3"] = _bcol(out, "flag_dic_species_negative_hco3_audit")
    out["flag_audit_negative_co3"] = _bcol(out, "flag_dic_species_negative_co3_audit")

    _set_flag_for_existing_index(out, missing_key_idx, "flag_audit_missing_key")

    if required_analysis_missing_idx is not None:
        _set_flag_for_existing_index(
            out,
            required_analysis_missing_idx,
            "flag_audit_required_analysis_missing",
        )

    if not dup_table.empty:
        _set_flag_for_existing_index(
            out,
            dup_table.index,
            "flag_audit_duplicate_complete_key",
        )

    severe = (
        out["flag_audit_missing_key"].fillna(False)
        | out["flag_audit_required_analysis_missing"].fillna(False)
        | out["flag_audit_stage3_issue_strict"].fillna(False)
        | out["flag_audit_strict_dic_fail"].fillna(False)
        | out["flag_audit_dic_unit_mismatch"].fillna(False)
        | out["flag_audit_unknown_solver"].fillna(False)
        | out["flag_audit_unknown_input_pair"].fillna(False)
    )

    review = (
        out["flag_audit_duplicate_complete_key"].fillna(False)
        | out["flag_audit_range_issue"].fillna(False)
        | out["flag_audit_stage3_issue"].fillna(False)
        | out["flag_audit_replicate_conflict"].fillna(False)
        | out["flag_audit_dic_unit_missing"].fillna(False)
        | out["flag_audit_dic_audit_not_run"].fillna(False)
        | out["flag_audit_dic_values_missing"].fillna(False)
        | _bcol(out, "flag_dic_inconsistent_robust")
        | _bcol(out, "flag_ph_diag_mismatch")
        | _bcol(out, "flag_ph_diag_mismatch_robust")
    )

    fail_def = [
        ("flag_audit_missing_key", "missing_key"),
        ("flag_audit_required_analysis_missing", "missing_required_analysis"),
        ("flag_audit_stage3_issue_strict", "stage3_strict_issue"),
        ("flag_audit_strict_dic_fail", "strict_dic_species_fail"),
        ("flag_audit_dic_unit_mismatch", "strict_dic_unit_mismatch"),
        ("flag_audit_unknown_solver", "unknown_solver"),
        ("flag_audit_unknown_input_pair", "unknown_input_pair"),
    ]

    review_def = [
        ("flag_audit_duplicate_complete_key", "duplicate_complete_key"),
        ("flag_audit_range_issue", "range_flag"),
        ("flag_audit_stage3_issue", "stage3_issue"),
        ("flag_audit_replicate_conflict", "replicate_conflict_carried"),
        ("flag_audit_dic_unit_missing", "strict_dic_unit_missing"),
        ("flag_audit_dic_audit_not_run", "strict_dic_audit_not_run"),
        ("flag_audit_dic_values_missing", "strict_dic_values_missing"),
        ("flag_dic_inconsistent_robust", "dic_robust_issue"),
        ("flag_ph_diag_mismatch", "ph_diag_issue"),
        ("flag_ph_diag_mismatch_robust", "ph_diag_robust_issue"),
    ]

    n_rows = len(out)
    fail_codes: List[List[str]] = [[] for _ in range(n_rows)]
    review_codes: List[List[str]] = [[] for _ in range(n_rows)]
    index_to_pos = {idx: pos for pos, idx in enumerate(out.index)}

    for flag_col, reason in fail_def:
        for idx in out.index[_bcol(out, flag_col)]:
            fail_codes[index_to_pos[idx]].append(reason)

    for flag_col, reason in review_def:
        for idx in out.index[_bcol(out, flag_col)]:
            review_codes[index_to_pos[idx]].append(reason)

    out["analysis_audit_reason_fail"] = pd.Series(
        [";".join(sorted(set(codes))) or pd.NA for codes in fail_codes],
        index=out.index,
        dtype="string",
    )
    out["analysis_audit_reason_review"] = pd.Series(
        [";".join(sorted(set(codes))) or pd.NA for codes in review_codes],
        index=out.index,
        dtype="string",
    )
    out["analysis_audit_reason_codes"] = pd.Series(
        [
            ";".join(sorted(set(fail + review))) or pd.NA
            for fail, review in zip(fail_codes, review_codes)
        ],
        index=out.index,
        dtype="string",
    )

    # FIX 8-A: Use explicit where() pattern so priority ordering is unambiguous.
    # The previous sequential assignment (PASS → REVIEW → FAIL) was logically
    status = pd.Series("PASS", index=out.index, dtype="string")
    status = status.where(~review, "REVIEW")
    status = status.where(~severe, "FAIL")
    out["analysis_audit_status"] = status

    # Set audit status from the Row role (decided at Stage QC, ADR-0006).
    # CRM rows get CRM_QC, Standard rows get STD_QC, Samples get PASS/REVIEW/FAIL
    # Inputs written before row_role existed fall back to the deprecated
    # row_classification labels.
    masks = _role_masks(out)
    if masks is not None:
        audit_status = out["analysis_audit_status"].copy()
        crm_mask, std_mask = masks
        # CRM rows should have CRM_QC verdict
        audit_status[crm_mask] = "CRM_QC"
        # TRIS rows should have STD_QC verdict
        audit_status[std_mask] = "STD_QC"
        out["analysis_audit_status"] = audit_status

    return out


# =============================================================================
# Reason counts
# =============================================================================


def reason_count_table(
    df: pd.DataFrame,
    col: str = "analysis_audit_reason_codes",
) -> pd.DataFrame:
    """Return a histogram of semicolon separated audit reason codes."""
    if col not in df.columns:
        return pd.DataFrame(columns=["reason_code", "count"])

    values = (
        df[col]
        .dropna()
        .astype("string")
        .str.split(";")
        .explode()
        .dropna()
        .str.strip()
    )
    values = values[values.ne("")]

    if values.empty:
        return pd.DataFrame(columns=["reason_code", "count"])

    return values.value_counts().rename_axis("reason_code").reset_index(name="count")


# =============================================================================
# Stage run (#42)
# =============================================================================

_DIC_FLAG_COLUMNS = (
    "flag_dic_species_audit_strict",
    "flag_dic_species_unit_mismatch_audit",
    "flag_dic_species_unit_missing_audit",
    "flag_dic_species_audit_not_run",
    "flag_dic_species_values_missing_audit",
)


def _run_carbonate_calc(df: pd.DataFrame, cc_cfg: Dict[str, Any]) -> Tuple[pd.DataFrame, str, Dict[str, Any]]:
    # The import is deliberately OUTSIDE the try/except below. If carbonate
    # chemistry was asked for and the engine cannot be imported, that is a
    # broken install and must fail loudly: a silently skipped calculation
    # yields an analysis_ready.csv with no chemistry while the run succeeds.
    from . import carbonate_calc

    try:
        # The module's own 'enabled' default must not override an explicit on.
        res = carbonate_calc.compute(df, {**cc_cfg, "enabled": True})
    except Exception as exc:
        # The calculation was asked for, so a failure stops Stage 4 (#44).
        # Continuing would write an analysis_ready.csv without the requested
        # chemistry while the run reports success.
        raise SystemExit(
            f"ERROR: Stage 4 carbonate calculation failed: {type(exc).__name__}: {exc}. "
            "Fix the inputs, or set carbonate_calc.enabled to false to skip it."
        ) from exc
    meta = {
        "n_computed": res.n_computed,
        "n_skipped": res.n_skipped,
        "settings": res.settings,
        "batch_quality": res.batch_quality,
        "notes": list(res.notes),
    }
    note = f"Computed carbonate system for {res.n_computed} rows ({res.n_skipped} skipped) with PyCO2SYS."
    return res.df, note, meta


def run(
    df: pd.DataFrame,
    stage_config: "StageConfig",
    *,
    source: Optional[str] = None,
    range_checks: bool = True,
    dic_species_check: bool = True,
    carbonate_calc: bool = False,
) -> StageResult:
    """Run Stage 4 on Stage 3's enhanced frame; no disk IO.

    ``range_checks`` and ``dic_species_check`` switch those audits off.
    The internal PyCO2SYS calculation runs when ``carbonate_calc`` is True
    or the config sets ``carbonate_calc.enabled``. ``source`` labels the
    input in the frame's ``source_file_stage4`` column, the report and the
    run bundle. Raises ``ValueError`` for another Stage's config; a missing
    required key column stops with ``SystemExit`` as before.
    """
    # Stage 4 shares Stage 2's alias, presence and inventory steps.
    from .stage2 import (
        ensure_required_columns,
        make_column_inventory,
        make_presence_table,
        materialize_canonical_aliases,
    )

    if stage_config.stage != "stage4":
        raise ValueError(f"Stage 4 needs the stage4 config, got {stage_config.stage}.")
    config = stage_config.config
    required_key_cols = list(config.get("required_stage4_key_columns", config.get("required_stage3_columns", [])))
    required_analysis_cols = list(config.get("required_stage4_analysis_columns", []))
    expected_cols = list(config.get("expected_stage4_columns", config.get("expected_stage3_columns", [])))
    required_cols = list(dict.fromkeys(required_key_cols + required_analysis_cols))
    notes: List[str] = []

    df = normalize_columns(df.copy())
    df["source_file_stage4"] = str(source) if source is not None else ""
    df["stage4_processed_utc"] = utc_stamp()
    df, alias_resolution = materialize_canonical_aliases(df, config["canonical_aliases"], notes)
    # Required key columns are the hard Stage 4 contract. Required analysis
    # columns are handled separately so they can become explicit FAIL reasons.
    ensure_required_columns(df, required_key_cols)
    df = coerce_and_standardize(df, notes)

    presence_df = make_presence_table(df, required=required_cols, expected=expected_cols)
    missing_opt = presence_df.loc[(~presence_df["required"]) & (~presence_df["present"]), "column"].tolist()
    if missing_opt:
        notes.append("Optional expected columns not found: " + ", ".join(missing_opt))
    inventory_df = make_column_inventory(df)

    # The internal carbonate calculation runs before the range checks and
    # DIC audit, so those audit the pipeline's own chemistry.
    cc_cfg = config.get("carbonate_calc", {}) or {}
    carbonate_note, carbonate_meta = "Skipped (not enabled).", {}
    if carbonate_calc or bool(cc_cfg.get("enabled", False)):
        df, carbonate_note, carbonate_meta = _run_carbonate_calc(df, cc_cfg)

    dup_keys = [str(k).strip() for k in config.get("duplicate_keys", []) if str(k).strip()]
    key_missing = missing_key_rows(df, required_key_cols)
    analysis_missing = missing_analysis_rows(df, required_analysis_cols)
    dup_table, dup_msgs, keys_used = detect_duplicates(df, dup_keys)

    range_summary, range_flags_df = pd.DataFrame(), pd.DataFrame()
    # Stage 4's own Range policy (#41).
    policy = stage_config.range_policy
    if range_checks:
        range_summary, range_flags_df = run_range_checks(df, policy)
    else:
        notes.append("Range checks were disabled.")
    df = add_range_flag_count(df, range_flags_df)

    dic_note, dic_meta = "Skipped (disabled by user or config).", {}
    dic_check = DicSpeciesAudit.from_config(config)
    if dic_species_check and dic_check.enabled:
        dic_result, dic_note, dic_meta = dic_species_audit(
            df,
            dic_check,
            candidates=config.get("strict_dic_candidates", {}),
            unit_equivalents=set(config.get("unit_equivalents", [])),
        )
        for col in _DIC_FLAG_COLUMNS:
            df[col] = (
                dic_result[col] if col in dic_result.columns else pd.Series(False, index=df.index, dtype="boolean")
            )
    else:
        notes.append("Strict DIC vs species audit disabled.")
        dic_result = pd.DataFrame(index=df.index)
        for col in _DIC_FLAG_COLUMNS:
            df[col] = pd.Series(False, index=df.index, dtype="boolean")
            dic_result[col] = df[col]

    df = add_readiness_status(
        df,
        dup_table=dup_table,
        missing_key_idx=key_missing.index,
        required_analysis_missing_idx=analysis_missing.index,
    )

    status_counts = (
        df["analysis_audit_status"].value_counts(dropna=False).rename_axis("status").reset_index(name="count")
    )
    reason_counts_df = reason_count_table(df)
    notes_md = "\n".join(f"- {n}" for n in notes) if notes else "- (none)"

    def _flag_count(col: str) -> int:
        if col in df.columns:
            return int(df[col].fillna(False).sum())
        return 0

    report = f"""# Stage 4 Analysis Audit Report

**Generated:** {utc_stamp()}
**Input:** `{source}`
**Rows:** {len(df):,}  **Columns:** {df.shape[1]:,}

## What this stage does
Audits the Stage 3 table for contract compliance, key integrity, range
violations, and optional strict DIC species closure. Assigns
`analysis_audit_status` (PASS / REVIEW / FAIL) with explicit reason
codes. Does NOT rebuild chemistry or overwrite Stage 3 QC flags.

## Final readiness classification
{md_table_from_df(status_counts, max_rows=20)}

### Reason code counts
{md_table_from_df(reason_counts_df, max_rows=200) if not reason_counts_df.empty else "_(none)_"}

## Canonical field presence
{md_table_from_df(presence_df, max_rows=200)}

## Key and duplicate integrity
- Required key columns: `{list(required_key_cols)}`
- Required analysis columns: `{list(required_analysis_cols)}`
- Duplicate keys requested: `{dup_keys}`
- Duplicate keys actually used: `{keys_used}`
- Rows with missing key fields: **{len(key_missing):,}**
- Rows with missing required analysis fields: **{len(analysis_missing):,}**
- Duplicate rows found: **{len(dup_table):,}**

## Range checks
- Variables checked: **{len(range_summary):,}**
- Flagged cells: **{len(range_flags_df):,}**

{md_table_from_df(range_summary, max_rows=200) if not range_summary.empty else "_(no range rows written)_"}

## Strict DIC vs species audit
{dic_note}

- Rows with strict DIC fail: **{_flag_count("flag_audit_strict_dic_fail"):,}**
- Rows with DIC unit mismatch: **{_flag_count("flag_audit_dic_unit_mismatch"):,}**
- Rows with DIC unit missing: **{_flag_count("flag_audit_dic_unit_missing"):,}**
- Rows where DIC audit did not run: **{_flag_count("flag_audit_dic_audit_not_run"):,}**
- Rows with missing DIC species values: **{_flag_count("flag_audit_dic_values_missing"):,}**

## Inherited Stage 3 context flags
| Flag | Rows |
|------|-----:|
| flag_any_carbonate_issue | {_flag_count("flag_any_carbonate_issue"):,} |
| flag_any_carbonate_issue_strict | {_flag_count("flag_any_carbonate_issue_strict"):,} |
| flag_stage2_replicate_conflict_carried | {_flag_count("flag_stage2_replicate_conflict_carried"):,} |
| flag_solver_unknown | {_flag_count("flag_solver_unknown"):,} |
| flag_carbon_input_pair_unknown | {_flag_count("flag_carbon_input_pair_unknown"):,} |

## Column inventory (top 30 by missingness)
{md_table_from_df(inventory_df.head(30), max_rows=200)}

## Notes
{notes_md}

## Main outputs
- analysis-ready CSV: `data/analysis_ready.csv`
- range_flags_long: `tables/range_flags_long.csv`
- dic_species_audit: `tables/dic_species_audit.csv`
"""

    def status(name: str) -> int:
        return int((df["analysis_audit_status"] == name).sum())

    manifest = {
        "notebook": NOTEBOOK,
        "generated_utc": utc_stamp(),
        "input_csv": source,
        "config_source": stage_config.source,
        "config_warnings": list(stage_config.warnings),
        "parameters": {},
        "policies": {
            "range_policy": asdict(policy),
            "dic_species_audit": asdict(dic_check),
            "required_stage4_key_columns": required_key_cols,
            "required_stage4_analysis_columns": required_analysis_cols,
            "expected_stage4_columns": expected_cols,
            "duplicate_keys": dup_keys,
            "duplicate_keys_used": keys_used,
        },
        "alias_resolution": alias_resolution,
        "dic_column_sources": dic_meta,
        "carbonate_calc": {"note": carbonate_note, **carbonate_meta},
        "duplicate_messages": list(dup_msgs),
        "row_counts": {
            "n_rows": int(len(df)),
            "missing_key_rows": int(len(key_missing)),
            "missing_required_analysis_rows": int(len(analysis_missing)),
            "duplicate_rows": int(len(dup_table)),
            "range_flagged_cells": int(len(range_flags_df)),
            "dic_strict_fails": _flag_count("flag_dic_species_audit_strict"),
            "status_PASS": status("PASS"),
            "status_REVIEW": status("REVIEW"),
            "status_FAIL": status("FAIL"),
            "status_CRM_QC": status("CRM_QC"),
            "status_STD_QC": status("STD_QC"),
        },
        "reason_code_counts": (
            reason_counts_df.set_index("reason_code")["count"].to_dict() if not reason_counts_df.empty else {}
        ),
        "notes": notes,
        "package_versions": package_versions(),
    }
    alias_df = pd.DataFrame(
        {"canonical_column": list(alias_resolution.keys()), "resolved_from": list(alias_resolution.values())}
    )
    return StageResult(
        stage="stage4",
        data={"data/analysis_ready.csv": df},
        tables={
            "tables/column_inventory.csv": inventory_df,
            "tables/missingness_top40.csv": inventory_df.head(40),
            "tables/canonical_presence.csv": presence_df,
            "tables/alias_resolution.csv": alias_df,
            "tables/missing_key_rows.csv": key_missing,
            "tables/duplicates_by_keys.csv": dup_table,
            "tables/range_check_summary.csv": range_summary,
            "tables/range_flags_long.csv": range_flags_df,
            "tables/dic_species_audit.csv": dic_result,
        },
        reports={"reports/report.md": report},
        texts={"logs/effective_config.json": json_text(config)},
        manifest=manifest,
        input_file=source,
        config_files=[stage_config.source],
        bundle_name=NOTEBOOK,
    )
