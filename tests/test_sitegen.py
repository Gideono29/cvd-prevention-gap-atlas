import pandas as pd

from gapatlas.sitegen import _props


def test_props_rounding_and_flags():
    df = pd.DataFrame({"fips": ["01001"], "gap_national": [12.3456], "svi": [0.6789],
                       "top_decile_gap": [True], "stratum": ["rural"]})
    out = _props(df, ["gap_national", "svi", "top_decile_gap", "stratum", "missing_col"])
    assert out.loc[0, "gap_national"] == 12.3 and out.loc[0, "svi"] == 0.68
    assert out.loc[0, "top_decile_gap"] == 1 and out.loc[0, "stratum"] == "rural"
    assert "missing_col" not in out.columns
