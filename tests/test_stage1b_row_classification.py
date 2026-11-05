# tests/test_stage1b_row_classification.py
"""Stage 1B row classification stop-gaps until roap.row_roles (#40) replaces them."""

from __future__ import annotations

import copy

import pandas as pd

from roap.stage1b import (
    STAGE1B_DEFAULTS,
    add_presence_flags,
    add_provenance_fields,
    classify_rows_sample,
)


def test_crm_and_std_rows_are_not_sample_rows() -> None:
    """is_sample_row is a boolean, so CRM/STD rows are not flagged as samples (#47)."""
    df = pd.DataFrame(
        {
            "sample_type": ["sample", "crm", "std"],
            "ta_best_umolkg": [2300.0, float("nan"), float("nan")],
            "ph_best": [8.1, float("nan"), float("nan")],
        }
    )

    add_provenance_fields(df, copy.deepcopy(STAGE1B_DEFAULTS))
    # The sample row has complete core chemistry; CRM/STD rows have none.
    df["calc_salinity"] = 35.0
    df["calc_temperature_c"] = 25.0
    df["calc_pressure_dbar"] = 0.0
    add_presence_flags(df)

    assert df["is_sample_row"].tolist() == [True, False, False]
    assert df["flag_core_chemistry_missing"].tolist() == [False, False, False]


def _untagged_frame(index: list) -> pd.DataFrame:
    """Rows with no usable sample_type label fall back to the QC flags."""
    return pd.DataFrame(
        {
            "sample_type": ["sample", None, "", "unknown", "  ", None],
            "is_ta_crm_row": [False, False, False, False, True, False],
            "is_phstd_row": [False, False, False, False, False, True],
        },
        index=index,
    )


# blank -> SAMPLE, empty -> SAMPLE, unrecognised -> SAMPLE, CRM flag -> CRM,
# pH standard flag -> STD (the docstring's QC-flag fallback, as in the prototype).
EXPECTED_FALLBACK = ["SAMPLE", "SAMPLE", "SAMPLE", "SAMPLE", "CRM", "STD"]


def test_untagged_rows_fall_back_to_qc_flags() -> None:
    """Blank or unrecognised sample_type on a non-CRM row no longer raises NameError (#38)."""
    out = classify_rows_sample(_untagged_frame(list(range(6))))
    assert out.tolist() == EXPECTED_FALLBACK


def test_untagged_rows_with_non_range_index() -> None:
    """The fallback uses label-aligned masks, not positional .iloc (#38)."""
    index = [10, 3, 7, 42, 0, 5]
    out = classify_rows_sample(_untagged_frame(index))
    assert out.index.tolist() == index
    assert out.tolist() == EXPECTED_FALLBACK
