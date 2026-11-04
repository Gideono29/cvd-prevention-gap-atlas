from gapatlas.download import pick_latest


def _r(i, name):
    return {"resource": {"id": i, "name": name}}


def test_pick_latest_takes_highest_release_year_and_ignores_other_datasets():
    res = [_r("a", "PLACES: Local Data for Better Health, County Data 2024 release"),
           _r("b", "PLACES: Local Data for Better Health, County Data, 2026 release"),
           _r("c", "PLACES: Local Data for Better Health, County Data, 2025 release"),
           _r("d", "PLACES: County Data (GIS Friendly Format), 2027 release"),
           _r("e", "PLACES: Local Data for Better Health, Census Tract Data, 2025 release")]
    assert pick_latest(res, "county")["id"] == "b"
    assert pick_latest(res, "tract")["id"] == "e"
    assert pick_latest([], "county") is None
