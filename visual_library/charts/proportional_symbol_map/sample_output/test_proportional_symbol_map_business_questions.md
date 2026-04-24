# Proportional Symbol Map Testing

## Canonical Questions
1. `bubble_population_concentration`
   - Output: `proportional_symbol_q1_population_concentration.png`
   - Question: Where is metro population most concentrated?
   - QA status: Pass for first review. Top-N filtering and limited labels make the national hierarchy readable.
2. `bubble_permit_majority_counties`
   - Output: `proportional_symbol_q2_permit_majority_counties.png`
   - Question: Which counties account for the largest share of new permitted units?
   - QA status: Pass for first review. The map uses total permitted units and highlights counties in the cumulative first half of units after ranking.
3. `bubble_largest_zctas_in_cbsa`
   - Output: `proportional_symbol_q3_largest_zctas_wilmington.png`
   - Question: Within a CBSA, where are the largest ZCTAs by population?
   - QA status: Pass with data caveat. ZCTA coordinates are tract-weighted approximations until a dedicated ZCTA geometry layer exists.
4. `bubble_retail_parcel_clusters`
   - Output: `proportional_symbol_q4_retail_parcel_cluster_proxy.png`
   - Question: Where are the largest retail parcel clusters?
   - QA status: Pass as a proxy only. Parcel-level clusters are not yet DuckDB-backed; this uses high-scoring Jacksonville tracts as the target-zone proxy.
5. `bubble_jobs_concentration`
   - Output: `proportional_symbol_q5_jobs_concentration_atlanta.png`
   - Question: How concentrated are jobs or establishments across counties?
   - QA status: Pass as a proxy. The current sample uses employed residents from `gold.economics_labor_wide` until workplace establishment totals are available.

## Notes
- Prefer explicit coordinates or reproducible centroid derivation.
- Use Top N filtering in broad national views to reduce clutter.
- Size uses area-based scaling through the shared renderer so radius grows perceptually rather than linearly.
- National maps reuse the choropleth family context layers and `national_compact` composition preset.
- Local maps use `local_focus` framing with county context boundaries.

## Visual QA Findings
- high: None in the current render set.
- medium: Parcel and jobs examples are semantically useful proxies but should be swapped to parcel-cluster and workplace-establishment totals once those are materialized.
- low: Dense coastal permit markets still overlap by design; labels are restricted to top-ranked geographies to preserve the spatial concentration read.
