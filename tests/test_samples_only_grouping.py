"""Only Sample rows count in duplicate, replicate and QC grouping (#44).

CRM and Standard rows are carried through every Stage (#29) but must never
join a duplicate or replicate group, a precision statistic, or a per-group QC
count. Each test gives non-Sample rows the same complete keys as Samples, so
the old behaviour (grouping every row) would fail it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roap.schema import add_duplicate_flags
from roap.stage2 import (
    add_conflict_annotations,
    add_duplicate_annotations,
    add_replicate_annotations,
    duplicate_check,
    replicate_harmonise,
)
from roap.stage3 import CarbonateIntegrityThresholds, build_qc_summary, carbonate_integrity_checks
from roap.stage4 import detect_duplicates

ROLES = ["SAMPLE", "CRM", "CRM", "STANDARD"]


def _keyed(**extra) -> pd.DataFrame:
    """One Sample, two CRMs and a Standard, all sharing one complete key."""
    return pd.DataFrame({"row_role": ROLES, "station_id": "ST1", "sample_id": "X", **extra})


# Stage 1A -------------------------------------------------------------------


def test_stage1a_duplicate_flags_ignore_non_samples() -> None:
    df = _keyed()
    assert add_duplicate_flags(df, ["station_id", "sample_id"]) == 0
    assert not df["flag_possible_duplicate"].any()

    # Two Samples with the same key are still duplicates.
    df = _keyed()
    df.loc[1, "row_role"] = "SAMPLE"
    assert add_duplicate_flags(df, ["station_id", "sample_id"]) == 2
    assert df["flag_possible_duplicate"].tolist() == [True, True, False, False]


def test_stage1a_incomplete_key_flag_is_samples_only() -> None:
    df = pd.DataFrame({"row_role": ROLES, "sample_id": [pd.NA] * 4})
    add_duplicate_flags(df, ["sample_id"])
    assert df["flag_duplicate_key_incomplete"].tolist() == [True, False, False, False]

    df = pd.DataFrame({"row_role": ROLES})
    add_duplicate_flags(df, [])
    assert df["flag_duplicate_key_incomplete"].tolist() == [True, False, False, False]


def test_missing_row_role_is_an_error() -> None:
    with pytest.raises(KeyError, match="row_role"):
        add_duplicate_flags(pd.DataFrame({"sample_id": ["A", "A"]}), ["sample_id"])


# Stage 2 --------------------------------------------------------------------


def test_stage2_duplicate_check_ignores_non_samples() -> None:
    df = _keyed(ph_best=[8.0, 7.0, 7.1, 9.0])
    dups, summary, keys = duplicate_check(df, ["station_id", "sample_id"])
    assert keys == ["station_id", "sample_id"]
    assert dups.empty and summary.empty

    annotated = add_duplicate_annotations(df, keys)
    assert not annotated["flag_duplicate"].any()
    assert annotated["duplicate_group_size"].isna().tolist() == [False, True, True, True]
    assert annotated["duplicate_group_size"].iloc[0] == 1
    assert not annotated["flag_duplicate_key_incomplete"].any()


def test_stage2_replicates_and_statistics_use_samples_only() -> None:
    keys = ["station_id", "sample_id"]
    df = _keyed(ph_best=[8.0, 7.0, 7.1, 9.0], ph_best_source=["a", "b", "c", "d"])
    df.loc[1, "row_role"] = "SAMPLE"  # a second Sample replicate: pH 7.0

    rep_mean, rep_mean_sd, consistency, disagree, keys_used, mean_vars, nrep = replicate_harmonise(
        df,
        requested_keys=keys,
        mean_whitelist=["ph_best"],
        consistency_cols=["ph_best_source"],
        sd_thresholds={"ph_best": 0.01},
        conflict_class_map={"provenance": ["ph_best_source"]},
    )
    assert nrep["n_reps"].tolist() == [2]
    assert rep_mean["ph_best"].tolist() == [7.5]  # mean of the two Samples only
    assert rep_mean_sd["sd__ph_best"].iloc[0] == pytest.approx(pd.Series([8.0, 7.0]).std())
    assert consistency["n_unique_nonnull"].tolist() == [2]  # sources a and b only

    annotated = add_replicate_annotations(df, nrep, keys_used)
    annotated = add_conflict_annotations(annotated, consistency, disagree, keys_used)
    assert annotated["replicate_group_n"].isna().tolist() == [False, False, True, True]
    assert annotated["flag_has_replicates"].tolist() == [True, True, False, False]
    assert annotated["flag_replicate_any_conflict"].tolist() == [True, True, False, False]
    assert annotated["flag_replicate_sd_exceeded"].tolist() == [True, True, False, False]
    assert annotated["row_role"].tolist() == ROLES[:1] + ["SAMPLE"] + ROLES[2:]


def test_stage2_replicates_need_a_groupable_sample() -> None:
    df = pd.DataFrame({"row_role": ["CRM", "STANDARD"], "station_id": "ST1", "ph_best": [7.0, 9.0]})
    with pytest.raises(SystemExit):
        replicate_harmonise(df, ["station_id"], ["ph_best"], [], {}, {})


# Stage 3 --------------------------------------------------------------------


def _dic_frame(roles: list[str], diffs: list[float]) -> pd.DataFrame:
    """DIC species frame whose DIC differs from the species sum by ``diffs``."""
    return pd.DataFrame(
        {
            "row_role": roles,
            "dic_best_umol_kg": [2000.0 + d for d in diffs],
            "co2aq_calc_umol_kg": 10.0,
            "hco3_calc_umol_kg": 1800.0,
            "co3_calc_umol_kg": 190.0,
            "dic_unit_normalized": "umol/kg",
            "co2aq_unit_normalized": "umol/kg",
            "hco3_unit_normalized": "umol/kg",
            "co3_unit_normalized": "umol/kg",
        }
    )


def test_stage3_summary_counts_samples_only() -> None:
    df = _dic_frame(["SAMPLE"] * 6 + ["CRM"] * 2, [0.1 * i for i in range(6)] + [500.0, 600.0])
    flags, summary, dic_mismatches, _ = carbonate_integrity_checks(df, CarbonateIntegrityThresholds())

    # Row flags stay on every row (informational) ...
    assert flags["flag_dic_inconsistent"].tolist() == [False] * 6 + [True, True]
    assert len(dic_mismatches) == 2
    # ... but only Samples are counted.
    assert summary["n_dic_checkable"] == 6
    assert summary["n_dic_inconsistent"] == 0
    assert summary["n_any_carbonate_issue"] == 0


def test_stage3_robust_population_is_samples_only() -> None:
    # Five Samples with one clear outlier (40). Ten CRM rows at 40 would pull
    # the median and MAD to themselves and hide that outlier.
    df = _dic_frame(["SAMPLE"] * 5 + ["CRM"] * 10, [0.0, 0.5, -0.5, 0.25, 40.0] + [40.0] * 10)
    flags, summary, _, _ = carbonate_integrity_checks(df, CarbonateIntegrityThresholds())
    robust = flags["flag_dic_inconsistent_robust"].tolist()
    assert robust == [False, False, False, False, True] + [False] * 10
    assert summary["n_dic_inconsistent_robust"] == 1


def test_stage3_qc_summary_groups_samples_only() -> None:
    df = pd.DataFrame(
        {
            "row_role": ["SAMPLE", "SAMPLE", "CRM", "STANDARD", "CRM"],
            "station_id": ["ST1", "ST1", "ST1", pd.NA, pd.NA],
            "flag_any_carbonate_issue": [False, True, True, True, True],
        }
    )
    qc, keys = build_qc_summary(df, ["station_id"])
    assert keys == ["station_id"]
    assert qc["n_rows"].tolist() == [2]
    assert qc["n_any_carbonate_issue"].tolist() == [1]
    assert qc["n_rows_with_incomplete_group_key"].tolist() == [0]


# Stage 4 --------------------------------------------------------------------


def test_stage4_duplicates_ignore_non_samples() -> None:
    dup, _, keys = detect_duplicates(_keyed(), ["station_id", "sample_id"])
    assert keys == ["station_id", "sample_id"] and dup.empty

    df = _keyed()
    df.loc[2, "row_role"] = "SAMPLE"
    dup, _, _ = detect_duplicates(df, ["station_id", "sample_id"])
    assert dup.index.tolist() == [0, 2]


def test_stage4_duplicates_fall_back_to_legacy_labels() -> None:
    legacy = _keyed().drop(columns="row_role").assign(row_classification=["SAMPLE", "CRM", "CRM_QC", "STD"])
    dup, _, _ = detect_duplicates(legacy, ["station_id", "sample_id"])
    assert dup.empty

    # An input with no roles at all compares every row, as before.
    unlabelled = _keyed().drop(columns="row_role")
    dup, _, _ = detect_duplicates(unlabelled, ["station_id", "sample_id"])
    assert len(dup) == 4


# Stage 3 run: group counts merge back onto rows --------------------------------

STAGE3_INPUT = (
    Path(__file__).resolve().parent
    / "golden" / "example_data" / "oa_stage2_outputs" / "data" / "enhanced.csv"
)


def _stage3_run(df: pd.DataFrame, tmp_path: Path):
    from roap import stage3
    from roap.stage_config import load_stage_config

    cfg = tmp_path / "07_stage3.yaml"
    cfg.write_text("qc_group_keys: [station_id]\n", encoding="utf-8")
    return stage3.run(df, load_stage_config("stage3", cfg))


def test_stage3_run_without_groupable_samples(tmp_path) -> None:
    """No Samples, or no Sample with a complete key, still runs (#44)."""
    full = pd.read_csv(STAGE3_INPUT)
    refs = full["row_role"].ne("SAMPLE")
    assert refs.sum() == 7

    # Only reference rows, all with complete station IDs.
    only_refs = full.loc[refs].assign(station_id="ST_REF")
    no_sample_keys = full.copy()
    no_sample_keys.loc[~refs, "station_id"] = pd.NA
    no_sample_keys.loc[refs, "station_id"] = "ST_REF"

    for df in (only_refs, no_sample_keys):
        result = _stage3_run(df, tmp_path)
        out = result.data["data/enhanced.csv"]
        qc = result.tables["tables/qc_summary_by_group.csv"]
        assert len(out) == len(df)
        assert out["row_role"].tolist() == df["row_role"].tolist()
        assert "flag_any_carbonate_issue" in out  # row-wise output kept
        assert qc.empty and "station_id" in qc.columns
        assert out["n_rows"].isna().all()


def test_stage3_run_gives_references_no_group_counts(tmp_path) -> None:
    """A reference row sharing a Sample group's key gets no group counts."""
    df = pd.read_csv(STAGE3_INPUT)
    refs = df["row_role"].ne("SAMPLE")
    station = df.loc[~refs, "station_id"].dropna().iloc[0]
    df.loc[refs, "station_id"] = station

    out = _stage3_run(df, tmp_path).data["data/enhanced.csv"]
    in_group = out["station_id"].eq(station)
    samples = in_group & out["row_role"].eq("SAMPLE")
    assert out.loc[samples, "n_rows"].notna().all()
    assert out.loc[samples, "n_rows"].iloc[0] == samples.sum()
    assert out.loc[out["row_role"].ne("SAMPLE"), "n_rows"].isna().all()
