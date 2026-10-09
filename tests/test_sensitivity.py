import numpy as np
import pandas as pd

from gapatlas.sensitivity import run


def _df(n=200, seed=0):
    r = np.random.default_rng(seed)
    d = pd.DataFrame({"fips": [f"{i:05d}" for i in range(n)]})
    for m in ["CHD", "STROKE", "BPHIGH", "DIABETES", "CSMOKING", "OBESITY", "CHECKUP", "ACCESS2"]:
        d[m] = r.normal(10, 2, n)
    return d


def test_tract_like_has_no_weight_variants():
    out = run(_df(), "tract")
    assert not out["variant"].str.contains("weight").any()
    assert out["variant"].str.startswith("drop_burden_").all()


def test_hpsa_variants_and_bounds():
    d = _df()
    d["hpsa_score"] = np.random.default_rng(1).integers(0, 20, len(d)).astype(float)
    out = run(d, "county")
    assert {"hpsa_weight=0.0", "preventive_weight=2.0"} <= set(out["variant"])
    assert out["spearman_vs_baseline"].between(-1, 1).all()
    assert out["top_decile_overlap"].between(0, 1).all()
