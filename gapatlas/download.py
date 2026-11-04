"""Download PLACES (county, tract) from data.cdc.gov and detect new releases."""
import hashlib
import json
import re
from pathlib import Path

import requests

from .config import PLACES_COUNTY_ID, PLACES_TRACT_ID, SOCRATA_CSV, SOCRATA_META

CATALOG = "https://data.cdc.gov/api/catalog/v1"
NAME_RE = {"county": re.compile(r"^PLACES: Local Data for Better Health, County Data,? (\d{4}) release$"),
           "tract": re.compile(r"^PLACES: Local Data for Better Health, Census Tract Data,? (\d{4}) release$")}

UA = {"User-Agent": "gapatlas/0.1 (research; python-requests)"}
DATASETS = {"county": PLACES_COUNTY_ID, "tract": PLACES_TRACT_ID}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pick_latest(results: list, level: str) -> dict | None:
    """From catalog search results, the dataset with the highest release year for `level` (None if none match)."""
    best = None
    for r in results:
        m = NAME_RE[level].match(r["resource"]["name"])
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), r["resource"]["id"], r["resource"]["name"])
    return {"id": best[1], "release": best[0], "name": best[2]} if best else None


def latest_datasets() -> dict:
    """CDC publishes each PLACES release as a new dataset id, so look the newest one up in the catalog.
    Falls back to the ids in config if the catalog is unreachable or returns no match."""
    out = {}
    try:
        for level, q in (("county", "PLACES Local Data for Better Health County Data"),
                         ("tract", "PLACES Local Data for Better Health Census Tract Data")):
            r = requests.get(CATALOG, params={"q": q, "only": "datasets", "limit": 50}, headers=UA, timeout=60)
            r.raise_for_status()
            hit = pick_latest(r.json().get("results", []), level)
            if hit:
                out[level] = hit
    except requests.RequestException:
        pass
    for level, ds in DATASETS.items():
        out.setdefault(level, {"id": ds, "release": None, "name": None})
    return out


def places_metadata(dataset_id: str) -> dict:
    r = requests.get(SOCRATA_META.format(id=dataset_id), headers=UA, timeout=60)
    r.raise_for_status()
    m = r.json()
    return {"id": dataset_id, "name": m.get("name"), "rowsUpdatedAt": m.get("rowsUpdatedAt"),
            "viewLastModified": m.get("viewLastModified")}


def check_release(data_dir: Path) -> dict:
    """Compare the newest PLACES release on data.cdc.gov with the stored manifest. `new_release` is True if a level
    has a different dataset id (a newer release) or a newer timestamp on the same id."""
    manifest_path = Path(data_dir) / "raw" / "manifest.json"
    stored = json.loads(manifest_path.read_text()).get("places", {}) if manifest_path.exists() else {}
    live, changed = {}, []
    for lvl, d in latest_datasets().items():
        meta = places_metadata(d["id"])
        live[lvl] = {**meta, "release": d["release"]}
        st = stored.get(lvl, {})
        if st.get("id") != meta["id"] or st.get("rowsUpdatedAt") != meta["rowsUpdatedAt"]:
            changed.append(lvl)
    return {"new_release": bool(changed), "changed": changed, "live": live}


def download_places(data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    dest_dir = data_dir / "raw" / "places"
    dest_dir.mkdir(parents=True, exist_ok=True)
    record = {}
    for lvl, d in latest_datasets().items():
        ds = d["id"]
        meta = places_metadata(ds)
        dest = dest_dir / f"places_{lvl}.csv"
        tmp = dest.with_suffix(".csv.part")
        with requests.get(SOCRATA_CSV.format(id=ds), headers=UA, timeout=600, stream=True) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        if tmp.read_bytes()[:80].lstrip().lower().startswith((b"<!doctype", b"<html")):
            tmp.unlink()
            raise RuntimeError(f"PLACES {lvl}: got HTML instead of CSV (dataset id {ds} may have changed)")
        tmp.replace(dest)
        record[lvl] = {**meta, "file": dest.name, "bytes": dest.stat().st_size, "sha256": _sha256(dest)}
        print(f"downloaded PLACES {lvl}: {dest.stat().st_size / 1e6:.1f} MB", flush=True)
    manifest_path = data_dir / "raw" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest["places"] = record
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return record
