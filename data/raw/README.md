# Raw inputs

`gapatlas download` fetches PLACES into `places/`. The other sources are release-specific and must be placed by hand
(they are git-ignored; record their provenance in your release notes):

- `ruca/*.csv`: USDA ERS RUCA tract file, saved as csv
- `svi/*county*.csv`, `svi/*tract*.csv`: CDC/ATSDR SVI downloads
- `hrsa/*.csv`: HRSA primary-care HPSA download
- `wonder/*.txt`: CDC WONDER underlying-cause-of-death export (tab-delimited), grouped by county, ICD-10 I00-I99

See `gapatlas/config.py` for the source pages.
