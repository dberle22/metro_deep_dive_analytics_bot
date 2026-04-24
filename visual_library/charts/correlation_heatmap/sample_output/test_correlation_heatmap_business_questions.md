# Correlation Heatmap Testing

## Canonical Questions
1. Which metrics appear redundant?
   Output: `correlation_heatmap_q1_redundant_kpis.png`
2. Do growth and level metrics cluster separately?
   Output: `correlation_heatmap_q2_growth_vs_level_blocks.png`
3. Is rent burden more associated with income or supply indicators?
   Output: `correlation_heatmap_q3_rent_burden_driver_scan.png`
4. How does the structure differ for Sweet Spot markets?
   Output: `correlation_heatmap_q4_sweet_spot_compare.png`
5. Within a CBSA's counties, which housing indicators co-move most?
   Output: `correlation_heatmap_q5_county_within_cbsa.png`

## Notes
- Keep each KPI set intentionally small enough for reviewable labels and stable clustered ordering.
- Spearman with pairwise-complete handling is the default smoke-test path unless a stricter policy is stated.
- The Sweet Spot comparison currently uses a documented derived shortlist because the warehouse does not expose a canonical Sweet Spot flag yet.
