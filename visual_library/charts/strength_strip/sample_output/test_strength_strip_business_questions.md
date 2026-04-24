# Strength Strip Testing

## Canonical Questions
1. What is Wilmington, NC's KPI profile versus the national CBSA universe?
2. Which KPI dimensions are strengths or weaknesses versus nearby South Atlantic peers when benchmarked against the full South Atlantic CBSA universe?
3. Which KPIs are dragging down the target versus the national CBSA median?
4. How does Wilmington's profile differ between 2023 levels and 2018-2023 growth windows?
5. Which county inside the Wilmington CBSA has the strongest overall profile when benchmarked against the full South Atlantic county universe?

## Output Files
- `strip_cbsa_profile`: visual_library/charts/strength_strip/sample_output/strength_strip_q1_cbsa_profile.png
- `strip_target_vs_peers`: visual_library/charts/strength_strip/sample_output/strength_strip_q2_target_vs_peers.png
- `strip_score_driver_scan`: visual_library/charts/strength_strip/sample_output/strength_strip_q3_score_driver_scan.png
- `strip_level_vs_growth_compare`: visual_library/charts/strength_strip/sample_output/strength_strip_q4_level_vs_growth_compare.png
- `strip_county_profile_compare`: visual_library/charts/strength_strip/sample_output/strength_strip_q5_county_profile_compare.png

## QA Notes
- Shared prep applies percentile normalization within each metric and time window, with polarity inversion for lower-is-better KPIs.
- The score-driver sample includes a benchmark tick for the national CBSA median on each KPI row.
- The peer and county comparison samples normalize against broad South Atlantic universes, then display only the compact comparison sets.
