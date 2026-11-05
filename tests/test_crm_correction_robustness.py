# tests/test_crm_correction_robustness.py
import pandas as pd
from roap.common import build_corrections_table


def test_build_corrections_table_always_returns_dataframe():
    """build_corrections_table never returns None, even with no grouping or no valid CRM rows."""
    # Case 1: Empty DataFrame with required columns
    df = pd.DataFrame(columns=["ta_corrected_umolkg", "ta_umol_kg", "crm_batch", "ta_corrected_umolkg_is_outlier"])
    result = build_corrections_table(df, group_by=None, diff_col="ta_corrected_umolkg", min_n=2)
    assert isinstance(result, pd.DataFrame)
    assert "overall_n" in result.columns
    assert "overall_correction" in result.columns
    assert "overall_sd" in result.columns

    # Case 2: CRM rows but all filtered as outliers (with group_by)
    # When all rows are outliers with group_by, returns DataFrame with overall_n=0
    df = pd.DataFrame({
        "ta_corrected_umolkg": [2200.0, 2210.0, 2220.0],
        "ta_umol_kg": [2300.0, 2310.0, 2320.0],
        "crm_batch": ["RM213", "RM213", "RM213"],
        "ta_corrected_umolkg_is_outlier": [True, True, True],
    })
    result = build_corrections_table(df, group_by="crm_batch", diff_col="ta_corrected_umolkg", min_n=2)
    assert isinstance(result, pd.DataFrame)
    assert "overall_n" in result.columns

    # Case 3: group_by column not in df
    df = pd.DataFrame({
        "ta_corrected_umolkg": [2200.0, 2210.0],
        "ta_umol_kg": [2300.0, 2310.0],
        "ta_corrected_umolkg_is_outlier": [False, False],
    })
    result = build_corrections_table(df, group_by="crm_batch", diff_col="ta_corrected_umolkg", min_n=2)
    assert isinstance(result, pd.DataFrame)
    assert "overall_n" in result.columns


def test_invariant_test_runs_without_config():
    """Stage 2 runs without a config file and does not crash on CRM correction.

    Guards the old ``AttributeError: 'NoneType' object has no attribute
    'columns'`` from a missing corrections table.
    """
    from pathlib import Path

    from roap import stage2
    from roap.stage_config import load_stage_config

    golden = Path(__file__).resolve().parent / "golden" / "example_data"
    df = pd.read_csv(golden / "oa_stage1b_outputs" / "data" / "analysis_ready_samples.csv")
    result = stage2.run(df, load_stage_config("stage2", None))
    assert "data/enhanced.csv" in result.data
    assert len(result.data["data/enhanced.csv"]) == len(df)
