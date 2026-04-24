# Highlight + Context Map Testing

## Canonical Questions
1. Where is the target geography and what surrounds it?
   Output: `highlight_context_q1_target_locator.png`
2. Which small areas within the target market read as affordability outliers?
   Output: `highlight_context_q2_target_outlier_proxy.png`
3. Are neighboring counties experiencing similar growth patterns?
   Output: `highlight_context_q3_neighbor_growth.png`
4. How does the target compare to adjacent counties on rent burden?
   Output: `highlight_context_q4_adjacent_rent_burden.png`
5. Which shortlisted markets cluster geographically, and which are isolated?
   Output: `highlight_context_q5_shortlist_geography.png`

## Notes
- The current runner uses live DuckDB-backed geometry for CBSA, county, and tract views.
- The local outlier question still uses tract geometry as the proxy until a reviewable ZCTA geometry layer is added.
- Review the focus layer separately from the background metric: the map should make the target obvious before the metric interpretation begins.
