# Query helpers for scatter chart sample pipelines.

get_env_path <- function(key) {
  val <- Sys.getenv(key, unset = "")
  if (!nzchar(val)) return(NA_character_)
  path.expand(val)
}

resolve_duckdb_path <- function() {
  db_connection <- get_env_path("DB_CONNECTION")
  if (!is.na(db_connection)) {
    return(db_connection)
  }

  data_root <- get_env_path("DATA")
  if (is.na(data_root)) {
    stop("Either DB_CONNECTION or DATA must be set.")
  }

  file.path(data_root, "duckdb", "metro_deep_dive.duckdb")
}

read_sql_file <- function(path) {
  if (!file.exists(path)) {
    stop(paste("SQL file not found:", path))
  }
  paste(readLines(path, warn = FALSE), collapse = "\n")
}

connect_metro_duckdb <- function(read_only = TRUE) {
  if (!requireNamespace("DBI", quietly = TRUE) || !requireNamespace("duckdb", quietly = TRUE)) {
    stop("Packages DBI and duckdb are required.")
  }

  db_path <- resolve_duckdb_path()
  if (!file.exists(db_path)) stop(paste("DuckDB not found:", db_path))

  con <- DBI::dbConnect(duckdb::duckdb(), dbdir = db_path, read_only = read_only)

  # Attach the same database under the legacy catalog name so older sample SQL
  # that still references metro_deep_dive.gold.* continues to work.
  tryCatch(
    DBI::dbExecute(
      con,
      paste0(
        "ATTACH '",
        gsub("'", "''", db_path, fixed = TRUE),
        "' AS metro_deep_dive (READ_ONLY)"
      )
    ),
    error = function(err) {
      if (!grepl("already exists", conditionMessage(err), fixed = TRUE)) {
        stop(err)
      }
      invisible(NULL)
    }
  )

  con
}

run_scatter_query <- function(con, sql_path) {
  sql <- read_sql_file(sql_path)
  DBI::dbGetQuery(con, sql)
}
