"""Gap index: burden percentile minus capacity percentile (positive = burden outpaces capacity)."""
import numpy as np
import pandas as pd

from .config import ACCESS_BARRIER_MEASURES, BURDEN_MEASURES, CAPACITY_MEASURES, IndexSpec


def pct(s: pd.Series) -> pd.Series:
    """Percentile rank in [0, 100]; NaN stays NaN."""
    return s.rank(pct=True, method="average") * 100


def _row_mean(frame: pd.DataFrame, min_frac: float = 0.5) -> pd.Series:
    """Row mean over available columns, NaN when fewer than min_frac of them are present."""
    return frame.mean(axis=1, skipna=True).where(frame.notna().mean(axis=1) >= min_frac)


def _wmean(parts: list, weights: list) -> pd.Series:
    """Weighted mean of series, ignoring NaN entries (weights renormalised per row)."""
    stack = pd.concat(parts, axis=1)
    w = np.array(weights, dtype=float)
    present = stack.notna().values * w
    den = present.sum(axis=1)
    num = (np.nan_to_num(stack.values) * w).sum(axis=1)
    return pd.Series(np.where(den > 0, num / np.where(den > 0, den, 1), np.nan), index=stack.index)


def burden_score(df: pd.DataFrame, spec: IndexSpec = IndexSpec()) -> pd.Series:
    cols = [m for m in BURDEN_MEASURES if m in df.columns]
    parts = [_row_mean(pd.concat([pct(df[m]) for m in cols], axis=1))] if cols else []
    weights = [spec.burden_weight_places] if cols else []
    if "cvd_mortality" in df.columns and spec.burden_weight_mortality > 0:
        parts.append(pct(df["cvd_mortality"]))
        weights.append(spec.burden_weight_mortality)
    return _wmean(parts, weights) if parts else pd.Series(np.nan, index=df.index)


def capacity_score(df: pd.DataFrame, spec: IndexSpec = IndexSpec()) -> pd.Series:
    """Higher = more prevention capacity. Preventive-care use ranks up; uninsured rate and HPSA score rank down."""
    ranked = [pct(df[m]) for m in CAPACITY_MEASURES if m in df.columns]
    ranked += [100 - pct(df[m]) for m in ACCESS_BARRIER_MEASURES if m in df.columns]
    parts, weights = [], []
    if ranked:
        parts.append(_row_mean(pd.concat(ranked, axis=1)))
        weights.append(spec.capacity_weight_preventive)
    if "hpsa_score" in df.columns:
        # No designation = score 0 (best); undesignated areas tie at the top of the capacity scale.
        parts.append(100 - pct(df["hpsa_score"].fillna(0)))
        weights.append(spec.capacity_weight_hpsa)
    return _wmean(parts, weights) if parts else pd.Series(np.nan, index=df.index)


def gap_table(df: pd.DataFrame, spec: IndexSpec = IndexSpec()) -> pd.DataFrame:
    """Adds burden, capacity, gap_national, gap_stratum (if 'stratum' present) and a top-decile flag."""
    out = df.copy()
    out["burden"] = burden_score(out, spec)
    out["capacity"] = capacity_score(out, spec)
    out["gap_national"] = pct(out["burden"]) - pct(out["capacity"])
    if "stratum" in out.columns:
        g = out.groupby("stratum", dropna=True)
        out["gap_stratum"] = g["burden"].transform(pct) - g["capacity"].transform(pct)
    out["top_decile_gap"] = out["gap_national"] >= out["gap_national"].quantile(0.9)
    return out
