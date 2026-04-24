# Boxplot Testing

## Canonical Questions
1. How does rent burden vary across regions, and where does the target CBSA fall?
2. For counties in the target CBSA, what is the distribution of median rent-to-income?
3. Within the target CBSA, do ZCTAs show a long tail of high commute intensity?
4. Are Sweet Spot markets outliers on affordability relative to all CBSAs?
5. How does the distribution of income growth differ by CBSA type?

## Output Files
- `boxplot_rent_burden_by_region`: visual_library/charts/boxplot/sample_output/boxplot_q1_rent_burden_by_region.png
- `boxplot_target_cbsa_county_rent_to_income`: visual_library/charts/boxplot/sample_output/boxplot_q2_target_cbsa_county_rent_to_income.png
- `boxplot_target_cbsa_zcta_commute_tail`: visual_library/charts/boxplot/sample_output/boxplot_q3_target_cbsa_zcta_commute_tail.png
- `boxplot_sweet_spot_affordability_outliers`: visual_library/charts/boxplot/sample_output/boxplot_q4_sweet_spot_affordability_outliers.png
- `boxplot_income_growth_by_cbsa_type`: visual_library/charts/boxplot/sample_output/boxplot_q5_income_growth_by_cbsa_type.png

## QA Notes
- Shared prep validates the boxplot contract, filters to the requested question, coerces numeric/logical fields, creates `box_group`, and orders groups by median by default.
- Shared render uses the visual-library theme, standard 1.5 IQR boxplot whiskers, optional jitter, shared benchmark helpers, and shared label helpers for highlighted geographies.
- The first sample set keeps boxplot-specific decisions local except for adding the shared boxplot contract and chart defaults.
- County and ZCTA examples intentionally use target markets with enough observations for distribution review.
