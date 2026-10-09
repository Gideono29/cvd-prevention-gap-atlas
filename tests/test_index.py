import numpy as np
import pandas as pd

from gapatlas.index import gap_table, pct
from gapatlas.sources import county_fips, tract_fips


def _frame():
    return pd.DataFrame({
        "fips": ["01001", "01003", "01005", "01007"],
        "CHD": [2, 4, 6, 8], "STROKE": [1, 2, 3, 4], "BPHIGH": [20, 30, 40, 50],
        "CHECKUP": [80, 70, 60, 50], "ACCESS2": [5, 10, 15, 20],
        "hpsa_score": [np.nan, 5, 10, 20],
        "stratum": ["rural", "rural", "metropolitan", "metropolitan"],
    })


def test_pct_range_and_nan():
    s = pct(pd.Series([1.0, 2.0, np.nan, 3.0]))
    assert s.isna().sum() == 1 and s.max() == 100


def test_gap_sign_high_burden_low_capacity():
    out = gap_table(_frame()).set_index("fips")
    assert out.loc["01007", "gap_national"] > 0 > out.loc["01001", "gap_national"]
    assert out["top_decile_gap"].sum() >= 1


def test_stratum_gap_present():
    assert "gap_stratum" in gap_table(_frame()).columns


def test_missing_inputs_give_nan_not_zero():
    df = _frame()
    df.loc[0, ["CHD", "STROKE", "BPHIGH"]] = np.nan
    assert np.isnan(gap_table(df).loc[0, "burden"])


def test_fips_padding():
    assert county_fips(pd.Series([1001, "6037"])).tolist() == ["01001", "06037"]
    assert tract_fips(pd.Series([1001020100])).iloc[0] == "01001020100"
