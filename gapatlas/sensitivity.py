"""Sensitivity of the gap ranking to index design choices."""
from dataclasses import replace

import pandas as pd

from .config import BURDEN_MEASURES, IndexSpec
from .index import gap_table

WEIGHTS = [0.0, 0.5, 1.0, 2.0]


def _compare(base: pd.DataFrame, alt: pd.DataFrame) -> dict:
    both = base["gap_national"].notna() & alt["gap_national"].notna()
    rho = base.loc[both, "gap_national"].corr(alt.loc[both, "gap_national"], method="spearman")
    a, b = set(base.index[base["top_decile_gap"] & both]), set(alt.index[alt["top_decile_gap"] & both])
    return {"n": int(both.sum()), "spearman_vs_baseline": round(float(rho), 4),
            "top_decile_overlap": round(len(a & b) / max(len(a | b), 1), 4)}


def run(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """df = joined (pre-index) table. Returns one row per variant compared with the default specification."""
    base = gap_table(df)
    rows = []
    has_mort = "cvd_mortality" in df.columns
    has_hpsa = "hpsa_score" in df.columns
    if has_hpsa:
        for w in WEIGHTS:
            if w == 1.0:
                continue
            alt = gap_table(df, replace(IndexSpec(), capacity_weight_hpsa=w))
            rows.append({"level": level, "variant": f"hpsa_weight={w}", **_compare(base, alt)})
    for w in WEIGHTS:
        if w == 1.0 or not has_hpsa:  # with one capacity component the weight cancels out
            continue
        alt = gap_table(df, replace(IndexSpec(), capacity_weight_preventive=w))
        rows.append({"level": level, "variant": f"preventive_weight={w}", **_compare(base, alt)})
    if has_mort:
        for w in WEIGHTS:
            if w == 1.0:
                continue
            alt = gap_table(df, replace(IndexSpec(), burden_weight_mortality=w))
            rows.append({"level": level, "variant": f"mortality_weight={w}", **_compare(base, alt)})
    for m in BURDEN_MEASURES:
        alt = gap_table(df, burden_measures=[x for x in BURDEN_MEASURES if x != m])
        rows.append({"level": level, "variant": f"drop_burden_{m}", **_compare(base, alt)})
    return pd.DataFrame(rows)
