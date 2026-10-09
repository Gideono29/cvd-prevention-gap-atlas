"""Generate the static map site data: simplified county GeoJSON and one tract GeoJSON per state.

Needs the optional `site` dependencies (geopandas, shapely, pyogrio) and the Census cartographic boundary
files in data/raw/boundaries (see data/raw/README.md).
"""
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .build import assemble
from .config import IndexSpec
from .index import gap_table

COUNTY_TOL = 0.01    # degrees, about 1 km
TRACT_TOL = 0.0015   # degrees, about 150 m
METRICS = ["gap_national", "gap_stratum", "gap_no_hpsa", "burden", "capacity", "svi"]


def _props(res: pd.DataFrame, cols: list) -> pd.DataFrame:
    out = res[["fips"] + [c for c in cols if c in res.columns]].copy()
    for c in out.columns[1:]:
        if c == "top_decile_gap":
            out[c] = out[c].astype(int)
        elif c == "stratum":
            continue
        else:
            out[c] = out[c].astype(float).round(2 if c == "svi" else 1)
    return out


def _write(gdf, path: Path, tol: float):
    import shapely
    g = gdf.copy()
    g["geometry"] = shapely.set_precision(g.geometry.simplify(tol, preserve_topology=True), 1e-4)
    g = g[~g.geometry.is_empty]
    path.parent.mkdir(parents=True, exist_ok=True)
    # NaN -> null so the browser sees missing values as missing
    path.write_text(g.to_json(drop_id=True).replace("NaN", "null"), encoding="utf-8")


def generate(data_dir: Path, site_dir: Path) -> dict:
    import geopandas as gpd

    data_dir, site_dir = Path(data_dir), Path(site_dir)
    bdir = data_dir / "raw" / "boundaries"
    frames, used, _ = assemble(data_dir)
    out = {}

    # County table, plus the HPSA-excluded gap used by the map toggle
    cnt = gap_table(frames["county"])
    alt = gap_table(frames["county"], replace(IndexSpec(), capacity_weight_hpsa=0.0))
    cnt["gap_no_hpsa"] = alt["gap_national"]
    cnt_cols = METRICS + ["top_decile_gap", "stratum", "hpsa_score"]
    cp = _props(cnt, cnt_cols)

    cg = gpd.read_file(bdir / "cb_2020_us_county_500k.zip")
    cg = cg[cg["STATEFP"].astype(int) <= 56][["GEOID", "NAME", "STUSPS", "STATEFP", "geometry"]]
    cg = cg.rename(columns={"GEOID": "fips"}).merge(cp, on="fips", how="left")
    cg["scored"] = cg["gap_national"].notna().astype(int)
    out["counties"] = {"features": int(len(cg)), "scored": int(cg["scored"].sum())}
    _write(cg.to_crs(4326), site_dir / "data" / "counties.geojson", COUNTY_TOL)

    # Tract table
    trt = gap_table(frames["tract"])
    tp = _props(trt, ["gap_national", "gap_stratum", "burden", "capacity", "svi", "top_decile_gap", "stratum"])
    states = {}
    n_feat = n_scored = 0
    for shp in sorted(bdir.glob("cb_2020_*_tract_500k.zip")):
        st = shp.name.split("_")[2]
        tg = gpd.read_file(shp)[["GEOID", "geometry"]].rename(columns={"GEOID": "fips"})
        tg = tg.merge(tp, on="fips", how="left")
        tg["scored"] = tg["gap_national"].notna().astype(int)
        n_feat += len(tg)
        n_scored += int(tg["scored"].sum())
        tg = tg.to_crs(4326)
        b = tg.total_bounds
        states[st] = [round(float(x), 3) for x in b]
        _write(tg, site_dir / "data" / "tracts" / f"{st}.geojson", TRACT_TOL)
    (site_dir / "data" / "states.json").write_text(json.dumps(states), encoding="utf-8")
    out["tracts"] = {"features": n_feat, "scored": n_scored, "states": len(states)}
    out["inputs"] = used
    (site_dir / "data" / "site_manifest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out
