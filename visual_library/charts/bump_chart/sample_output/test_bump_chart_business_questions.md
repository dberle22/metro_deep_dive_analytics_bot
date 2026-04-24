# Bump Chart Testing

## Canonical Questions
1. Which CBSAs moved into the top 10 for 5-year population growth?
2. Did the target CBSA improve in affordability rank since 2018?
3. Are the top performers stable or rotating?
4. Which counties within the CBSA rose fastest in rent-burden rank?
5. How did Sweet Spot markets shift in overheating risk rank over time?

## Output Files
- `bump_top10_growth`: visual_library/charts/bump_chart/sample_output/bump_top10_growth.png
- `bump_target_affordability_rank`: visual_library/charts/bump_chart/sample_output/bump_target_affordability_rank.png
- `bump_top_performer_stability`: visual_library/charts/bump_chart/sample_output/bump_top_performer_stability.png
- `bump_county_rent_burden_rank`: visual_library/charts/bump_chart/sample_output/bump_county_rent_burden_rank.png
- `bump_sweet_spot_overheating`: visual_library/charts/bump_chart/sample_output/bump_sweet_spot_overheating.png

## QA Notes
- Shared prep preserves raw `metric_value` and uses `rank` as the plotted value.
- Rank 1 is plotted at the top; upward movement means moving toward rank 1.
- Derived ranks use deterministic row-number ties: metric value, then geography name, then geography id.
- Fixed top-N samples compute ranks on the full query universe before trimming to the display set.
- The first PNG set is chart-local; no broad shared-standard changes were made.
