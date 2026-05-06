# Shared CLI helpers for standalone chart rendering.

parse_render_cli_args <- function(args = commandArgs(trailingOnly = TRUE)) {
  out <- list()
  idx <- 1
  while (idx <= length(args)) {
    key <- args[[idx]]
    if (!startsWith(key, "--")) {
      stop(sprintf("Unexpected argument: %s", key), call. = FALSE)
    }
    if (idx == length(args)) {
      stop(sprintf("Missing value for %s", key), call. = FALSE)
    }
    out[[substring(key, 3)]] <- args[[idx + 1]]
    idx <- idx + 2
  }

  required <- c("config", "data", "output")
  missing <- setdiff(required, names(out))
  if (length(missing) > 0) {
    stop(
      sprintf("Missing required CLI args: %s", paste(missing, collapse = ", ")),
      call. = FALSE
    )
  }

  out
}

load_render_inputs <- function(args) {
  config <- jsonlite::fromJSON(args$config, simplifyVector = TRUE)
  data <- utils::read.csv(args$data, stringsAsFactors = FALSE, check.names = FALSE)
  list(config = config, data = data, output = args$output)
}

save_rendered_plot <- function(plot, output, config = list()) {
  ggplot2::ggsave(
    output,
    plot = plot,
    width = as.numeric(config$width %||% 11),
    height = as.numeric(config$height %||% 7),
    dpi = as.numeric(config$dpi %||% 300),
    bg = config$background_fill %||% "white"
  )
  invisible(output)
}

run_renderer_cli <- function(render_fn, adapter = NULL) {
  args <- parse_render_cli_args()
  payload <- load_render_inputs(args)
  plot <- if (is.null(adapter)) {
    render_fn(payload$data, payload$config)
  } else {
    adapter(payload$data, payload$config, render_fn)
  }
  save_rendered_plot(plot, payload$output, payload$config)
}
