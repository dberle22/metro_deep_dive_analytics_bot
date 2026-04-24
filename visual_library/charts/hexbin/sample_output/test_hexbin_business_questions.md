# Hexbin Testing

## Canonical Questions
1. Where is the dense core of the distribution?
   Output: `hexbin_q1_affordability_density.png`
2. Are there multiple meaningful clusters or tails?
   Output: `hexbin_q2_growth_vs_burden_clusters.png`
3. What does the internal tradeoff shape look like inside a target CBSA?
   Output: `hexbin_q3_target_cbsa_tradeoff_shape.png`
4. How does the pattern differ across census regions?
   Output: `hexbin_q4_regional_density_compare.png`
5. How does the pattern change when weighted by population?
   Output: `hexbin_q5_population_weighted_tradeoff.png`

## Notes
- Gold-layer affordability and income marts are the preferred analytical base.
- Use highlighted-point overlays only for a very small labeled subset.
- Approved render set uses true `Hexbin` geometry via the installed `hexbin` package.
