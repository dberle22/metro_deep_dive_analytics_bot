# Choropleth Testing

## Canonical Questions
1. Where are the strongest spatial clusters on the active metric?
2. How does the target geography compare to nearby geographies?
3. What changes when the growth window changes?

## Notes
- The current test runner now uses live DuckDB-backed geometry for counties, CBSAs, and tracts.
- The local outlier question uses tract geometry as a temporary proxy until a ZCTA geometry layer is added.
- Review outputs:
  - `choropleth_q1_rent_burden_clusters.png`
  - `choropleth_q2_population_growth_corridors.png`
  - `choropleth_q3_affordability_outliers_within_cbsa.png`
  - `choropleth_q4_benchmark_relative_metros.png`
  - `choropleth_q5_growth_window_compare.png`
  - `choropleth_preset_national_compact_county.png`
  - `choropleth_preset_local_focus_atlanta.png`
  - `choropleth_preset_facet_national_growth.png`
