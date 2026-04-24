# Scatter Plot Testing: Business Questions

## Source Priority
Questions are selected from `scatter_spec.md` (chart-specific spec first).

## Selected Questions for Step 4
1. Which CBSAs have high income growth but comparatively low rent burden?
2. Which counties have unusually high home values relative to incomes?
3. Which ZCTAs are outliers within a given CBSA on rent vs income?

## Query Files (One per Question)
- `visual_library/charts/scatter/sample_sql/q1_cbsa_income_growth_vs_rent_burden.sql`
- `visual_library/charts/scatter/sample_sql/q2_county_home_value_vs_income.sql`
- `visual_library/charts/scatter/sample_sql/q3_zcta_rent_vs_income_outliers.sql`

## Notes
- Each SQL file uses a `params` CTE with documented constants at the top.
- Do not create persistent tables for sample testing.
- `test_scatter_render.R` should execute each query via DuckDB (`dbGetQuery`) and pass results into prep/render functions.
