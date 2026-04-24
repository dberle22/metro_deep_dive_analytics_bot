# 0) One-time: set an env var so all projects share the same data home
#    Put this in ~/.Renviron for persistence:
# DATA_HOME=/Users/you/DataHub

library(DBI)
library(duckdb)

# Set paths for our environments
# Make sure we're reading from the project Renviron
if (file.exists(".Renviron")) readRenviron(".Renviron")

# Set paths
data <- get_env_path("DATA")

db_path <- paste0(data, "/duckdb", "/metro_deep_dive.duckdb")
con <- dbConnect(duckdb::duckdb(), dbdir = db_path, read_only = FALSE)

# (optional) sanity check
dbGetQuery(con, "PRAGMA version;")  # proves it's open

# Create our schemas in the Metro database
dbExecute(con, "CREATE SCHEMA IF NOT EXISTS staging;")
dbExecute(con, "CREATE SCHEMA IF NOT EXISTS silver;")
dbExecute(con, "CREATE SCHEMA IF NOT EXISTS gold;")

# Create our Staging Environment
# Name tables Source <> KPI <> Gran
dbWriteTable(con, 
             DBI::Id(schema = "staging", table = "acs_age_us"),
             us_acs_age_raw, 
             overwrite = TRUE)


# Check what tables are created
dbListTables(con, "staging")        # lists tables in the staging schema
head(dbGetQuery(con, "SELECT * FROM staging.acs_age_us LIMIT 5"))

# Shutdown
dbDisconnect(con, shutdown = TRUE)