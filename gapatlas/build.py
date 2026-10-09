"""Join sources into county and tract gap tables."""
import json
from pathlib import Path

from . import __version__
from .config import IndexSpec
from .index import gap_table
from .sources import load_hpsa, load_places, load_ruca, load_svi, load_wonder, ruca_county


def _first(raw: Path, sub: str, pattern: str) -> Path | None:
    hits = sorted((raw / sub).glob(pattern)) if (raw / sub).exists() else []
    return hits[0] if hits else None


def assemble(data_dir: Path) -> tuple:
    """Join all available sources. Returns ({level: joined frame}, {input name: file}, {level: skip note})."""
    raw = Path(data_dir) / "raw"
    used, frames, skipped = {}, {}, {}

    ruca_path = _first(raw, "ruca", "*.csv")
    ruca_t = load_ruca(ruca_path) if ruca_path else None
    if ruca_path:
        used["ruca"] = ruca_path.name

    for level in ("county", "tract"):
        places_path = raw / "places" / f"places_{level}.csv"
        if not places_path.exists():
            skipped[level] = "skipped: PLACES file missing (run `gapatlas download`)"
            continue
        df = load_places(places_path, level)
        used[f"places_{level}"] = places_path.name

        svi_path = _first(raw, "svi", f"*{level}*.csv")
        if svi_path:
            df = df.merge(load_svi(svi_path, level), on="fips", how="left")
            used[f"svi_{level}"] = svi_path.name
        if ruca_t is not None:
            strata = ruca_t if level == "tract" else ruca_county(ruca_t)
            df = df.merge(strata[["fips", "stratum"]], on="fips", how="left")
        if level == "county":
            hpsa_path = _first(raw, "hrsa", "*.csv")
            if hpsa_path:
                df = df.merge(load_hpsa(hpsa_path), on="fips", how="left")
                used["hrsa"] = hpsa_path.name
            wonder_path = _first(raw, "wonder", "*.txt")
            if wonder_path:
                df = df.merge(load_wonder(wonder_path), on="fips", how="left")
                used["wonder"] = wonder_path.name

        frames[level] = df
    return frames, used, skipped


def build(data_dir: Path, out_dir: Path, spec: IndexSpec = IndexSpec()) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames, used, summary = assemble(data_dir)
    for level, df in frames.items():
        res = gap_table(df, spec)
        res.to_csv(out_dir / f"gap_{level}.csv", index=False)
        summary[level] = {"rows": int(len(res)), "top_decile": int(res["top_decile_gap"].sum())}

    manifest = {"gapatlas_version": __version__, "inputs": used, "index_spec": spec.__dict__,
                "summary": summary}
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
