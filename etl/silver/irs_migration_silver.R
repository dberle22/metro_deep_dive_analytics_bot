# In this script we normalize IRS data into our Silver layer

# 1. Set up our Environment
# 2. Read in our Staging Data to R Data Frames
# 3. Build Final Tables
# 3.1. Add GEOID Metadata for Origin & Destinations
# 3.2. Standardize names
# 3.3. Recompute Metrics (CBSA)
# 4. Materialize to Silver

# Find our current directory 
getwd()

# 1. Set up our environment ----
# Read our common libraries & set other packages
source(here::here("scripts", "utils.R"))


# Set paths for our environments
# Make sure we're reading from the project Renviron
if (file.exists(".Renviron")) readRenviron(".Renviron")

# Set our Paths - Pointing to our Bronze folder in Data
data <- get_env_path("DATA")
db_path <- paste0(data, "/duckdb", "/metro_deep_dive.duckdb")

## Connect to the DB ----
con <- dbConnect(duckdb::duckdb(), dbdir = db_path, read_only = FALSE)

### List the tables available in the DB
tables <- dbListTables(con)
print(tables)

# 2. Read in our Staging Data to R Data Frames ----

## Metric Tables ----
county_inflow_raw <- dbGetQuery(con, "SELECT * FROM staging.irs_inflow_migration_county")
state_inflow_raw <- dbGetQuery(con, "SELECT * FROM staging.irs_inflow_migration_state")

## CBSA <> County Xwalk ----
cbsa_county_xwalk <- dbGetQuery(con, "SELECT * FROM silver.xwalk_cbsa_county")
county_state_xwalk <- dbGetQuery(con, "SELECT * FROM silver.xwalk_county_state")

# 3. Build Final Tables ----
## State ----

# Create State Geo ID Names 
state_names <- county_state_xwalk %>%
  select(state_fip, state_abbr) %>%
  unique()

# Add GEOID Names to DF & Standardize Columns
state_inflow <- state_inflow_raw %>%
  left_join(state_names %>% select(state_fip, origin_state_abbr = state_abbr),
            by = c("origin_state_fips" = "state_fip")) %>%
  left_join(state_names %>% select(state_fip, dest_state_abbr = state_abbr),
            by = c("dest_state_fips" = "state_fip")) %>%
  transmute(
    geo_level = "State",
    flow_id = flow_id,
    period = year,
    dest_year = dest_year,
    origin_year = origin_year,
    dest_geo_id = dest_state_fips,
    dest_state_name = dest_state_name,
    dest_state_abbr = dest_state_abbr,
    origin_geo_id = origin_state_fips,
    origin_state_fips = origin_state_abbr,
    n_returns = n_returns,
    n_people = n_exemptions,
    agi = agi,
    agi_thousands = agi_thousands
  )

## County ----
# Create County Geo ID Names 
county_names <- county_state_xwalk %>%
  select(state_fip, state_abbr, 
         county_fip, county_geoid, county_name = county_name_long) %>%
  unique()

# Add GEOID Names to DF & Standardize Columns
county_inflow <- county_inflow_raw %>%
  left_join(county_names %>% select(county_geoid, origin_state_abbr = state_abbr, origin_county_name = county_name),
            by = c("origin_geoid" = "county_geoid")) %>%
  left_join(county_names %>% select(county_geoid, dest_state_abbr = state_abbr, origin_county_name = county_name),
            by = c("dest_geoid" = "county_geoid")) %>%
  transmute(
    geo_level = "State",
    flow_id = flow_id,
    period = year,
    dest_year = dest_year,
    origin_year = origin_year,
    dest_geo_id = dest_state_fips,
    dest_state_name = dest_state_name,
    dest_state_abbr = dest_state_abbr,
    origin_geo_id = origin_state_fips,
    origin_state_fips = origin_state_abbr,
    n_returns = n_returns,
    n_people = n_exemptions,
    agi = agi,
    agi_thousands = agi_thousands
  )


