# tests/test_crm_tris_preservation.py
import pandas as pd
import pytest
from roap.stage1b import classify_rows_sample, analysis_ready_subset, STAGE1B_DEFAULTS


def test_classify_rows_sample_preserves_crm_tris():
    """classify_rows_sample identifies CRM/TRIS but doesn't drop them."""
    df = pd.DataFrame({
        "sample_id": ["S1", "S2", "RM213_1", "tris_1"],
        "sample_type": ["sample", "sample", "crm", "std"],
        "sample_tag": ["S1", "S2", "RM213_1", "tris_1"],
        "ta_best_umolkg": [2300.0, 2310.0, 2200.0, 2305.0],
        "ph_best": [8.1, 8.05, 8.08, 8.06],
    })
    
    is_sample = classify_rows_sample(df)
    # CRM and TRIS rows should be "CRM"/"STD" (not "SAMPLE")
    assert is_sample.iloc[0] == "SAMPLE"   # S1
    assert is_sample.iloc[1] == "SAMPLE"   # S2
    assert is_sample.iloc[2] == "CRM"      # RM213_1 (CRM)
    assert is_sample.iloc[3] == "STD"      # tris_1 (STD)


def test_analysis_ready_subset_preserves_all_rows():
    """analysis_ready_subset returns all rows with verdict column, not just samples."""
    df = pd.DataFrame({
        "sample_id": ["S1", "S2", "RM213_1", "tris_1"],
        "sample_type": ["sample", "sample", "crm", "std"],
        "sample_tag": ["S1", "S2", "RM213_1", "tris_1"],
        "ta_best_umolkg": [2300.0, 2310.0, 2200.0, 2305.0],
        "ph_best": [8.1, 8.05, 8.08, 8.06],
        "salinity": [35.0]*4,
        "temperature_insitu_c": [25.0]*4,
        "is_sample_row": [True, True, False, False],
        "ta_qc_status_norm": ["PASS"]*4,
        "phstd_status_norm": ["PASS", "PASS", "PASS", "PASS"],
        "phstd_correction_applied": [False]*4,
    })
    
    # Add required columns for analysis_ready_subset
    for col in ["flag_lat_out_of_range", "flag_lon_out_of_range", "flag_sal_out_of_range",
                "flag_depth_out_of_range", "flag_calc_temperature_out_of_range",
                "flag_ta_out_of_range", "flag_ph_out_of_range", "flag_ta_non_numeric",
                "flag_ph_non_numeric", "flag_sal_non_numeric", "flag_calc_temperature_non_numeric",
                "flag_ta_units_missing", "flag_ta_units_unexpected", 
                "flag_ph_scale_observed_missing", "flag_ph_scale_observed_unexpected",
                "flag_core_chemistry_missing"]:
        df[col] = False
    
    result = analysis_ready_subset(df, STAGE1B_DEFAULTS)
    
    # Should have ALL 4 rows, not just 2 samples
    assert len(result) == 4, f"Expected 4 rows, got {len(result)}"
    
    # Sample rows get PASS/REVIEW/FAIL, CRM/TRIS get CRM_QC/STD_QC
    statuses = result.set_index("sample_tag")["safe_for_analysis_strict"]