# Heatmap Table Testing

## Canonical Questions
1. Across the tract shortlist, which places are consistently strong across income, talent, housing headroom, and affordability guardrails?
2. For counties in the target CBSA, which dimensions are strongest versus weakest?
3. For selected peer CBSAs, what does the full KPI profile look like in one scannable matrix?
4. For rent burden, which ZCTAs show persistent stress across years?
5. Which metrics improved most in the target CBSA from 2013 to 2023?

## Output Files
- `heatmap_shortlist_scan`: visual_library/charts/heatmap_table/sample_output/heatmap_table_q1_shortlist_scan.png
- `heatmap_county_dimension_compare`: visual_library/charts/heatmap_table/sample_output/heatmap_table_q2_county_dimension_compare.png
- `heatmap_peer_cbsa_profile`: visual_library/charts/heatmap_table/sample_output/heatmap_table_q3_peer_cbsa_profile.png
- `heatmap_zcta_persistent_stress`: visual_library/charts/heatmap_table/sample_output/heatmap_table_q4_zcta_persistent_stress.png
- `heatmap_target_metric_improvement`: visual_library/charts/heatmap_table/sample_output/heatmap_table_q5_target_metric_improvement.png

## QA Notes
- Shared prep keeps raw `metric_value` for labels and uses `normalized_value`/`fill_value` for color.
- Multi-metric samples apply percentile normalization within each metric and time window, with lower-is-better metrics inverted before coloring.
- Missing matrix cells are completed by prep and labeled as `No data` instead of being silently dropped.
- The first PNG set is intentionally chart-local; no broad shared-standard changes were made.
