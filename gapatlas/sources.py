"""Loaders that normalise each source to FIPS-keyed frames."""
from pathlib import Path

import pandas as pd

from .config import ACCESS_BARRIER_MEASURES, BURDEN_MEASURES, CAPACITY_MEASURES, RUCA_STRATA


def _read(path, **kw) -> pd.DataFrame:
    """read_csv that tolerates BOMs and non-UTF-8 (Latin-1) source files."""
    try:
        return pd.read_csv(path, encoding="utf-8-sig", **kw)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", **kw)


def county_fips(s: pd.Series) -> pd.Series:
    return s.astype(str).str.extract(r"(\d+)")[0].str.zfill(5)


def tract_fips(s: pd.Series) -> pd.Series:
    return s.astype(str).str.extract(r"(\d+)")[0].str.zfill(11)


def load_places(path: Path, level: str) -> pd.DataFrame:
    """Long PLACES file -> wide, one row per county/tract, columns = MeasureId (crude prevalence, %)."""
    df = _read(path, dtype=str)
    df = df[df["Data_Value_Type"].str.contains("Crude", na=False)]
    keep = set(BURDEN_MEASURES + CAPACITY_MEASURES + ACCESS_BARRIER_MEASURES)
    df = df[df["MeasureId"].isin(keep)].copy()
    df["value"] = pd.to_numeric(df["Data_Value"], errors="coerce")
    df["fips"] = tract_fips(df["LocationID"]) if level == "tract" else county_fips(df["LocationID"])
    return df.pivot_table(index="fips", columns="MeasureId", values="value", aggfunc="first").reset_index()


def load_ruca(path: Path) -> pd.DataFrame:
    """USDA tract-level RUCA csv ('State-County-Tract FIPS Code', 'Primary RUCA Code')."""
    df = _read(path, dtype=str)
    # The file carries 2020 and 2023 tract IDs. They differ only in Connecticut, where PLACES 2025 uses the 2023
    # planning-region IDs, so both are kept (a tract ID appears under one vintage only).
    code_col = "PrimaryRUCA" if "PrimaryRUCA" in df.columns else next(
        c for c in df.columns if "primary" in c.lower() and "ruca" in c.lower())
    id_cols = [c for c in ("TractFIPS20", "TractFIPS23") if c in df.columns] or [
        next(c for c in df.columns if "tract" in c.lower() and "fips" in c.lower())]
    ruca = pd.to_numeric(df[code_col], errors="coerce")
    out = pd.concat([pd.DataFrame({"fips": tract_fips(df[c]), "ruca": ruca}) for c in id_cols])
    out = out.dropna(subset=["fips"]).drop_duplicates("fips")
    out = out[out["ruca"].isin(RUCA_STRATA)].copy()
    out["stratum"] = out["ruca"].map(RUCA_STRATA)
    return out


def ruca_county(tracts: pd.DataFrame) -> pd.DataFrame:
    """County stratum = stratum of the county's most common RUCA code (ties go to the more urban code)."""
    t = tracts.assign(county=tracts["fips"].str[:5])
    mode = t.groupby("county")["ruca"].agg(lambda s: s.value_counts().sort_index().idxmax())
    return pd.DataFrame({"fips": mode.index, "ruca": mode.values,
                         "stratum": mode.map(RUCA_STRATA).values})


def load_svi(path: Path, level: str) -> pd.DataFrame:
    """CDC/ATSDR SVI csv: FIPS and RPL_THEMES (overall percentile; negative = missing)."""
    df = _read(path, dtype={"FIPS": str})
    svi = pd.to_numeric(df["RPL_THEMES"], errors="coerce")
    svi = svi.where(svi >= 0)
    fips = tract_fips(df["FIPS"]) if level == "tract" else county_fips(df["FIPS"])
    return pd.DataFrame({"fips": fips, "svi": svi})


def load_hpsa(path: Path) -> pd.DataFrame:
    """HRSA primary-care HPSA download -> max designated HPSA score per county."""
    fips = "State and County Federal Information Processing Standard Code"
    df = _read(path, dtype=str, usecols=["HPSA Status", "HPSA Score", fips])
    d = df[df["HPSA Status"].str.strip().str.lower().eq("designated")].copy()
    d["fips"] = county_fips(d[fips])
    d["score"] = pd.to_numeric(d["HPSA Score"], errors="coerce")
    return d.groupby("fips", as_index=False)["score"].max().rename(columns={"score": "hpsa_score"})


def load_wonder(path: Path) -> pd.DataFrame:
    """CDC WONDER underlying-cause export (tab-delimited, exported manually): county code and crude rate.
    Suppressed or unreliable rows become NaN and are never imputed."""
    df = _read(path, sep="\t", dtype=str)
    df = df[df["County Code"].notna()].copy()
    df["fips"] = county_fips(df["County Code"])
    df["cvd_mortality"] = pd.to_numeric(df["Crude Rate"], errors="coerce")
    return df[["fips", "cvd_mortality"]]
