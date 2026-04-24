# Bar Chart Testing

## Canonical Questions
1. What are the top 25 CBSAs by 5-year per-capita income growth?
2. Which counties in Wilmington, NC (CBSA 48900) have the highest rent-to-income ratio?

## Notes
- Prefer gold-layer sources for ranking and affordability metrics.
- Sample SQL lives in `visual_library/charts/bar/sample_sql/build_bar_sample.sql`.
- Current canonical implementation uses:
- `gold.economics_income_wide` for `income_pc_growth_5yr`
- `gold.affordability_wide` for `rent_to_income`
- Deferred for a later pass:
- target-vs-peer highlighted ranking
- state benchmark-delta / diverging bar behavior
