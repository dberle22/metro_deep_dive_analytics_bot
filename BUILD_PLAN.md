# Chatbot Build Plan
## US Demographic & Economic Analytics Chatbot

Last updated: 2026-04-24

---

## Overview

A constrained analytical chatbot that converts natural language questions about US demographic and economic data into trusted SQL, standardized visuals, and concise answers. Users ask questions like "Which midsize metros had the fastest population growth over 5 years?" and receive a written summary, a chart from the visual library, a supporting table, the SQL used, and metric definitions.

**Core design principle:** Reliability over openness. Answer a narrow set of questions well rather than support unlimited free-form analysis poorly.

---

## Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend | Python + FastAPI | Standard for ML/LLM orchestration; clean API boundary |
| Frontend | Streamlit | Fastest MVP path; deployable to Streamlit Cloud |
| Data (local/dev) | DuckDB at local file path | Use existing Gold layer for all dev and testing |
| Data (production) | MotherDuck | Cloud-hosted DuckDB; solves multi-user sharing |
| LLM (local/dev) | Ollama + Llama 3.2 3B | Runs on Intel CPU; sufficient for prompt iteration |
| LLM (production) | Groq API (Llama 3) | Same model family as local; free tier; fast |
| LLM abstraction | OpenAI-compatible interface | Swap local → hosted via single env var; no code change |
| Python-to-R bridge | subprocess | Simplest integration; no runtime coupling; good enough for MVP |
| Semantic layer format | YAML files | Human-readable, version-controlled, agent-editable |
| Build order | Semantic layer → SQL templates → LLM orchestration → Charts → Frontend → Deploy | Each phase builds on previous; no orphaned work |

### Data Path Strategy

- **Development and testing:** Local DuckDB at `/Users/danberle/Documents/projects/data/duckdb/metro_deep_dive.duckdb`
- **Production deployment:** MotherDuck (migration handled in Phase 6)
- The `DB_CONNECTION` env var controls which is used; app code is identical for both

### LLM Provider Strategy

Both local (Ollama) and production (Groq) expose an OpenAI-compatible chat completions API. The app uses an environment variable to select the provider — no application code changes between environments.

```
# Local development
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Production
LLM_PROVIDER=groq
GROQ_API_KEY=...
```

### MVP Subject Area Scope

Start with three Gold tables. Expand to others once the pipeline is validated end-to-end.

| Priority | Table | Subject |
|---|---|---|
| 1 | `gold.population_demographics` | Population, age, demographics |
| 2 | `gold.housing_core_wide` | Housing units, tenure, costs, structure |
| 3 | `gold.economics_income_wide` | Income, earnings, per capita |
| Later | `gold.economics_labor_wide` | Employment, wages, unemployment |
| Later | `gold.affordability_wide` | Rent burden, value-to-income |
| Later | `gold.economics_gdp_wide` | Regional GDP |
| Later | Others | Migration, transport, industry |

### MVP Geography Scope

Region, Division, State, CBSA, County. ZCTA and Census Tract deferred to v1.1.

### MVP Question Types

Rankings, trends over time, comparisons across geographies, distributions, benchmark comparisons. Scatter/relationship questions deferred to v1.1.

### MVP Chart Types (from visual library)

Bar, line, scatter, boxplot, heatmap table, slopegraph. Choropleth and highlight context map deferred to v1.1 (map rendering adds significant complexity).

---

## Repo Structure

```
metro_deep_dive_chatbot/
├── BUILD_PLAN.md                   ← this file
├── chatbot/                        ← product docs (existing)
│   └── docs/
├── data_dictionary/                ← Gold table definitions (existing)
├── visual_library/                 ← R chart library (existing)
├── app/                            ← TO BE BUILT
│   ├── main.py                     ← FastAPI entry point
│   ├── orchestrator.py             ← end-to-end pipeline
│   ├── intent/
│   │   ├── parser.py               ← LLM intent parsing
│   │   └── prompts/                ← prompt templates
│   ├── query/
│   │   ├── planner.py              ← structured query plan builder
│   │   ├── generator.py            ← SQL template rendering
│   │   ├── validator.py            ← SQL safety and correctness checks
│   │   └── executor.py             ← DuckDB / MotherDuck query runner
│   ├── charts/
│   │   ├── profiler.py             ← result shape profiler
│   │   ├── selector.py             ← chart type selection logic
│   │   └── renderer.py             ← subprocess R bridge
│   ├── response/
│   │   └── assembler.py            ← final answer + metadata assembly
│   └── llm/
│       └── provider.py             ← Ollama / Groq abstraction
├── semantic_layer/                 ← TO BE BUILT
│   ├── table_catalog.yml
│   ├── metric_catalog.yml
│   ├── join_catalog.yml
│   ├── geography_catalog.yml
│   ├── chart_rules.yml
│   └── query_templates.yml
├── frontend/                       ← TO BE BUILT
│   └── streamlit_app.py
├── examples/                       ← TO BE BUILT
│   ├── question_library.yml        ← tagged example questions + expected SQL
│   └── sample_sql/
├── tests/                          ← TO BE BUILT
│   ├── test_semantic/
│   ├── test_sql/
│   └── test_pipeline/
├── .env.example
└── requirements.txt
```

---

## Phase 0 — Environment & Data Setup

**Goal:** Verify the full local stack works before writing product code. Nothing in later phases should fail due to environment issues.

**Owner:** Human / Engineer

- [x] Install Ollama on local machine: `brew install ollama`
- [x] Pull the dev model: `ollama pull llama3.2:3b`
- [x] Verify local DuckDB connection is readable:
  ```python
  import duckdb
  con = duckdb.connect("/Users/danberle/Documents/projects/data/duckdb/metro_deep_dive.duckdb", read_only=True)
  con.execute("SHOW TABLES").fetchall()
  ```
- [x] Confirm all 9 Gold tables are present and queryable
- [x] Confirm R is installed and the visual library renders a test chart from the command line
- [x] Create `requirements.txt` with initial deps: `fastapi`, `duckdb`, `python-dotenv`, `openai` (used for Ollama/Groq compatible calls), `pandas`, `pydantic`
- [x] Create `.env.example` with all expected env vars documented (no real values)
- [x] Create `.env` locally with real values (gitignored)
- [x] Stub the `app/`, `semantic_layer/`, `examples/`, `frontend/`, `tests/` directories with placeholder files

**Success check:** `python -c "import duckdb; con = duckdb.connect('...'); print(con.execute('SELECT COUNT(*) FROM gold.population_demographics').fetchone())"` returns a row count.

---

## Phase 1 — Semantic Layer

**Goal:** A machine-readable contract the app and LLM use instead of inventing schema logic. This is the highest-leverage work in the project — every downstream component depends on it.

**Owner:** Agent (with human review before Phase 2 begins)

### `table_catalog.yml`

- [x] Add entry for `gold.population_demographics` (schema, grain, geo fields, time field, subject area, description)
- [x] Add entry for `gold.housing_core_wide`
- [x] Add entry for `gold.economics_income_wide`
- [x] Add stub entries for the 6 remaining Gold tables (marked `status: deferred`)

Each entry format:
```yaml
- table_id: population_demographics
  schema: gold
  table_name: population_demographics
  subject_area: population
  description: "..."
  grain: one row per geo_level + geo_id + year
  geo_id_field: geo_id
  geo_level_field: geo_level
  geo_name_field: geo_name
  time_field: year
  supported_geo_levels: [region, division, state, cbsa, county]
  status: active
```

### `metric_catalog.yml`

- [x] Define 8–12 metrics from `population_demographics` (e.g. `total_population`, `pop_growth_5yr`, `median_age`, `pct_foreign_born`)
- [x] Define 8–12 metrics from `housing_core_wide` (e.g. `median_home_value`, `median_gross_rent`, `owner_occupancy_rate`)
- [x] Define 8–12 metrics from `economics_income_wide` (e.g. `median_household_income`, `per_capita_income`, `income_growth_5yr`)
- [x] Mark each metric with `growth_eligible: true/false` and supported growth windows

Each entry format:
```yaml
- metric_id: total_population
  display_name: "Total Population"
  description: "..."
  source_table: population_demographics
  source_column: total_population
  unit_format: integer
  subject_area: population
  valid_geo_levels: [us, region, division, state, cbsa, county]
  growth_eligible: true
  growth_windows: [1, 3, 5]
  caveats: "ACS 5-year estimates; not comparable to decennial census counts"
  status: active
```

### `geography_catalog.yml`

- [x] Define all supported geo levels with canonical names and `geo_level` values used in DuckDB
- [x] Define parent-child hierarchy (county → cbsa, county → state, state → division, state → region)
- [x] Note which rollup paths are valid vs. invalid (e.g. ZCTA does not roll up cleanly to CBSA)

### `join_catalog.yml`

- [x] Define approved join paths between the 3 active tables (via `geo_id` + `geo_level` + `year`)
- [x] Note grain compatibility rules (same grain required for most joins)
- [x] Note any known join caveats in the Gold layer

### `chart_rules.yml`

- [x] Map each question type + result shape to 1–2 approved chart types
- [x] Start with: ranking → bar; trend → line; comparison → bar or slopegraph; distribution → boxplot or histogram; benchmark → bar with reference line; correlation → scatter

### `query_templates.yml`

- [x] Define 6 named SQL template patterns:
  - `ranking`: top/bottom N by metric, optional geo filter
  - `trend`: metric over time for one or more geographies
  - `compare_selected`: metric across a user-specified list of geographies
  - `distribution`: spread of a metric across all geos at a grain
  - `benchmark`: target geo vs. benchmark (US, region, state, peers)
  - `growth`: point-in-time growth rate over N years via LAG or CTE

### Semantic Graph & Visualization

- [x] Add a shared Python semantic graph builder that loads all Phase 1 YAML catalogs into a graph model
- [x] Add Mermaid diagram export for human-readable semantic layer visualization
- [x] Add a CLI workflow to regenerate graph artifacts from the YAML source of truth
- [x] Add tests for graph construction and Mermaid generation
- [x] Document how to visualize and explore the semantic layer

**Human review checkpoint:** Before Phase 2, review all YAML files for accuracy against the actual DuckDB schema. Run sample queries manually to confirm field names and grain.

---

## Phase 2 — SQL Templates & Validation

**Goal:** Turn a structured query plan (JSON/dict) into validated, executable SQL — with no LLM involved. This must work deterministically before the LLM layer is added.

**Owner:** Agent

- [ ] Build `app/query/generator.py`: reads `query_templates.yml`, takes a structured plan dict, renders parameterized SQL using Jinja2 or f-strings
- [ ] Build `app/query/validator.py`: checks rendered SQL against semantic layer rules
  - Tables used are in `table_catalog.yml` and marked `status: active`
  - Fields used exist in the table (cross-reference `data_dictionary/`)
  - Joins used are in `join_catalog.yml`
  - Query is read-only (no INSERT, UPDATE, DROP, etc.)
  - Geo level is in the table's `supported_geo_levels`
- [ ] Build `app/query/executor.py`: connects to DuckDB (path from env var), executes validated SQL, returns a pandas DataFrame
- [ ] Build `examples/question_library.yml`: 20–30 example questions with:
  - natural language question
  - structured query plan (hand-written)
  - expected template type
  - expected SQL pattern
  - expected chart type
- [ ] Write tests in `tests/test_sql/` that run each example question's hand-written plan through the generator and validator and confirm the SQL is correct

**Success check:** Every example in `question_library.yml` produces valid, executable SQL against the local DuckDB with correct results.

---

## Phase 3 — LLM Orchestration

**Goal:** Convert a natural language question into a structured query plan using the local model. The semantic layer and example library do the grounding; the LLM fills the structured slots.

**Owner:** Agent

- [ ] Build `app/llm/provider.py`: abstract class with `OllamaProvider` and `GroqProvider` implementations, both using the OpenAI-compatible interface. Selected by `LLM_PROVIDER` env var
- [ ] Build `app/intent/parser.py`: sends a question to the LLM with a system prompt that includes:
  - supported tables and metrics from `table_catalog.yml` and `metric_catalog.yml`
  - supported geo levels from `geography_catalog.yml`
  - supported question types
  - 5–8 few-shot examples from `question_library.yml`
  - instruction to return a structured JSON query plan
- [ ] Define the structured query plan schema (Pydantic model):
  ```python
  class QueryPlan(BaseModel):
      question_type: str        # ranking, trend, compare, distribution, benchmark, growth
      subject_area: str
      metric_id: str
      geo_level: str
      geo_filter: dict | None
      benchmark_type: str | None
      time_range: dict | None
      growth_window: int | None
      sort: str | None
      limit: int | None
  ```
- [ ] Build clarification logic: if the LLM cannot fill required fields (`metric_id`, `geo_level`, `question_type`), return a targeted clarification question to the user instead of a query plan
- [ ] Build `app/orchestrator.py`: wires intent parser → query planner → SQL generator → validator → executor in sequence; handles clarification routing
- [ ] Evaluate intent parser against all 20–30 examples in `question_library.yml`; target 80%+ correct structured plans

**Success check:** A natural language question typed in Python produces a correct structured plan, valid SQL, and a result DataFrame — all in one call to `orchestrator.run(question)`.

---

## Phase 4 — Chart Selection & Rendering

**Goal:** Turn a query result DataFrame into a rendered chart using the existing R visual library.

**Owner:** Agent

- [ ] Build `app/charts/profiler.py`: inspects a result DataFrame and returns a result profile dict:
  - `row_count`
  - `has_time_series` (bool)
  - `has_geo_column` (bool)
  - `dimension_count`
  - `measure_count`
  - `inferred_shape` (ranking, trend, distribution, comparison, benchmark)
- [ ] Build `app/charts/selector.py`: takes `question_type` from the query plan + `inferred_shape` from the profiler, looks up `chart_rules.yml`, returns the best approved chart type
- [ ] Build `app/charts/renderer.py`: subprocess bridge
  - Writes result DataFrame to a temp CSV
  - Writes chart config (type, x, y, group, title) to a temp JSON
  - Calls the appropriate R script: `Rscript visual_library/shared/render/render_{chart_type}.R --config /tmp/chart_config.json --data /tmp/chart_data.csv --output /tmp/chart_out.png`
  - Returns the path to the rendered PNG
- [ ] Confirm each active R render script accepts `--config`, `--data`, `--output` CLI args (adapt scripts if needed — this is human-reviewable work)
- [ ] Wire chart selection + rendering into `orchestrator.py`

**R script CLI interface (human task):**
- [ ] Review the 6 MVP chart render scripts (`render_bar.R`, `render_line.R`, `render_scatter.R`, `render_boxplot.R`, `render_heatmap_table.R`, `render_slopegraph.R`) and confirm or add CLI argument handling so they can be called from subprocess

**Success check:** `orchestrator.run("Which states had the highest population growth over 5 years?")` returns a written answer, a PNG path, a DataFrame, and SQL.

---

## Phase 5 — Streamlit Frontend

**Goal:** A clean, inspectable UI a non-technical user can use without reading documentation.

**Owner:** Agent

- [ ] Build `frontend/streamlit_app.py` with:
  - Chat-style input at the bottom
  - Response history (scrollable, most recent at top)
  - For each response:
    - Short written answer (always visible)
    - Chart (always visible, with download button)
    - Result table (always visible, with copy/download)
    - Expandable SQL panel
    - Expandable assumptions + metric definitions panel
  - Loading state indicator during query
  - Clarification prompt display (when orchestrator returns a clarification instead of an answer)
- [ ] Add session state management: retain `geo_level`, `metric_id`, `geo_filter`, `time_range` across turns for follow-up support
- [ ] Add follow-up detection: if a new question modifies but doesn't replace the prior plan (e.g. "now filter to the South"), merge with session state rather than starting fresh
- [ ] Add example prompt suggestions on first load (pull from `question_library.yml`)
- [ ] Test against at least 10 example questions from the library end-to-end

**Success check:** A user unfamiliar with the data model can ask a question, read the answer, inspect the SQL, and ask a follow-up — all without confusion.

---

## Phase 6 — Cloud Deployment

**Goal:** Deploy a shared instance accessible to a small group of users.

**Owner:** Human / Engineer (with agent support for config files)

### MotherDuck Migration

- [ ] Create MotherDuck account and workspace
- [ ] Export local DuckDB Gold tables to MotherDuck (DuckDB's `COPY` or MotherDuck CLI)
- [ ] Confirm all 9 Gold tables are queryable in MotherDuck
- [ ] Update `DB_CONNECTION` env var to use MotherDuck connection string
- [ ] Run full example question library against MotherDuck to confirm parity with local results

### Streamlit Cloud Deployment

- [ ] Create `packages.txt` to install R on Streamlit Cloud: `r-base`
- [ ] Create `setup.sh` to install required R packages (`ggplot2`, `dplyr`, etc.) at build time
- [ ] Create `requirements.txt` finalized with all Python deps and pinned versions
- [ ] Set all env vars in Streamlit Cloud secrets: `DB_CONNECTION`, `LLM_PROVIDER=groq`, `GROQ_API_KEY`
- [ ] Set up basic access control (Streamlit's built-in password or `st.secrets`-based allowlist) for the small user group
- [ ] Deploy and run smoke test: 5 questions covering each supported question type

### Post-Deploy Checks

- [ ] Confirm chart rendering works on Streamlit Cloud (R subprocess call succeeds)
- [ ] Confirm MotherDuck queries return in acceptable latency (<5s for typical questions)
- [ ] Confirm Groq LLM responses are correct (re-run 10 example questions)

---

## Open Decisions (to resolve during implementation)

| Decision | Status | Notes |
|---|---|---|
| Exact metrics per subject area | Resolve in Phase 1 | Derive from `data_dictionary/` YAML files |
| Which Gold fields are actually populated vs. sparse | Resolve in Phase 0 | Query DuckDB to audit coverage |
| R script CLI interface standardization | Resolve in Phase 4 | Review each render script; adapt as needed |
| Peer group support | Deferred to v1.1 | Manual peer list in session; no DB-backed peer table in MVP |
| Growth window calculation method | Resolve in Phase 2 | LAG vs. self-join CTE; confirm DuckDB compatibility |
| Follow-up question merging strategy | Resolve in Phase 5 | Rule-based merge vs. second LLM call to diff plans |
| Benchmark query pattern | Resolve in Phase 2 | Union of target + benchmark rows vs. joined approach |
| Map chart types (choropleth, highlight context) | Deferred to v1.1 | Geometry handling adds significant complexity |

---

## Milestone Summary

| Milestone | Phase | What It Proves |
|---|---|---|
| Stack verified | 0 | Local DuckDB, Ollama, and R all work together |
| Semantic layer complete | 1 | The analytical contract is defined and reviewed |
| SQL pipeline works | 2 | Deterministic, validated SQL from structured plans |
| LLM orchestration works | 3 | Natural language → correct SQL end-to-end |
| Full pipeline works | 4 | Question → chart output locally |
| App usable | 5 | Non-technical user can interact without confusion |
| Deployed | 6 | Shared with small user group on Streamlit Cloud |
