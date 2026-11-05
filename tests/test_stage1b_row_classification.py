# tests/test_stage1b_row_classification.py
"""Stage 1B row classification stop-gaps until roap.row_roles (#40) replaces them."""

from __future__ import annotations

import copy

import pandas as pd

from roap.stage1b import STAGE1B_DEFAULTS, add_presence_flags, add_provenance_fields


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
