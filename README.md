# CVD Prevention Gap Atlas

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23298097.svg)](https://doi.org/10.5281/zenodo.23298097)
[![tests](https://github.com/Gideono29/cvd-prevention-gap-atlas/actions/workflows/tests.yml/badge.svg)](https://github.com/Gideono29/cvd-prevention-gap-atlas/actions/workflows/tests.yml)
[Interactive map](https://gideono29.github.io/cvd-prevention-gap-atlas/)

County and census-tract map joining **CDC PLACES, HRSA, USDA RUCA and CDC/ATSDR SVI** (and, optionally, CDC WONDER
mortality) to locate where cardiovascular risk burden outpaces prevention capacity.

Maintainer: Gideon Owusu, Michigan Technological University
([ORCID 0009-0000-0540-7449](https://orcid.org/0009-0000-0540-7449))

**Status: v1.0.0.** The pipeline runs end to end on real PLACES 2025, RUCA 2020, SVI 2022 and HRSA
HPSA data (2,957 counties, 78,815 tracts scored; Kentucky and Pennsylvania are absent from the PLACES 2025 core
measures, see `docs/methods.md`). A static interactive map is in `site/`. CDC WONDER mortality is supported by the pipeline
but **not included in v1** (burden is PLACES-based), see `docs/methods.md`.

## Citation

See `CITATION.cff`. Cite all versions with the concept DOI
[10.5281/zenodo.23298097](https://doi.org/10.5281/zenodo.23298097), or v1.0.0 specifically with
[10.5281/zenodo.23298098](https://doi.org/10.5281/zenodo.23298098).

## Index

For each county or tract:

- **Burden** = mean percentile of PLACES crude prevalence (CHD, stroke, high BP, diabetes, smoking, obesity),
  combined with WONDER CVD mortality at county level when an export is supplied (not in v1.0.0).
- **Capacity** = mean percentile of preventive-care use (checkup, BP medication, cholesterol screening), inverted
  uninsured rate and inverted HRSA primary-care HPSA score (no designation = best).
- **Gap** = burden percentile − capacity percentile; positive means burden outpaces capacity. Computed nationally
  (`gap_national`) and within RUCA stratum (`gap_stratum`: metropolitan, micropolitan, small town, rural).
- SVI is carried as an overlay column and is not part of the gap.

See `docs/methods.md` for the specification and limitations.

## Quick start

```bash
pip install -e .[test]
gapatlas download          # PLACES county + tract from data.cdc.gov (SHA-256 manifest)
# add RUCA, SVI, HRSA, WONDER files by hand: see data/raw/README.md
gapatlas build             # outputs/gap_county.csv, gap_tract.csv, run_manifest.json
gapatlas sensitivity       # outputs/sensitivity_summary.csv (weights, leave-one-measure-out)
pip install -e .[site]     # then: gapatlas site  -> site/data/ (needs Census boundaries, see data/raw/README.md)
python -m http.server -d site 8000   # view the map at http://localhost:8000
gapatlas check-release     # exit code 10 when CDC has published a newer PLACES release
pytest -q
```

## Refresh

`.github/workflows/refresh.yml` runs `gapatlas check-release` weekly and opens an issue when a new PLACES release is
detected. Releases are cut manually after reviewing the rebuilt outputs (`docs/release_checklist.md`).

## Limitations

PLACES values are model-based small-area estimates, not direct measurements. WONDER suppresses counts under 10 and
has no bulk county API, so mortality is a manual export and is missing for small counties. The gap is a
prioritization index, not a causal claim, and depends on weighting choices.
