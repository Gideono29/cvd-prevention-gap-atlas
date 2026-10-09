"""Source registry and index definitions.

Dataset IDs and URLs change with each release. They are centralised here and recorded in the run manifest.
Verify them against the publisher pages before cutting a release.
"""
from dataclasses import dataclass

PLACES_COUNTY_ID = "swc5-untb"   # CDC PLACES, county, data.cdc.gov (Socrata)
PLACES_TRACT_ID = "cwsq-ngmh"    # CDC PLACES, census tract, data.cdc.gov (Socrata)
SOCRATA_CSV = "https://data.cdc.gov/api/views/{id}/rows.csv?accessType=DOWNLOAD"
SOCRATA_META = "https://data.cdc.gov/api/views/{id}.json"

# Release-specific sources; place the files in data/raw/<name>/ (see data/raw/README.md).
RUCA_URL = "https://www.ers.usda.gov/data-products/rural-urban-commuting-area-codes/"
SVI_URL = "https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html"
HRSA_URL = "https://data.hrsa.gov/data/download"
WONDER_URL = "https://wonder.cdc.gov/ucd-icd10-expanded.html"

# PLACES MeasureId values. Burden: higher is worse. Capacity: higher is better.
BURDEN_MEASURES = ["CHD", "STROKE", "BPHIGH", "DIABETES", "CSMOKING", "OBESITY"]
CAPACITY_MEASURES = ["CHECKUP", "BPMED", "CHOLSCREEN"]   # preventive-care use
ACCESS_BARRIER_MEASURES = ["ACCESS2"]                    # uninsured, 18-64; higher is worse

# RUCA primary code -> stratum
RUCA_STRATA = {**{c: "metropolitan" for c in (1, 2, 3)},
               **{c: "micropolitan" for c in (4, 5, 6)},
               **{c: "small_town" for c in (7, 8, 9)},
               10: "rural"}


@dataclass(frozen=True)
class IndexSpec:
    burden_weight_places: float = 1.0
    burden_weight_mortality: float = 1.0
    capacity_weight_hpsa: float = 1.0
    capacity_weight_preventive: float = 1.0
