# Raw inputs

`gapatlas download` fetches PLACES into `places/`. The other sources are release-specific and must be placed by hand
(they are git-ignored; record their provenance in your release notes):

- `ruca/*.csv`: USDA ERS RUCA tract file, saved as csv
- `svi/*county*.csv`, `svi/*tract*.csv`: CDC/ATSDR SVI downloads
- `hrsa/*.csv`: HRSA primary-care HPSA download
- `wonder/*.txt`: CDC WONDER underlying-cause-of-death export (tab-delimited), grouped by county, ICD-10 I00-I99
- `boundaries/cb_2020_us_county_500k.zip` and `boundaries/cb_2020_<SS>_tract_500k.zip` (one per state and DC):
  Census cartographic boundaries, <https://www2.census.gov/geo/tiger/GENZ2020/shp/>. Used only by `gapatlas site`.
  Connecticut: also `boundaries/cb_2022_us_county_500k.zip` and `boundaries/cb_2022_09_tract_500k.zip`
  (<https://www2.census.gov/geo/tiger/GENZ2022/shp/>), because PLACES 2025 uses planning regions (09110-09190).

See `gapatlas/config.py` for the source pages.
