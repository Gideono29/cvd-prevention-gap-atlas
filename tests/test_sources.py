import pandas as pd

from gapatlas.sources import load_hpsa, load_places, load_ruca, load_svi, ruca_county


def test_places_pivot_crude_only(tmp_path):
    p = tmp_path / "places.csv"
    pd.DataFrame({
        "LocationID": ["1001", "1001", "1001", "1003"],
        "MeasureId": ["CHD", "CHD", "STROKE", "CHD"],
        "Data_Value_Type": ["Crude prevalence", "Age-adjusted prevalence", "Crude prevalence", "Crude prevalence"],
        "Data_Value": ["6.0", "5.0", "3.0", "7.5"],
    }).to_csv(p, index=False)
    out = load_places(p, "county").set_index("fips")
    assert out.loc["01001", "CHD"] == 6.0 and out.loc["01001", "STROKE"] == 3.0
    assert out.loc["01003", "CHD"] == 7.5


def test_ruca_uses_2020_tracts_and_drops_secondary_codes(tmp_path):
    p = tmp_path / "ruca.csv"
    pd.DataFrame({"TractFIPS23": ["01001020101", "01001020200", "01003000100"],
                  "TractFIPS20": ["01001020100", "01001020200", "01003000100"],
                  "PrimaryRUCA": ["1", "1", "99"],
                  "PrimaryRUCADescription": ["a", "b", "c"]}).to_csv(p, index=False)
    out = load_ruca(p)
    assert out["fips"].tolist() == ["01001020100", "01001020200"]
    assert set(out["stratum"]) == {"metropolitan"}


def test_ruca_county_mode():
    t = pd.DataFrame({"fips": ["01001000001", "01001000002", "01001000003"], "ruca": [4, 4, 1]})
    assert ruca_county(t)["stratum"].iloc[0] == "micropolitan"


def test_svi_missing_sentinel(tmp_path):
    p = tmp_path / "svi.csv"
    pd.DataFrame({"FIPS": ["1001", "1003"], "RPL_THEMES": [0.4, -999]}).to_csv(p, index=False)
    out = load_svi(p, "county")
    assert out["svi"].iloc[0] == 0.4 and pd.isna(out["svi"].iloc[1])


def test_hpsa_designated_max_per_county(tmp_path):
    f = "State and County Federal Information Processing Standard Code"
    p = tmp_path / "hpsa.csv"
    pd.DataFrame({"HPSA Status": ["Designated", "Designated", "Withdrawn", "Designated"],
                  "HPSA Score": ["10", "18", "25", "7"],
                  f: ["01001", "01001", "01001", "01003"]}).to_csv(p, index=False)
    out = load_hpsa(p).set_index("fips")["hpsa_score"]
    assert out["01001"] == 18 and out["01003"] == 7
