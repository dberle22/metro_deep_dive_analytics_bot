# Loop 1 QA Fix Brief

## Instructions for the Agent

You are being handed a specific, scoped set of fixes to implement in the `metro_deep_dive_chatbot` repo. Work through the issues in the priority order listed below. Before starting each fix, read the relevant files first so you understand the current implementation.

**Important:** If you encounter a blocker — for example, a geo level that does not exist in the Gold layer, a table that is missing, or a semantic layer concept that is not yet defined — **stop and ask the user for clarification before proceeding**. Do not attempt to resolve data or schema gaps on your own. The user needs to make those decisions. Describe exactly what you found and what the options are, then wait.

---

## Context

This is `metro_deep_dive_chatbot` — a constrained analytical chatbot that takes natural language questions and returns a structured query plan, SQL, query results, a chart, and answer text. The pipeline layers are:

```
intent parsing → query planning → SQL generation → SQL validation
  → execution → chart selection → R chart rendering → answer text assembly
```

Key directories:
- `semantic_layer/` — YAML source of truth (tables, metrics, geography, chart rules, query templates)
- `app/` — Python backend
- `app/intent/parser.py` — intent parsing and heuristic matching
- `app/response/assembler.py` — answer text generation
- `app/scripts/ask.py` — CLI runner and artifact saving
- `visual_library/shared/render/` — R chart rendering scripts
- `examples/question_library.yml` — few-shot examples used in the LLM system prompt

QA loop 1 was run with 10 prompts via `app/scripts/qa_batch.py`. Human reviews are in `runs/qa_batch/loop1/*/qa_review.json`. The full QA framework is in `QA_FRAMEWORK.md`.

After completing all fixes, re-run the batch and verify outcomes as described at the bottom of this brief.

---

## Issues to Fix — In Priority Order

### 1. Bar chart sort order is reversed for ranking

**Cases affected:** qa_r_001, qa_r_002

**Symptom:** Both ranking runs returned `sort_direction: desc` in the query plan and correct descending SQL, but the rendered bar chart displays the lowest value at the top and the highest at the bottom — the opposite of what is expected.

**Where to look:** `visual_library/shared/render/render_bar.R`. The sort direction from the query plan is passed through the R subprocess config JSON. Check whether the R script is reversing the factor order, or whether the config is not being read correctly.

**Expected fix:** For ranking charts with `sort_direction: desc`, the highest value should appear at the top (horizontal bar) or leftmost (vertical bar). This likely requires reversing the factor order in the R script or passing a `sort_dir` parameter through the config.

**Verify:** Re-run `qa_r_001` and `qa_r_002` with `--render-chart` and confirm the bar chart shows the highest value at the top.

---

### 2. Benchmark pipeline is fundamentally broken

**Cases affected:** qa_b_001, qa_b_002, qa_b_003

This is the largest issue and has multiple root causes across different layers.

**qa_b_001** (`"Compare Florida's population to the US in 2024"`) — heuristic parser routes this to benchmark but the output is a single-row result for Florida only with no US comparison. `benchmark_type` was not set. The SQL did not join or compare against a US aggregate.

**qa_b_002** (`"How does Texas household income stack up against the national average?"`) — LLM triggered an unnecessary clarification. The question is fully specified: Texas, household income, US benchmark.

**qa_b_003** (`"Is California's median home value above the US average in 2024?"`) — LLM identified the wrong question type entirely (ranking instead of benchmark).

**Root causes to investigate:**

- `"us"` may not be a recognized `geo_level` or may not have real data in the Gold layer. **If this is the case, stop and ask the user before proceeding.**
- The benchmark query template in `query_templates.yml` may not be generating a real side-by-side comparison (i.e. target geo row vs US aggregate row).
- The LLM few-shot examples in `examples/question_library.yml` likely have zero or weak benchmark examples, causing the model to fall back to clarification or misclassify.
- The heuristic parser in `app/intent/parser.py → _heuristic_parse()` has a benchmark branch but `benchmark_type: "us"` may not be set and propagated correctly.

**Expected fixes (only if the data exists to support them):**

1. Confirm `"us"` is a valid `geo_level` in `geography_catalog.yml` and that US-level rows exist in the relevant Gold tables. If not, stop and report to the user.
2. Audit the benchmark query template: it should produce a two-row result — one for the target geo, one for the US — that can be shown side by side.
3. Add 2–3 strong benchmark few-shot examples to `examples/question_library.yml` covering `state vs us` for population, income, and home value.
4. Update the LLM system prompt in `app/intent/parser.py → build_system_prompt()` to more clearly describe when to use `benchmark` vs `comparison` vs `ranking`.

**Verify:** Re-run all three `qa_b_*` cases. All three should parse to `question_type: benchmark` with a valid `benchmark_type: us` and return a two-row result.

---

### 3. "Places" not mapped to a geo level

**Case affected:** qa_c_001

**Symptom:** `"What are the fastest growing places?"` triggered a clarification. "places" should resolve to a geo level. Additionally, when no geo is specified for a growth or ranking question, the system should default to a reasonable geo level rather than always clarifying.

**Two sub-issues:**

- `"place"`, `"places"`, `"city"`, `"cities"`, `"town"`, `"towns"` are not in the geo pattern list in `app/intent/parser.py → _infer_geo_level()`. Before adding them, **check whether a `place` geo level exists in `geography_catalog.yml` and whether place-level data exists in the Gold layer. If not, stop and ask the user what geo level "places" should resolve to.**
- For growth and ranking questions where geo is not specified, consider defaulting to `state` rather than requiring clarification.

**Verify:** Re-run `qa_c_001`. It should parse without clarification and resolve to a valid geo level.

---

### 4. Clarification message language is too technical

**Case affected:** qa_c_002

**Symptom:** Clarification messages expose internal field names like `geo_level`, `geo_ids`, and `year` directly to the user. These are implementation terms, not user-friendly language.

**Where to fix:** `app/intent/parser.py → _build_clarification()`. Map internal field names to plain English before constructing the message:

- `geo_level` → "which geography type (state, metro, county, etc.)"
- `geo_ids` → "which specific location"
- `year` → omit if a reasonable default (latest year) can be used instead; otherwise "which year"
- `metric_id` → "which metric (population, income, home value, etc.)"

**Verify:** Re-run `qa_c_002`. The clarification message should be readable by a non-technical user with no knowledge of the system internals.

---

### 5. Answer text missing insight for distribution and trend cases

**Cases affected:** qa_d_001, qa_t_002

**Symptom:** Answer text is accurate but shallow. For `qa_d_001` (distribution of state home values) the answer does not call out any specific states. For `qa_t_002` (trend across all states) it does not highlight any notable performers.

**Where to fix:** `app/response/assembler.py`. Enhance the distribution and trend templates:

- **Distribution:** include the geo with the highest value, the geo with the lowest value, and the median value. All are derivable from the result dataframe.
- **Trend:** for multi-geo trend results, identify the geo with the highest end value and the geo with the largest absolute or percentage change over the window.

**Verify:** Re-run `qa_d_001` and `qa_t_002`. Answer text should cite at least one specific data-grounded insight (e.g. "Hawaii had the highest median home value at $X. West Virginia was the lowest at $Y.").

---

### 6. Default highlight state in distribution chart

**Case affected:** qa_d_001

**Symptom:** Florida appears to be hardcoded as the default highlight state in the boxplot chart.

**Where to look:** `visual_library/shared/render/render_boxplot.R` and `app/charts/renderer.py`. Check for any hardcoded `"FL"` or `"Florida"` reference. The highlight should be driven by the query plan (e.g. a specific geo was named in the question) or left blank when no specific geo was requested.

**Verify:** Re-run `qa_d_001`. No state should be highlighted unless one was specified in the question.

---

### 7. Result preview sort order for time-series (minor)

**Case affected:** qa_t_001

**Symptom:** The 5-row `result_preview` in `qa_run.json` shows rows from only one geography because the data is not sorted by year first.

**Where to fix:** `app/scripts/ask.py → build_qa_run_json()`. When building `result_preview`, check `result_profile.has_time_series` and if true, sort the dataframe by `year` then `geo_name` before calling `.head(5)`.

**Verify:** Re-run `qa_t_001`. The `result_preview` in `qa_run.json` should show rows from multiple geographies across different years.

---

## After All Fixes: Verification Steps

Run the full prompt library against loop2:

```bash
.venv/bin/python -m app.scripts.qa_batch --collection loop2 --render-chart
```

Then open the QA review app to compare:

```bash
.venv/bin/python -m streamlit run frontend/qa_review.py
```

Expected outcomes in loop2:
- All three `qa_b_*` cases parse to `benchmark` with `benchmark_type: us` and return a 2-row result
- Both `qa_r_*` cases show the highest value at the top of the bar chart
- `qa_c_001` resolves without clarification to a valid geo level
- `qa_c_002` clarification message uses plain English
- `qa_d_001` and `qa_t_002` answer text cites at least one specific data-grounded insight
- `qa_d_001` chart has no default highlight state
- `qa_t_001` `result_preview` shows rows from multiple geographies
