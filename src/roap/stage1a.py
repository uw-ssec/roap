"""Stage 1A: canonical schema, presence, range and duplicate flags (#42).

``run(df, stage_config)`` orders the existing ``roap.schema`` steps and
returns a ``StageResult``; it does no disk IO. ``schema.py`` keeps the step
functions. Notebook 04 reads Stage QC's ``derived.csv``, calls ``run`` and
writes the result with ``roap.stage_result.write_stage_result``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional, Sequence

import pandas as pd

from .common import (
    build_flag_summary,
    coerce_datetime,
    coerce_numeric,
    make_missingness_table,
    md_table_from_df,
    utc_stamp,
)
from .policy import add_stage_range_flags
from .schema import (
    add_canonical_presence_flags,
    add_duplicate_flags,
    apply_canonical_schema,
    build_canonical_export,
    build_canonical_inventory,
    build_numeric_candidates_for_canonical,
    choose_duplicate_keys,
)
from .stage_config import StageConfig
from .stage_result import StageResult, package_versions

__all__ = ["NOTEBOOK", "run"]

NOTEBOOK = "04_stage1a"


def run(
    df: pd.DataFrame,
    stage_config: StageConfig,
    *,
    source: Optional[str] = None,
    duplicate_keys: Optional[Sequence[str]] = None,
    preserve_original_columns: bool = True,
) -> StageResult:
    """Run Stage 1A on Stage QC's derived frame.

    ``source`` labels the input (e.g. the derived.csv path) in the frame's
    ``source_file`` column and the report. ``duplicate_keys`` overrides the
    duplicate key tuple chosen from ``duplicate_key_candidates``. Raises
    ``ValueError`` for an empty frame or override keys that are not columns.
    """
    if stage_config.stage != "stage1a":
        raise ValueError(f"Stage 1A needs the stage1a config, got {stage_config.stage}.")
    if df.empty:
        raise ValueError(f"Stage 1A input is empty: {source or '<frame>'}")
    config, range_policy = stage_config.config, stage_config.range_policy

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df["source_file"] = str(source) if source is not None else ""
    df["stage1a_processed_utc"] = utc_stamp()
    # Alias resolution below may create sample_date again, so it is coerced
    # a second time after the canonical schema is applied.
    if "sample_date" in df.columns:
        coerce_datetime(df, "sample_date")

    df, rename_audit, source_lookup = apply_canonical_schema(
        df, config=config, preserve_original_columns=preserve_original_columns
    )
    coerce_numeric(df, build_numeric_candidates_for_canonical())
    if "sample_date" in df.columns:
        coerce_datetime(df, "sample_date")

    add_stage_range_flags(df, policy=range_policy)
    add_canonical_presence_flags(df, config=config)

    override = list(duplicate_keys) if duplicate_keys else None
    if override:
        missing = [col for col in override if col not in df.columns]
        if missing:
            raise ValueError(
                "DUPLICATE_KEYS contains columns not present in the dataframe: "
                + ", ".join(missing)
            )
    dup_keys = choose_duplicate_keys(df, config, override_keys=override)
    n_dup = add_duplicate_flags(df, dup_keys)

    analysis_ready = build_canonical_export(df, config=config)
    inventory = build_canonical_inventory(df, config=config)
    missing_tbl = make_missingness_table(df)

    report = _report(
        df, source, stage_config, preserve_original_columns, rename_audit,
        inventory, missing_tbl, dup_keys, n_dup,
    )
    manifest = {
        "notebook": NOTEBOOK,
        "generated_utc": utc_stamp(),
        "input_csv": source,
        "config_source": stage_config.source,
        "config_warnings": list(stage_config.warnings),
        "parameters": {
            "DUPLICATE_KEYS": list(override) if override else None,
            "DUPLICATE_KEYS_USED": dup_keys,
            "PRESERVE_ORIGINAL_COLUMNS": preserve_original_columns,
        },
        "policy": {
            "range_policy": asdict(range_policy),
            "duplicate_keys_used": dup_keys,
            "required_columns": config.get("required_columns", []),
            "canonical_export_order": config.get("canonical_export_order", []),
        },
        "row_counts": {
            "staged_rows": int(len(df)),
            "analysis_ready_rows": int(len(analysis_ready)),
            "possible_duplicate_rows": int(n_dup),
        },
        "canonical_summary": {
            "n_present": int(inventory["present"].sum()),
            "n_missing": int((~inventory["present"]).sum()),
        },
    }
    manifest["package_versions"] = package_versions()
    return StageResult(
        stage="stage1a",
        data={"data/staged.csv": df, "data/analysis_ready.csv": analysis_ready},
        tables={
            "logs/rename_audit.csv": rename_audit,
            "logs/canonical_inventory.csv": inventory,
            "logs/missingness.csv": missing_tbl,
        },
        reports={"reports/report.md": report},
        texts={
            "logs/effective_config.json": _json_text(config),
            "logs/source_lookup.json": _json_text(source_lookup),
        },
        manifest=manifest,
        input_file=source,
        config_files=[stage_config.source],
        bundle_name=NOTEBOOK,
    )


def _json_text(obj) -> str:
    # Same layout as roap.common.write_json.
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)

def _report(
    df, source, stage_config, preserve, rename_audit, inventory, missing_tbl, dup_keys, n_dup
) -> str:
    range_policy = stage_config.range_policy
    flag_summary = build_flag_summary(df)

    def section(table: pd.DataFrame, empty: str) -> str:
        return md_table_from_df(table, max_rows=200) if not table.empty else empty

    return f"""# Stage 1A Report

**Generated:** {utc_stamp()}
**Source CSV:** `{source}`
**Config source:** `{stage_config.source if stage_config.source else "DEFAULT_CONFIG"}`
**Rows:** {len(df):,}
**Columns:** {df.shape[1]:,}
**Preserve original columns:** `{preserve}`

## What this script does
1. Resolve canonical alias columns from the source frame.
2. Normalise TA-unit and pH-scale labels to canonical strings.
3. Add range, presence and duplicate flags. These flags are advisory and never destructive.
4. Write a staged frame and an analysis-ready frame.

## Canonical column actions
{section(rename_audit, "_(No canonical actions applied)_")}

## Canonical inventory
{section(inventory, "_(No canonical inventory available)_")}

## Missingness inventory (top 50)
{md_table_from_df(missing_tbl.head(50), max_rows=200)}

## Duplicate checks
- Duplicate keys used: `{dup_keys}`
- Rows flagged as possible duplicates: **{n_dup}**

## Range policy used
- Salinity: {range_policy.sal_min} to {range_policy.sal_max}
- TA: {range_policy.ta_min} to {range_policy.ta_max} umol/kg
- pH: {range_policy.ph_min} to {range_policy.ph_max}
- Depth: {range_policy.depth_min} to {range_policy.depth_max} m
- Latitude: {range_policy.lat_min} to {range_policy.lat_max}
- Longitude: {range_policy.lon_min} to {range_policy.lon_max}

## Flag summary
{section(flag_summary, "_(No flags were added.)_")}

## Main outputs
- `data/staged.csv`: Stage 1B reads this in the current runner.
- `data/analysis_ready.csv`: canonical export order for review and downstream use.
- `logs/source_lookup.json`: where each canonical column came from.
"""
