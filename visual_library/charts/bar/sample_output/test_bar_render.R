# Bar chart render tests with question-specific DuckDB queries.

if (file.exists(".Renviron")) readRenviron(".Renviron")

source("visual_library/shared/standards.R")
source("visual_library/shared/data_contracts.R")
source("visual_library/shared/scatter_query_helpers.R")
source("visual_library/shared/prep/prep_bar.R")
source("visual_library/shared/render/render_bar.R")

sql_string <- function(con, value) {
  as.character(DBI::dbQuoteString(con, value))
}

run_bar_query <- function(con, sql) {
  DBI::dbGetQuery(con, sql)
}

assert_bar_contract <- function(data, question_id) {
  validation <- validate_bar_contract(data)
  if (isTRUE(validation$pass)) {
    return(invisible(validation))
  }

  stop(
    sprintf(
      "Bar contract validation failed for %s. Missing required: %s. Rows: %s",
      question_id,
      paste(validation$missing_required, collapse = ", "),
      validation$rows
    )
  )
}

bar_sql_top_growth_cbsas <- function(con) {
  target_geo_id <- sql_string(con, "48900")
  vintage <- sql_string(con, format(Sys.Date(), "%Y-%m-%d"))

  paste(
    "WITH target_cbsa AS (",
    paste0("  SELECT ", target_geo_id, " AS target_geo_id"),
    "),",
    "latest_cbsa_growth_year AS (",
    "  SELECT MAX(year) AS year",
    "  FROM metro_deep_dive.gold.economics_income_wide",
    "  WHERE geo_level = 'cbsa'",
    "    AND income_pc_growth_5yr IS NOT NULL",
    "),",
    "cbsa_division_lookup AS (",
    "  SELECT",
    "    c.cbsa_code AS geo_id,",
    "    s.census_division AS division,",
    "    ROW_NUMBER() OVER (PARTITION BY c.cbsa_code ORDER BY c.county_geoid) AS rn",
    "  FROM metro_deep_dive.silver.xwalk_cbsa_county c",
    "  LEFT JOIN metro_deep_dive.silver.xwalk_state_region s",
    "    ON c.state_fips = s.state_fips",
    "),",
    "cbsa_division_dedup AS (",
    "  SELECT geo_id, division",
    "  FROM cbsa_division_lookup",
    "  WHERE rn = 1",
    ")",
    "SELECT",
    "  'bar_top_growth_cbsas' AS question_id,",
    "  i.geo_level,",
    "  i.geo_id,",
    "  i.geo_name,",
    "  CONCAT(CAST(i.year - 5 AS VARCHAR), '_to_', CAST(i.year AS VARCHAR), '_growth') AS time_window,",
    "  'income_pc_growth_5yr' AS metric_id,",
    "  '5-Year Per Capita Income Growth' AS metric_label,",
    "  i.income_pc_growth_5yr AS metric_value,",
    "  'gold.economics_income_wide' AS source,",
    paste0("  ", vintage, " AS vintage,"),
    "  ROW_NUMBER() OVER (ORDER BY i.income_pc_growth_5yr DESC, i.geo_name) AS rank,",
    "  d.division AS \"group\",",
    "  NULL::VARCHAR AS series,",
    "  NULL::DOUBLE AS share_value,",
    "  i.geo_id = (SELECT target_geo_id FROM target_cbsa) AS highlight_flag,",
    "  NULL::DOUBLE AS benchmark_value,",
    "  'Top-25 display is applied in prep_bar().' AS note",
    "FROM metro_deep_dive.gold.economics_income_wide i",
    "LEFT JOIN cbsa_division_dedup d",
    "  ON i.geo_id = d.geo_id",
    "WHERE i.geo_level = 'cbsa'",
    "  AND i.year = (SELECT year FROM latest_cbsa_growth_year)",
    "  AND i.income_pc_growth_5yr IS NOT NULL",
    "ORDER BY rank, geo_name",
    collapse = "\n"
  )
}

bar_sql_county_affordability <- function(con) {
  target_geo_id <- sql_string(con, "48900")
  vintage <- sql_string(con, format(Sys.Date(), "%Y-%m-%d"))

  paste(
    "WITH target_cbsa AS (",
    paste0("  SELECT ", target_geo_id, " AS target_geo_id"),
    "),",
    "latest_target_county_year AS (",
    "  SELECT MAX(a.year) AS year",
    "  FROM metro_deep_dive.gold.affordability_wide a",
    "  JOIN metro_deep_dive.silver.xwalk_cbsa_county x",
    "    ON a.geo_id = x.county_geoid",
    "  JOIN target_cbsa t",
    "    ON x.cbsa_code = t.target_geo_id",
    "  WHERE a.geo_level = 'county'",
    "    AND a.annualized_median_rent IS NOT NULL",
    "    AND a.median_hh_income IS NOT NULL",
    "    AND a.median_hh_income <> 0",
    ")",
    "SELECT",
    "  'bar_county_affordability' AS question_id,",
    "  a.geo_level,",
    "  a.geo_id,",
    "  a.geo_name,",
    "  CONCAT(CAST(a.year AS VARCHAR), '_snapshot') AS time_window,",
    "  'rent_to_income' AS metric_id,",
    "  'Annualized Median Rent as % of Median Household Income' AS metric_label,",
    "  a.annualized_median_rent / a.median_hh_income AS metric_value,",
    "  'gold.affordability_wide' AS source,",
    paste0("  ", vintage, " AS vintage,"),
    "  ROW_NUMBER() OVER (ORDER BY a.annualized_median_rent / a.median_hh_income DESC, a.geo_name) AS rank,",
    "  'Wilmington, NC counties' AS \"group\",",
    "  NULL::VARCHAR AS series,",
    "  NULL::DOUBLE AS share_value,",
    "  FALSE AS highlight_flag,",
    "  NULL::DOUBLE AS benchmark_value,",
    "  NULL::VARCHAR AS note",
    "FROM metro_deep_dive.gold.affordability_wide a",
    "JOIN metro_deep_dive.silver.xwalk_cbsa_county x",
    "  ON a.geo_id = x.county_geoid",
    "JOIN target_cbsa t",
    "  ON x.cbsa_code = t.target_geo_id",
    "WHERE a.geo_level = 'county'",
    "  AND a.year = (SELECT year FROM latest_target_county_year)",
    "  AND a.annualized_median_rent IS NOT NULL",
    "  AND a.median_hh_income IS NOT NULL",
    "  AND a.median_hh_income <> 0",
    "ORDER BY rank, geo_name",
    collapse = "\n"
  )
}

bar_sql_target_vs_peers <- function(con) {
  target_geo_id <- sql_string(con, "48900")
  vintage <- sql_string(con, format(Sys.Date(), "%Y-%m-%d"))

  paste(
    "WITH target_cbsa AS (",
    paste0("  SELECT ", target_geo_id, " AS target_geo_id"),
    "),",
    "target_division AS (",
    "  SELECT",
    "    x.cbsa_code AS geo_id,",
    "    MIN(s.census_division) AS census_division",
    "  FROM metro_deep_dive.silver.xwalk_cbsa_county x",
    "  LEFT JOIN metro_deep_dive.silver.xwalk_state_region s",
    "    ON x.state_fips = s.state_fips",
    "  WHERE x.cbsa_code = (SELECT target_geo_id FROM target_cbsa)",
    "  GROUP BY 1",
    "),",
    "cbsa_division_lookup AS (",
    "  SELECT",
    "    x.cbsa_code AS geo_id,",
    "    MIN(s.census_division) AS census_division",
    "  FROM metro_deep_dive.silver.xwalk_cbsa_county x",
    "  LEFT JOIN metro_deep_dive.silver.xwalk_state_region s",
    "    ON x.state_fips = s.state_fips",
    "  GROUP BY 1",
    "),",
    "latest_cbsa_affordability_year AS (",
    "  SELECT MAX(year) AS year",
    "  FROM metro_deep_dive.gold.affordability_wide",
    "  WHERE geo_level = 'cbsa'",
    "    AND annualized_median_rent IS NOT NULL",
    "    AND median_hh_income IS NOT NULL",
    "    AND median_hh_income <> 0",
    ")",
    "SELECT",
    "  'bar_target_vs_peers' AS question_id,",
    "  a.geo_level,",
    "  a.geo_id,",
    "  a.geo_name,",
    "  CONCAT(CAST(a.year AS VARCHAR), '_snapshot') AS time_window,",
    "  'rent_to_income' AS metric_id,",
    "  'Annualized Median Rent as % of Median Household Income' AS metric_label,",
    "  a.annualized_median_rent / a.median_hh_income AS metric_value,",
    "  'gold.affordability_wide' AS source,",
    paste0("  ", vintage, " AS vintage,"),
    "  ROW_NUMBER() OVER (ORDER BY a.annualized_median_rent / a.median_hh_income DESC, a.geo_name) AS rank,",
    "  l.census_division AS \"group\",",
    "  NULL::VARCHAR AS series,",
    "  NULL::DOUBLE AS share_value,",
    "  a.geo_id = (SELECT target_geo_id FROM target_cbsa) AS highlight_flag,",
    "  NULL::DOUBLE AS benchmark_value,",
    "  'Target CBSA is retained even if it falls outside the display cutoff.' AS note",
    "FROM metro_deep_dive.gold.affordability_wide a",
    "JOIN cbsa_division_lookup l",
    "  ON a.geo_id = l.geo_id",
    "JOIN target_division d",
    "  ON l.census_division = d.census_division",
    "WHERE a.geo_level = 'cbsa'",
    "  AND a.year = (SELECT year FROM latest_cbsa_affordability_year)",
    "  AND a.annualized_median_rent IS NOT NULL",
    "  AND a.median_hh_income IS NOT NULL",
    "  AND a.median_hh_income <> 0",
    "ORDER BY rank, geo_name",
    collapse = "\n"
  )
}

bar_sql_state_benchmark_delta <- function(con) {
  vintage <- sql_string(con, format(Sys.Date(), "%Y-%m-%d"))

  paste(
    "WITH latest_state_year AS (",
    "  SELECT MAX(year) AS year",
    "  FROM metro_deep_dive.gold.affordability_wide",
    "  WHERE geo_level = 'state'",
    "    AND rpp_real_pc_income IS NOT NULL",
    "),",
    "state_benchmark AS (",
    "  SELECT",
    "    year,",
    "    AVG(rpp_real_pc_income) AS national_state_avg_real_pc_income",
    "  FROM metro_deep_dive.gold.affordability_wide",
    "  WHERE geo_level = 'state'",
    "    AND year = (SELECT year FROM latest_state_year)",
    "    AND rpp_real_pc_income IS NOT NULL",
    "  GROUP BY 1",
    "),",
    "state_region AS (",
    "  SELECT DISTINCT",
    "    state_fips AS geo_id,",
    "    census_region",
    "  FROM metro_deep_dive.silver.xwalk_state_region",
    ")",
    "SELECT",
    "  'bar_state_benchmark_delta' AS question_id,",
    "  a.geo_level,",
    "  a.geo_id,",
    "  a.geo_name,",
    "  CONCAT(CAST(a.year AS VARCHAR), '_snapshot_vs_national_state_avg') AS time_window,",
    "  'rpp_real_pc_income_delta_vs_national_state_avg' AS metric_id,",
    "  'Real Per Capita Income Gap vs National State Average' AS metric_label,",
    "  a.rpp_real_pc_income - b.national_state_avg_real_pc_income AS metric_value,",
    "  'gold.affordability_wide' AS source,",
    paste0("  ", vintage, " AS vintage,"),
    "  ROW_NUMBER() OVER (ORDER BY ABS(a.rpp_real_pc_income - b.national_state_avg_real_pc_income) DESC, a.geo_name) AS rank,",
    "  r.census_region AS \"group\",",
    "  NULL::VARCHAR AS series,",
    "  NULL::DOUBLE AS share_value,",
    "  FALSE AS highlight_flag,",
    "  0.0 AS benchmark_value,",
    "  CONCAT('Benchmark is the latest unweighted state average real per-capita income: $', CAST(ROUND(b.national_state_avg_real_pc_income, 0) AS VARCHAR)) AS note",
    "FROM metro_deep_dive.gold.affordability_wide a",
    "CROSS JOIN state_benchmark b",
    "LEFT JOIN state_region r",
    "  ON a.geo_id = r.geo_id",
    "WHERE a.geo_level = 'state'",
    "  AND a.year = (SELECT year FROM latest_state_year)",
    "  AND a.rpp_real_pc_income IS NOT NULL",
    "ORDER BY rank, geo_name",
    collapse = "\n"
  )
}

save_bar_plot <- function(plot, output_dir, filename, width, height) {
  path <- file.path(output_dir, filename)
  ggplot2::ggsave(path, plot = plot, width = width, height = height, dpi = 300, bg = "white")
  path
}

run_bar_tests <- function() {
  output_dir <- "visual_library/charts/bar/sample_output"
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  con <- connect_metro_duckdb(read_only = TRUE)
  on.exit(DBI::dbDisconnect(con, shutdown = TRUE), add = TRUE)

  outputs <- c()

  sql_top_growth <- bar_sql_top_growth_cbsas(con)
  raw_top_growth <- run_bar_query(con, sql_top_growth)
  assert_bar_contract(raw_top_growth, "bar_top_growth_cbsas")
  top_growth_df <- prep_bar(
    raw_top_growth,
    config = list(
      question_id = "bar_top_growth_cbsas",
      metric_id = "income_pc_growth_5yr",
      top_n = 25
    )
  )
  top_growth_plot <- render_bar(
    top_growth_df,
    config = list(
      output_mode = "presentation",
      title = "Top 25 CBSAs by 5-year per-capita income growth",
      subtitle = "Latest CBSA snapshot | Ranked nationally by income growth over the trailing 5-year window",
      y_label = "5-year growth (%)",
      label_style = "percent",
      label_accuracy = 0.1,
      caption_side_note = "National CBSA comparison.",
      caption_footer_note = "Top 25 shown."
    )
  )
  outputs["bar_top_growth_cbsas"] <- save_bar_plot(
    top_growth_plot,
    output_dir,
    "bar_top_growth_cbsas.png",
    width = 11,
    height = 8
  )

  sql_county_affordability <- bar_sql_county_affordability(con)
  raw_county_affordability <- run_bar_query(con, sql_county_affordability)
  assert_bar_contract(raw_county_affordability, "bar_county_affordability")
  county_affordability_df <- prep_bar(
    raw_county_affordability,
    config = list(
      question_id = "bar_county_affordability",
      metric_id = "rent_to_income"
    )
  )
  county_affordability_plot <- render_bar(
    county_affordability_df,
    config = list(
      output_mode = "presentation",
      title = "Which Wilmington-area counties face the highest rent burden?",
      subtitle = "2024 county snapshot within CBSA 48900 | Sorted by annualized median rent as a share of household income",
      y_label = "Rent-to-income (%)",
      label_style = "percent",
      label_accuracy = 0.1,
      caption_side_note = "County comparison within the Wilmington, NC metro."
    )
  )
  outputs["bar_county_affordability"] <- save_bar_plot(
    county_affordability_plot,
    output_dir,
    "bar_county_affordability.png",
    width = 11,
    height = 7
  )

  sql_target_vs_peers <- bar_sql_target_vs_peers(con)
  raw_target_vs_peers <- run_bar_query(con, sql_target_vs_peers)
  assert_bar_contract(raw_target_vs_peers, "bar_target_vs_peers")
  target_vs_peers_df <- prep_bar(
    raw_target_vs_peers,
    config = list(
      question_id = "bar_target_vs_peers",
      metric_id = "rent_to_income",
      top_n = 15,
      include_geo_ids = "48900",
      include_highlighted = TRUE
    )
  )
  target_vs_peers_plot <- render_bar(
    target_vs_peers_df,
    config = list(
      output_mode = "presentation",
      title = "How Wilmington, NC ranks on rent burden against South Atlantic peers",
      subtitle = "2024 CBSA snapshot | South Atlantic division metros | Wilmington highlighted",
      y_label = "Rent-to-income (%)",
      label_style = "percent",
      label_accuracy = 0.1,
      caption_side_note = "Display keeps the selected metro even if it falls outside the top-15 cutoff."
    )
  )
  outputs["bar_target_vs_peers"] <- save_bar_plot(
    target_vs_peers_plot,
    output_dir,
    "bar_target_vs_peers.png",
    width = 11,
    height = 8
  )

  sql_state_benchmark_delta <- bar_sql_state_benchmark_delta(con)
  raw_state_benchmark_delta <- run_bar_query(con, sql_state_benchmark_delta)
  assert_bar_contract(raw_state_benchmark_delta, "bar_state_benchmark_delta")
  state_benchmark_delta_df <- prep_bar(
    raw_state_benchmark_delta,
    config = list(
      question_id = "bar_state_benchmark_delta",
      metric_id = "rpp_real_pc_income_delta_vs_national_state_avg",
      top_n = 20,
      sort_by = "abs_metric_value"
    )
  )
  state_benchmark_delta_plot <- render_bar(
    state_benchmark_delta_df,
    config = list(
      output_mode = "presentation",
      title = "Which states diverge most from the national state-average income benchmark?",
      subtitle = "Latest state snapshot with non-null real income | Bars show real per-capita income minus the latest cross-state average",
      y_label = "Income gap vs national state average",
      label_style = "dollar",
      label_accuracy = 1,
      bar_variant = "diverging",
      show_benchmark = TRUE,
      benchmark_value = 0,
      benchmark_label = "National state average",
      legend_position = "bottom",
      axis_expand_upper = 0.22,
      right_margin_pt = 28,
      caption_side_note = "Positive values are above the latest state-average benchmark and negative values are below it.",
      highlight_legend = TRUE
    )
  )
  outputs["bar_state_benchmark_delta"] <- save_bar_plot(
    state_benchmark_delta_plot,
    output_dir,
    "bar_state_benchmark_delta.png",
    width = 11,
    height = 8.5
  )

  outputs
}

outputs <- run_bar_tests()
print(outputs)
