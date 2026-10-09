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

## Data vintages used for the current build
- PLACES 2025 release (BRFSS 2023 based): county `swc5-untb`, tract `cwsq-ngmh`; hashes in `data/raw/manifest.json`.
- RUCA 2020 (tracts, 2020 tract vintage `TractFIPS20`, `PrimaryRUCA`); SVI 2022 (county and tract, `RPL_THEMES`);
  HRSA primary-care HPSA detail file (downloaded 2026-10-09; designated records only, all designation types in the
  file are geographic or population-group, and the maximum score per county is used).
- WONDER mortality: not yet included. Burden currently uses PLACES measures only.

## Coverage
- **Kentucky and Pennsylvania have no core-measure estimates in the PLACES 2025 release** (only five 2022 non-core
  measures), so all their counties and tracts are absent from the atlas rather than imputed. Loving County, TX is
  suppressed (population < 50). Result: 2,957 of 3,145 PLACES counties and 78,815 tracts are scored.
- Because of this, national percentiles are relative to the scored units only.

## Score construction
1. Each input is converted to a percentile rank in [0, 100] across all units at that level.
2. Burden: row mean of PLACES burden percentiles (needs at least half present), then weighted mean with the
   mortality percentile when available. Weights default to 1:1.
3. Capacity: row mean of preventive-care percentiles and inverted uninsured percentile, then weighted mean with the
   inverted HPSA percentile. Undesignated counties have HPSA score 0.
4. `gap_national` = percentile(burden) − percentile(capacity). `gap_stratum` ranks within RUCA stratum.
   `top_decile_gap` flags the top 10% of `gap_national`.
5. Missing inputs are never imputed. Units without enough inputs get NaN.

## Sensitivity analysis (`gapatlas sensitivity` -> `outputs/sensitivity_summary.csv`)
Each variant is compared with the default index by Spearman correlation of `gap_national` and by the Jaccard overlap
of the top-decile sets. Variants: HPSA, preventive-care and (when WONDER is present) mortality weights in
{0, 0.5, 2}; and leave-one-out of each of the six burden measures.

Findings on the current build (PLACES 2025, no WONDER), counties:
- Dropping any single burden measure leaves rankings nearly unchanged (rho >= 0.995, top-decile overlap 0.90-0.95).
- **The top decile is sensitive to HPSA.** Setting the HPSA weight to 0 keeps only 38% of the top-decile counties
  (rho 0.83); halving it keeps 72%; doubling it keeps 80%. Counties flagged only because of HPSA designation should
  be described as such, and the map should expose the HPSA-excluded ranking.
- Tracts have no HPSA input, so weight variants do not apply and only the leave-one-out rows are reported
  (rho >= 0.995, top-decile overlap 0.88-0.94).

## Planned
- Uncertainty propagation from PLACES confidence limits for tracts.
- Age-adjusted prevalence variant.

## Limitations
PLACES are modeled estimates. WONDER suppression leaves small counties without mortality. HPSA scores measure
designation, not utilization. Percentile gaps are relative to the chosen reference population.
