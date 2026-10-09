# Methods

## Units and keys
County = 5-digit FIPS; tract = 11-digit GEOID. All sources are zero-padded to these widths before joining.

## Sources
| Source | Used for | Level | Acquisition |
|---|---|---|---|
| CDC PLACES | crude prevalence of burden and preventive-care measures | county, tract | `gapatlas download` (Socrata) |
| CDC WONDER | county CVD crude mortality rate | county | manual export to `data/raw/wonder/*.txt` |
| HRSA HPSA | maximum designated primary-care HPSA score | county | manual download to `data/raw/hrsa/*.csv` |
| USDA RUCA | rural-urban stratum (primary code) | tract; county = most common code | manual download to `data/raw/ruca/*.csv` |
| CDC/ATSDR SVI | overlay (RPL_THEMES) | county, tract | manual download to `data/raw/svi/*county*.csv`, `*tract*.csv` |

## Score construction
1. Each input is converted to a percentile rank in [0, 100] across all units at that level.
2. Burden: row mean of PLACES burden percentiles (needs at least half present), then weighted mean with the
   mortality percentile when available. Weights default to 1:1.
3. Capacity: row mean of preventive-care percentiles and inverted uninsured percentile, then weighted mean with the
   inverted HPSA percentile. Undesignated counties have HPSA score 0.
4. `gap_national` = percentile(burden) − percentile(capacity). `gap_stratum` ranks within RUCA stratum.
   `top_decile_gap` flags the top 10% of `gap_national`.
5. Missing inputs are never imputed. Units without enough inputs get NaN.

## Planned
- Sensitivity analysis on weights (mortality and HPSA weights 0, 0.5, 1, 2) with rank correlation of gaps.
- Uncertainty propagation from PLACES confidence limits for tracts.
- Age-adjusted prevalence variant.

## Limitations
PLACES are modeled estimates. WONDER suppression leaves small counties without mortality. HPSA scores measure
designation, not utilization. Percentile gaps are relative to the chosen reference population.
