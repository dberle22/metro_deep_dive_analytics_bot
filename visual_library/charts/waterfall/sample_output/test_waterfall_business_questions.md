# Waterfall Testing

## Canonical Questions
1. What drove the change in personal income from 2013 to 2023 in the target CBSA?
2. How does the income component mix differ from a regional benchmark?
3. What components explain GDP change by major sector?
4. For housing stock change, what share came from single-unit vs multifamily additions?
5. Which components offset growth in the last 5 years for a target-market county?

## Output Files
- `waterfall_income_change_drivers`: visual_library/charts/waterfall/sample_output/waterfall_q1_income_change_drivers.png
- `waterfall_income_mix_compare`: visual_library/charts/waterfall/sample_output/waterfall_q2_income_mix_compare.png
- `waterfall_gdp_sector_change`: visual_library/charts/waterfall/sample_output/waterfall_q3_gdp_sector_change.png
- `waterfall_housing_stock_components`: visual_library/charts/waterfall/sample_output/waterfall_q4_housing_stock_components.png
- `waterfall_negative_offsets`: visual_library/charts/waterfall/sample_output/waterfall_q5_negative_offsets.png

## QA Notes
- Shared prep validates the waterfall contract, filters to the requested question, chooses delta vs level mode, creates running cumulative positions by waterfall group, and appends a terminal total bar.
- Shared render uses visual-library theme defaults, diverging positive/negative colors, total bars, connector lines, value labels, source/vintage captions, and optional facets for benchmark comparison.
- Component ordering follows `waterfall_decisions.md`: canonical logical order is preferred over magnitude sorting.
- Additive validation is checked after prep for every canonical question before rendering.
