"""Download PLACES (county, tract) from data.cdc.gov and detect new releases."""
import hashlib
import json
from pathlib import Path

import requests

from .config import PLACES_COUNTY_ID, PLACES_TRACT_ID, SOCRATA_CSV, SOCRATA_META

UA = {"User-Agent": "gapatlas/0.1 (research; python-requests)"}
DATASETS = {"county": PLACES_COUNTY_ID, "tract": PLACES_TRACT_ID}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def places_metadata(dataset_id: str) -> dict:
    r = requests.get(SOCRATA_META.format(id=dataset_id), headers=UA, timeout=60)
    r.raise_for_status()
    m = r.json()
    return {"id": dataset_id, "name": m.get("name"), "rowsUpdatedAt": m.get("rowsUpdatedAt"),
            "viewLastModified": m.get("viewLastModified")}


def check_release(data_dir: Path) -> dict:
    """Compare live PLACES timestamps with the stored manifest. `new_release` is True if any differ."""
    manifest_path = Path(data_dir) / "raw" / "manifest.json"
    stored = json.loads(manifest_path.read_text()).get("places", {}) if manifest_path.exists() else {}
    live = {lvl: places_metadata(i) for lvl, i in DATASETS.items()}
    changed = [lvl for lvl, m in live.items()
               if stored.get(lvl, {}).get("rowsUpdatedAt") != m["rowsUpdatedAt"]]
    return {"new_release": bool(changed), "changed": changed, "live": live}


def download_places(data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    dest_dir = data_dir / "raw" / "places"
    dest_dir.mkdir(parents=True, exist_ok=True)
    record = {}
    for lvl, ds in DATASETS.items():
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
