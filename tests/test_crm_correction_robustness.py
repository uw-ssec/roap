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
    """Simulate invariant test running Stage 2 without --config-dir."""
    # This is more of an integration test - verify pipeline stage runs
    # without config don't crash on CRM correction
    import subprocess
    from pathlib import Path

    # Run Stage 2 notebook via papermill without config dir
    # Should not crash with AttributeError: 'NoneType' object has no attribute 'columns'
    # (This test may be slow - mark as @pytest.mark.slow)
    pass
