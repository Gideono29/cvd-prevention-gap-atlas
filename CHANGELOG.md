# Changelog

## 1.0.0 (2026-10-11)
First release. Burden is **PLACES-based only**: CDC WONDER mortality is supported by the pipeline but not included in
this release (WONDER has no bulk county API; the export is manual).
- Data: PLACES 2025 release, SVI 2022, RUCA 2020, HRSA primary-care HPSA (downloaded 2026-10-09).
- 2,957 counties and 78,815 tracts scored; Kentucky and Pennsylvania have no PLACES 2025 core estimates and are not
  scored (see `docs/methods.md`).
- Static interactive map (`site/`), county and per-state tract layers, Connecticut planning regions.
- Fixed `gapatlas sensitivity` on installs without scipy.
- `gapatlas sensitivity` (weight and leave-one-out variants, rank correlation and top-decile overlap).
- Source loaders, gap index, build and PLACES release check, with unit tests on synthetic data.
