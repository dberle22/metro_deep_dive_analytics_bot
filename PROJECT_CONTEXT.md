# Metro Deep Dive — Shared Project Context

**Purpose of this document:** Cross-repo context for any Claude project that spans the Metro Deep Dive ecosystem. Keep it current as phases complete and architecture decisions change.

Last updated: 2026-05-10

---

## The Ecosystem

Three repos form the core of this work:

| Repo | Language | Role |
|---|---|---|
| `metro_database_build` | SQL / dbt / DuckDB | Builds the Bronze → Silver → Gold data layers from raw sources |
| `metro_deep_dive` | R | Analytics platform: reusable functions, visual library, Retail Opportunity Finder product, secondary analyses |
| `metro_deep_dive_chatbot` | Python + R | NL-to-SQL chatbot over the Gold layer; portfolio app for non-technical analysts |

The chatbot is a consumer of the Gold layer built by `metro_database_build`. The R visual library in `metro_deep_dive` is the chart rendering engine for the chatbot.

**Shared data path (dev):** `/Users/danberle/Documents/projects/data/duckdb/metro_deep_dive.duckdb`

---

## What the Chatbot Is

A constrained analytical chatbot where users ask natural language questions about US demographic and economic data and receive:
- a short written answer
- a chart (rendered by R)
- a supporting data table
- the SQL used
- metric definitions and assumptions

**Core design principle:** Reliability over openness. Answer a narrow set of questions well; reject or clarify everything outside scope rather than improvising.

**Audience:** Portfolio demo + small group of non-technical analysts. Deploy target: Streamlit Cloud.

---

## Build Status (as of 2026-05-10)

| Phase | Status | What it delivered |
|---|---|---|
| 0 — Environment | ✅ Complete | Local DuckDB, Ollama, R all verified |
| 1 — Semantic layer | ✅ Complete | `semantic_layer/` YAML catalogs for tables, metrics, geography, joins, chart rules, query templates |
| 2 — SQL pipeline | ✅ Complete | Deterministic SQL generation, validation, DuckDB execution |
| 3 — LLM orchestration | ✅ Complete | NL → structured query plan → SQL via Ollama/Groq |
| 4 — Chart rendering | ✅ Complete | R subprocess bridge; result profiling and chart selection |
| 4.5 — Pipeline hardening | ✅ Complete | QA tooling, batch runner, artifact saving, QA prompt library |
| **Reference dashboard** | ✅ Complete | `reference_dashboard/data_explorer.py` — Streamlit choropleth + data table for QA ground-truth lookup |
| **5 — Streamlit frontend** | 🔲 Pending | Chat UI over the orchestrator |
| **6 — Cloud deployment** | 🔲 Pending | MotherDuck migration, Streamlit Cloud deploy |

---

## Repo Structure

```
metro_deep_dive_chatbot/
├── app/
│   ├── orchestrator.py          ← end-to-end pipeline (parse → plan → SQL → execute → chart → assemble)
│   ├── intent/parser.py         ← LLM intent parsing → QueryPlan (Pydantic)
│   ├── llm/provider.py          ← OllamaProvider / GroqProvider (OpenAI-compatible interface)
│   ├── query/
│   │   ├── planner.py           ← QueryPlan → PlannedQuery
│   │   ├── generator.py         ← PlannedQuery → SQL (Jinja2 templates from semantic layer)
│   │   ├── validator.py         ← SQL safety + semantic layer compliance checks
│   │   └── executor.py          ← DuckDB query runner
│   ├── charts/
│   │   ├── profiler.py          ← result DataFrame → ResultProfile (shape inference)
│   │   ├── selector.py          ← question_type + profile → chart type (from chart_rules.yml)
│   │   └── renderer.py          ← subprocess R bridge (CSV + JSON config → PNG)
│   ├── response/assembler.py    ← answer text assembly
│   └── scripts/
│       ├── ask.py               ← CLI entrypoint; --output-dir saves full artifact set
│       └── qa_batch.py          ← batch QA runner
├── semantic_layer/
│   ├── table_catalog.yml        ← approved tables: schema, grain, geo fields, time field
│   ├── metric_catalog.yml       ← metrics: source column, unit_format, growth eligibility
│   ├── geography_catalog.yml    ← geo levels, hierarchy, rollup rules
│   ├── join_catalog.yml         ← approved join paths between Gold tables
│   ├── chart_rules.yml          ← question_type + result shape → approved chart types
│   └── query_templates.yml      ← 6 SQL template patterns (Jinja2)
├── data_dictionary/
│   └── layers/gold/             ← YAML + MD definitions for each Gold table
├── visual_library/              ← R chart library (shared with metro_deep_dive)
│   └── shared/render/           ← render_{chart_type}.R scripts (CLI: --config --data --output)
├── reference_dashboard/
│   ├── data_explorer.py         ← Streamlit data explorer (choropleth + table for QA)
│   └── explorer_utils.py        ← DuckDB helpers, GeoJSON builder, formatters
├── frontend/
│   ├── streamlit_app.py         ← Chat UI (Phase 5, in progress)
│   ├── qa_review.py             ← QA review surface
│   └── qa_utils.py
├── examples/
│   └── question_library.yml     ← 20-30 tagged examples with expected query plans + SQL
├── qa/
│   └── qa_prompt_library.yml    ← QA prompt library (golden / paraphrase / clarification categories)
├── tests/
├── analysis/                    ← Short-form manual analyses (leading indicator for chatbot)
├── BUILD_PLAN.md                ← Phase-by-phase implementation plan with completion status
├── qa/QA_FRAMEWORK.md           ← QA layer definitions, scoring, prompt category specs
├── qa/QA_TUNING_LOG.md          ← Loop-by-loop QA scoreboard and fix history
├── DASHBOARD_SPEC.md            ← Reference dashboard full spec
└── DASHBOARD_BACKLOG.md         ← Reference dashboard sprint tasks (all complete)
```

---

## Tech Stack

| Concern | Choice | Notes |
|---|---|---|
| Backend | Python + FastAPI | Orchestration layer |
| Frontend (chatbot) | Streamlit | Deploy to Streamlit Cloud |
| Data (dev) | Local DuckDB | `DB_CONNECTION` env var |
| Data (prod) | MotherDuck | Phase 6 migration |
| LLM (dev) | Ollama + Llama 3.2 3B | Intel Mac CPU |
| LLM (prod) | Groq API (Llama 3) | Free tier, fast, same model family |
| LLM interface | OpenAI-compatible chat completions | Swap via `LLM_PROVIDER` env var — no code change |
| Python-to-R bridge | subprocess | temp CSV + JSON config → Rscript → PNG |
| Semantic layer format | YAML files in repo | Human-readable, version-controlled |
| Map library (dashboard) | Plotly Express choropleth_mapbox | carto-positron tiles, no API key |

**Do not suggest Claude API, OpenAI API, or rpy2.** The LLM choice (Ollama/Groq) is intentional for learning local/open-source model workflows.

---

## Gold Layer Tables

These live in `gold.*` in DuckDB. All are defined in `data_dictionary/layers/gold/`.

| Table | Subject | Status in chatbot |
|---|---|---|
| `gold.population_demographics` | Population, age, demographics | ✅ Active (MVP) |
| `gold.housing_core_wide` | Housing units, tenure, costs | ✅ Active (MVP) |
| `gold.economics_income_wide` | Income, earnings, per capita | ✅ Active (MVP) |
| `gold.economics_labor_wide` | Employment, wages, unemployment | Deferred |
| `gold.affordability_wide` | Rent burden, value-to-income ratios | Deferred |
| `gold.economics_gdp_wide` | Regional GDP | Deferred |
| `gold.migration_wide` | Domestic migration flows | Deferred |
| `gold.transport_built_form_wide` | Transit, density, walkability | Deferred |
| `gold.tx_isd_metrics` | Texas school district metrics | Deferred |

All Gold tables share a common grain: `one row per geo_level + geo_id + year`.

Common join keys across tables: `geo_id`, `geo_level`, `year`.

---

## Geography Model

**Supported levels:** `region`, `division`, `state`, `cbsa`, `county`
**Deferred:** `zcta`, `census_tract`

**48-state rule (reference dashboard):** Contiguous US + DC only. Exclude Alaska (FIPS 02), Hawaii (FIPS 15), territories (FIPS ≥ 57 except DC=11).

**Hierarchy:**
```
county → cbsa (partial: not all counties are in a CBSA)
county → state
state → division → region
```

Region/Division geometries: dissolved from `geo.states` via `silver.xwalk_state_region`. No separate geometry table.

Geometry tables in DuckDB: `geo.states`, `geo.counties`, `geo.cbsas` — use `ST_AsGeoJSON(geom)` via DuckDB spatial extension.

---

## Application Pipeline (end-to-end)

```
User question
    ↓
IntentParser (app/intent/parser.py)
  - LLM call with system prompt built from semantic layer catalogs + few-shot examples
  - Returns QueryPlan (Pydantic) or ClarificationRequest
    ↓ (if QueryPlan)
QueryPlanner (app/query/planner.py)
  - Validates plan against semantic layer
  - Returns PlannedQuery
    ↓
QueryGenerator (app/query/generator.py)
  - Selects template from query_templates.yml
  - Renders SQL with Jinja2
    ↓
QueryValidator (app/query/validator.py)
  - Checks: approved tables, approved metrics, approved joins, read-only, valid geo level
    ↓
QueryExecutor (app/query/executor.py)
  - Runs against DuckDB; returns pandas DataFrame
    ↓
ResultProfiler (app/charts/profiler.py)
  - Infers result shape: row_count, has_time_series, dimension_count, inferred_shape
    ↓
ChartSelector (app/charts/selector.py)
  - Looks up chart_rules.yml → returns chart type
    ↓
ChartRenderer (app/charts/renderer.py)
  - subprocess: writes CSV + JSON config → calls Rscript → returns PNG path
    ↓
ResponseAssembler (app/response/assembler.py)
  - Assembles answer text, chart path, table, SQL, assumptions
    ↓
OrchestrationResult
```

---

## Supported Question Types and SQL Templates

| Question type | Template | Chart type(s) |
|---|---|---|
| `ranking` | Top/bottom N by metric, optional geo filter | Bar (horizontal) |
| `trend` | Metric over time for one or more geos | Line |
| `compare_selected` | Metric across user-specified geos | Bar or slopegraph |
| `distribution` | Spread of metric across all geos at a grain | Boxplot or histogram |
| `benchmark` | Target geo vs. US / region / state / peers | Bar with reference line |
| `growth` | Point-in-time growth over N years (LAG or CTE) | Bar |

Growth windows: 1yr, 3yr, 5yr. Default: 5yr.

---

## QueryPlan Schema

```python
class QueryPlan(BaseModel):
    question_type: str        # ranking, trend, compare_selected, distribution, benchmark, growth
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

---

## QA Framework Summary

**QA layers (evaluated per run):**
1. Intent QA — correct question_type, metric, geo_level, geo_ids
2. Query Plan QA — complete + valid plan
3. SQL QA — SQL matches plan, correct table/column, read-only
4. Data / Result QA — rows returned, plausible values
5. Chart QA — appropriate type, correct labels and formatting
6. Answer Text QA — accurate, specific, non-hallucinated
7. End-to-End Regression QA — consistency across known prompts

**Prompt categories in `qa/qa_prompt_library.yml`:**
- `golden` — exact regression anchors (run deterministically)
- `provider_paraphrase` — reworded variants to test LLM generalization (run with `--force-provider`)
- `clarification` — underspecified prompts to test clarification behavior

**Current QA scores (Loop 3, 2026-05-02, 20 cases):**
10 pass / 6 partial / 4 fail

**Known weak areas:** benchmark cases, growth-with-explicit-template (model prefers precomputed growth columns), clarification message language (too technical).

**Artifact saved per run:** `qa_run.json` (canonical QA record), `query_plan.json`, `result.sql`, `result.csv`, `chart.png`, `answer.txt`

---

## Reference Dashboard

`reference_dashboard/data_explorer.py` — a separate Streamlit app (not the chatbot). Used as a QA ground-truth lens on the Gold layer.

**What it does:** Filter by geo level, subject area, KPI, year, and KPI range. Renders a Plotly choropleth map and a formatted, downloadable data table. Growth columns always included.

**Launch:** `.venv/bin/python -m streamlit run reference_dashboard/data_explorer.py`

**Status:** Complete (all 5 sprints done).

---

## Analysis Folder

`analysis/` — short-form manual analyses for quick insights. Structured as `analysis/<topic>/` with SQL, R, and chart outputs. Intended as a leading indicator for new chatbot question types. May be deeper or more tuned than the chatbot question library.

---

## Key Constraints and Guardrails

- **Read-only queries only.** The validator rejects any non-SELECT SQL.
- **Approved tables only.** No ad-hoc table references — everything must be in `table_catalog.yml` with `status: active`.
- **LLM does not write SQL.** It produces a structured plan; the template engine writes SQL.
- **Charts come from the visual library.** No ad-hoc Plotly/matplotlib in the chatbot response path.
- **Clarify rather than improvise.** Underspecified questions get a clarification request, not a guess.
- **MVP geo scope:** No ZCTA or census tract. No maps in the chatbot (choropleth deferred to v1.1).

---

## Open Work (as of 2026-05-10)

| Item | Phase | Notes |
|---|---|---|
| Streamlit chat UI | 5 | `frontend/streamlit_app.py` — chat input, response history, chart + table + SQL display, clarification routing, session state, follow-up merging |
| MotherDuck migration | 6 | Export local Gold tables; update `DB_CONNECTION` |
| Streamlit Cloud deploy | 6 | `packages.txt` (r-base), `setup.sh` (R packages), secrets for Groq + MotherDuck |
| Benchmark QA fixes | Loop 4 | `gold.benchmark_reference` view exists; benchmark template still weakest area |
| Clarification message language | Loop 4 | Field names exposed to users should map to plain English |
| Growth template forcing | Loop 4 | Model prefers precomputed growth columns over explicit growth template |
| `analysis/` expansion | Ongoing | Add more manual analyses as chatbot leading indicators |

---

## Environment Variables

```bash
# Data
DB_CONNECTION=/Users/danberle/Documents/projects/data/duckdb/metro_deep_dive.duckdb

# LLM — local dev
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# LLM — production
LLM_PROVIDER=groq
GROQ_API_KEY=...
```
