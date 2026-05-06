-- gold.benchmark_reference view
--
-- Pre-aggregated benchmark values for US, Census region, and Census division.
-- Used by the benchmark SQL template to supply reliable reference values without
-- an inline aggregate that can fail for tables lacking high-level geo rows.
--
-- Sources:
--   population_demographics : reads existing us/region/division rows directly.
--   housing_core_wide        : reads existing us/region/division rows directly.
--   economics_income_wide    : aggregates from state-level rows (unweighted average)
--                              joined to silver.xwalk_state_region for region/division.
--
-- Note: economics_income_wide aggregates are unweighted state averages, not
-- population-weighted national figures. Suitable for directional benchmarks.

CREATE OR REPLACE VIEW gold.benchmark_reference AS

WITH pop_ref AS (
  SELECT geo_level, geo_id, geo_name, year,
    pop_total, pop_growth_1yr, pop_growth_3yr, pop_growth_5yr,
    median_age, pct_age_under_18, pct_age_over_64, dependents_per_worker,
    pct_hispanic, diversity_index, pct_ba_plus
  FROM gold.population_demographics
  WHERE geo_level IN ('us', 'region', 'division')
),

pop_state AS (
  SELECT
    p.geo_id,
    p.year,
    x.census_region,
    x.census_division,
    p.pop_total
  FROM gold.population_demographics p
  INNER JOIN silver.xwalk_state_region x
    ON p.geo_id = x.state_fips
  WHERE p.geo_level = 'state'
    AND p.pop_total IS NOT NULL
),

pop_total_ref AS (
  SELECT geo_level AS benchmark_level, geo_id AS benchmark_geo_id, geo_name AS benchmark_label, year, CAST(pop_total AS DOUBLE) AS metric_value
  FROM pop_ref
  WHERE pop_total IS NOT NULL

  UNION ALL

  SELECT 'us', 'us', 'United States', year, CAST(SUM(pop_total) AS DOUBLE)
  FROM pop_state
  WHERE NOT EXISTS (
    SELECT 1
    FROM pop_ref existing
    WHERE existing.geo_level = 'us'
      AND existing.year = pop_state.year
      AND existing.pop_total IS NOT NULL
  )
  GROUP BY year

  UNION ALL

  SELECT 'region', census_region, census_region, year, CAST(SUM(pop_total) AS DOUBLE)
  FROM pop_state
  WHERE NOT EXISTS (
    SELECT 1
    FROM pop_ref existing
    WHERE existing.geo_level = 'region'
      AND existing.geo_id = pop_state.census_region
      AND existing.year = pop_state.year
      AND existing.pop_total IS NOT NULL
  )
  GROUP BY census_region, year

  UNION ALL

  SELECT 'division', census_division, census_division, year, CAST(SUM(pop_total) AS DOUBLE)
  FROM pop_state
  WHERE NOT EXISTS (
    SELECT 1
    FROM pop_ref existing
    WHERE existing.geo_level = 'division'
      AND existing.geo_id = pop_state.census_division
      AND existing.year = pop_state.year
      AND existing.pop_total IS NOT NULL
  )
  GROUP BY census_division, year
),

housing_ref AS (
  SELECT geo_level, geo_id, geo_name, year,
    hu_total, vacancy_rate, owner_occ_rate, renter_occ_rate,
    median_gross_rent, annualized_median_rent, median_home_value,
    pct_rent_burden_30plus, rent_to_income, value_to_income
  FROM gold.housing_core_wide
  WHERE geo_level IN ('us', 'region', 'division')
),

-- economics_income_wide has no us/region/division rows; aggregate from state level.
income_state AS (
  SELECT
    e.geo_id,
    e.year,
    x.census_region,
    x.census_division,
    e.median_hh_income,
    e.acs_income_pc,
    e.pov_rate,
    e.gini_index,
    e.pi_total,
    e.calc_income_pc,
    e.income_pc_growth_1yr,
    e.income_pc_growth_5yr,
    e.income_pc_cagr_5yr,
    e.pi_wage_share
  FROM gold.economics_income_wide e
  INNER JOIN silver.xwalk_state_region x
    ON e.geo_id = x.state_fips
  WHERE e.geo_level = 'state'
)

-- ── population_demographics ───────────────────────────────────────────────────
SELECT benchmark_level, benchmark_geo_id, benchmark_label, 'population_demographics' AS source_table, 'pop_total'             AS metric_id, year, metric_value FROM pop_total_ref UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pop_growth_1yr',          year, CAST(pop_growth_1yr          AS DOUBLE) FROM pop_ref WHERE pop_growth_1yr          IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pop_growth_3yr',          year, CAST(pop_growth_3yr          AS DOUBLE) FROM pop_ref WHERE pop_growth_3yr          IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pop_growth_5yr',          year, CAST(pop_growth_5yr          AS DOUBLE) FROM pop_ref WHERE pop_growth_5yr          IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'median_age',              year, CAST(median_age              AS DOUBLE) FROM pop_ref WHERE median_age              IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pct_age_under_18',        year, CAST(pct_age_under_18        AS DOUBLE) FROM pop_ref WHERE pct_age_under_18        IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pct_age_over_64',         year, CAST(pct_age_over_64         AS DOUBLE) FROM pop_ref WHERE pct_age_over_64         IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'dependents_per_worker',   year, CAST(dependents_per_worker   AS DOUBLE) FROM pop_ref WHERE dependents_per_worker   IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pct_hispanic',            year, CAST(pct_hispanic            AS DOUBLE) FROM pop_ref WHERE pct_hispanic            IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'diversity_index',         year, CAST(diversity_index         AS DOUBLE) FROM pop_ref WHERE diversity_index         IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'population_demographics', 'pct_ba_plus',             year, CAST(pct_ba_plus             AS DOUBLE) FROM pop_ref WHERE pct_ba_plus             IS NOT NULL

UNION ALL

-- ── housing_core_wide ─────────────────────────────────────────────────────────
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'hu_total',                    year, CAST(hu_total                    AS DOUBLE) FROM housing_ref WHERE hu_total                    IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'vacancy_rate',               year, CAST(vacancy_rate               AS DOUBLE) FROM housing_ref WHERE vacancy_rate               IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'owner_occ_rate',             year, CAST(owner_occ_rate             AS DOUBLE) FROM housing_ref WHERE owner_occ_rate             IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'renter_occ_rate',            year, CAST(renter_occ_rate            AS DOUBLE) FROM housing_ref WHERE renter_occ_rate            IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'median_gross_rent',          year, CAST(median_gross_rent          AS DOUBLE) FROM housing_ref WHERE median_gross_rent          IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'annualized_median_rent',     year, CAST(annualized_median_rent     AS DOUBLE) FROM housing_ref WHERE annualized_median_rent     IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'median_home_value',          year, CAST(median_home_value          AS DOUBLE) FROM housing_ref WHERE median_home_value          IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'pct_rent_burden_30plus',     year, CAST(pct_rent_burden_30plus     AS DOUBLE) FROM housing_ref WHERE pct_rent_burden_30plus     IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'rent_to_income',             year, CAST(rent_to_income             AS DOUBLE) FROM housing_ref WHERE rent_to_income             IS NOT NULL UNION ALL
SELECT geo_level, geo_id, geo_name, 'housing_core_wide', 'value_to_income',            year, CAST(value_to_income            AS DOUBLE) FROM housing_ref WHERE value_to_income            IS NOT NULL

UNION ALL

-- ── economics_income_wide — US ────────────────────────────────────────────────
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'median_hh_income',      year, AVG(median_hh_income)      FROM income_state WHERE median_hh_income      IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'acs_income_pc',         year, AVG(acs_income_pc)         FROM income_state WHERE acs_income_pc         IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'pov_rate',              year, AVG(pov_rate)              FROM income_state WHERE pov_rate              IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'gini_index',            year, AVG(gini_index)            FROM income_state WHERE gini_index            IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'pi_total',              year, AVG(pi_total)              FROM income_state WHERE pi_total              IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'calc_income_pc',        year, AVG(calc_income_pc)        FROM income_state WHERE calc_income_pc        IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'income_pc_growth_1yr',  year, AVG(income_pc_growth_1yr)  FROM income_state WHERE income_pc_growth_1yr  IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'income_pc_growth_5yr',  year, AVG(income_pc_growth_5yr)  FROM income_state WHERE income_pc_growth_5yr  IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'income_pc_cagr_5yr',    year, AVG(income_pc_cagr_5yr)    FROM income_state WHERE income_pc_cagr_5yr    IS NOT NULL GROUP BY year UNION ALL
SELECT 'us', 'us', 'United States', 'economics_income_wide', 'pi_wage_share',         year, AVG(pi_wage_share)         FROM income_state WHERE pi_wage_share         IS NOT NULL GROUP BY year

UNION ALL

-- ── economics_income_wide — Census region ─────────────────────────────────────
SELECT 'region', census_region, census_region, 'economics_income_wide', 'median_hh_income',      year, AVG(median_hh_income)      FROM income_state WHERE median_hh_income      IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'acs_income_pc',         year, AVG(acs_income_pc)         FROM income_state WHERE acs_income_pc         IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'pov_rate',              year, AVG(pov_rate)              FROM income_state WHERE pov_rate              IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'gini_index',            year, AVG(gini_index)            FROM income_state WHERE gini_index            IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'pi_total',              year, AVG(pi_total)              FROM income_state WHERE pi_total              IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'calc_income_pc',        year, AVG(calc_income_pc)        FROM income_state WHERE calc_income_pc        IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'income_pc_growth_1yr',  year, AVG(income_pc_growth_1yr)  FROM income_state WHERE income_pc_growth_1yr  IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'income_pc_growth_5yr',  year, AVG(income_pc_growth_5yr)  FROM income_state WHERE income_pc_growth_5yr  IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'income_pc_cagr_5yr',    year, AVG(income_pc_cagr_5yr)    FROM income_state WHERE income_pc_cagr_5yr    IS NOT NULL GROUP BY census_region, year UNION ALL
SELECT 'region', census_region, census_region, 'economics_income_wide', 'pi_wage_share',         year, AVG(pi_wage_share)         FROM income_state WHERE pi_wage_share         IS NOT NULL GROUP BY census_region, year

UNION ALL

-- ── economics_income_wide — Census division ───────────────────────────────────
SELECT 'division', census_division, census_division, 'economics_income_wide', 'median_hh_income',      year, AVG(median_hh_income)      FROM income_state WHERE median_hh_income      IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'acs_income_pc',         year, AVG(acs_income_pc)         FROM income_state WHERE acs_income_pc         IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'pov_rate',              year, AVG(pov_rate)              FROM income_state WHERE pov_rate              IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'gini_index',            year, AVG(gini_index)            FROM income_state WHERE gini_index            IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'pi_total',              year, AVG(pi_total)              FROM income_state WHERE pi_total              IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'calc_income_pc',        year, AVG(calc_income_pc)        FROM income_state WHERE calc_income_pc        IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'income_pc_growth_1yr',  year, AVG(income_pc_growth_1yr)  FROM income_state WHERE income_pc_growth_1yr  IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'income_pc_growth_5yr',  year, AVG(income_pc_growth_5yr)  FROM income_state WHERE income_pc_growth_5yr  IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'income_pc_cagr_5yr',    year, AVG(income_pc_cagr_5yr)    FROM income_state WHERE income_pc_cagr_5yr    IS NOT NULL GROUP BY census_division, year UNION ALL
SELECT 'division', census_division, census_division, 'economics_income_wide', 'pi_wage_share',         year, AVG(pi_wage_share)         FROM income_state WHERE pi_wage_share         IS NOT NULL GROUP BY census_division, year
;
