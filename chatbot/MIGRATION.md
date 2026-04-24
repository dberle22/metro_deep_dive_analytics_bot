# Chatbot Repo Migration Guide

This document captures everything needed to stand up the US Demographic & Economic Analytics Chatbot as a standalone repository. It covers the project overview, architectural context, data sources, and a full inventory of files to copy from `metro_deep_dive`.

---

## Project Overview

The chatbot is a **constrained analytical copilot** that answers natural language questions about US demographic and economic data. Users ask questions like:

- *"Which midsize metros had the fastest population growth over the last 5 years?"*
- *"Show counties in Florida with high rent growth and lower home values."*
- *"Compare labor force participation and median income across Northeast states."*

The system returns a written answer, a chart (from the visual library), a supporting data table, the SQL used, and metric definitions — keeping analytics transparent and reproducible.

**Core design principles:**
- Reliability over openness: narrow, well-tested scope
- Transparent analytics: SQL is always visible to the user
- Controlled SQL generation: no free-form LLM SQL invention
- Visual consistency: all outputs follow visual library standards

**Primary tech stack:**
- **Backend**: Python + FastAPI for orchestration
- **Data layer**: DuckDB querying the Gold layer (Parquet or `.duckdb` file)
- **LLM layer**: Claude API for intent parsing, query planning, chart selection, response generation
- **Visualization**: R-based rendering using the visual library (`ggplot2`)
- **Frontend**: Streamlit (MVP)

---

## Architectural Context

The chatbot sits on top of a three-layer **medallion data architecture** built in the parent `metro_deep_dive` repo:

```
Raw Sources (APIs/CSV)
      ↓
  Staging Layer   ← source-shaped, landed tables
      ↓
  Silver Layer    ← standardized, lightly transformed, analysis-ready
      ↓
  Gold Layer      ← curated cross-domain marts, chatbot queries here
      ↓
  Semantic Layer  ← metric catalog, table catalog, join rules (to be built)
      ↓
  Chatbot App     ← intent parsing → SQL → chart → response
```

The chatbot only queries the **Gold layer** via DuckDB. All ETL runs upstream in the parent repo and produces the Gold tables the chatbot depends on. The new repo will not re-implement ETL but should include the Gold SQL definitions for reference and for any future need to regenerate data.

### Geography Hierarchy

```
Census Tract → County → CBSA → State → Division → Region → US
```

All Gold tables carry `(geo_level, geo_id, geo_name, year)` as the primary key grain, enabling consistent joins across domains.

### MVP Supported Scope

| Dimension | MVP Scope |
|---|---|
| Geography grains | Region, State, CBSA, County, Census Tract |
| Subject areas | Population, Income/Earnings, Housing/Rent, Labor Market, Education, Migration |
| Chart types | Bar, Line, Scatter, Choropleth, Boxplot, Histogram, Heatmap Table, Highlight Context Map |
| Question types | Rankings, Trends, Comparisons, Distributions, Scatter/Relationship, Basic Maps, Benchmarking |

---

## Data Sources

The chatbot queries Gold layer tables produced from these upstream sources. No direct API calls are made by the chatbot itself — all data is pre-processed in the parent repo.

| Source | What It Provides | Gold Tables Used |
|---|---|---|
| **ACS (Census Bureau)** | Population, age, race, income, housing, labor, education, migration, transport, social infrastructure — 5-year rolling estimates via `tidycensus` | `gold.population_demographics`, `gold.housing_core_wide`, `gold.migration_wide`, `gold.economics_income_wide`, `gold.economics_labor_wide`, `gold.transport_built_form_wide` |
| **BEA Regional API** | GDP by metro, personal income, Regional Price Parity — requires API key | `gold.economics_gdp_wide`, `gold.economics_income_wide`, `gold.economics_industry_wide` |
| **BLS API** | Labor force, unemployment (LAUS), covered employment and wages (QCEW) | `gold.economics_labor_wide` |
| **HUD** | Fair Market Rent (FMR), rent burden (CHAS) | `gold.affordability_wide` |
| **Zillow** | ZHVI (home values), ZORI (observed rent index) — public CSVs | `gold.housing_core_wide`, `gold.affordability_wide` |
| **BPS (Census Bureau)** | Building permits by metro | Integrated into `gold.housing_core_wide` |
| **IRS Migration** | County-to-county migration flows | `gold.migration_wide` (planned v1.1) |
| **TIGER/Line + Census** | Geography geometries and crosswalk tables | `geo.*` dimension tables, choropleth rendering |

### DuckDB Connection

The chatbot connects to a local or hosted DuckDB file:
```
/path/to/metro_deep_dive.duckdb
```
Schemas in scope: `gold`, `geo`

---

## Files to Copy

### 1. Chatbot Product Docs (`products/chatbot/`)

Copy the entire directory. This is the primary product definition.

```
products/chatbot/
├── README.md
├── us_demographic_economic_analytics_chatbot_spec.md   # Full product spec (776 lines)
├── docs/
│   ├── architecture.md                                 # System design and request flow
│   ├── semantic_layer.md                               # Metadata contract definitions
│   ├── product_spec.md                                 # Concise product requirements
│   ├── frontend.md                                     # UI/UX specifications
│   └── visual_library_integration.md                  # Chart system integration
├── app/                                                # App code (copy as-is)
├── data/
│   └── local_configs.yml                              # Local config template
└── tests/                                             # Test harness
```

### 2. Visual Library (`visual_library/`)

Copy the entire directory. The chatbot renders all charts through this library.

```
visual_library/
├── README.md
├── charts/                        # 15+ chart type folders (spec, sample SQL, sample output)
├── shared/
│   ├── standards.R               # Canonical color, font, formatting rules
│   ├── chart_utils.R             # Axis labels, legends, annotations
│   ├── data_contracts.R          # Schema validation functions
│   ├── scatter_query_helpers.R
│   ├── sql_patterns.md
│   ├── prep/                     # 16 data prep functions (one per chart type)
│   │   ├── prep_bar.R
│   │   ├── prep_line.R
│   │   ├── prep_scatter.R
│   │   ├── prep_choropleth.R
│   │   ├── prep_boxplot.R
│   │   ├── prep_heatmap_table.R
│   │   ├── prep_highlight_context_map.R
│   │   └── [9 additional prep functions]
│   └── render/                   # 16 render functions (one per chart type)
│       ├── render_bar.R
│       ├── render_line.R
│       ├── render_scatter.R
│       ├── render_choropleth.R
│       ├── render_boxplot.R
│       ├── render_heatmap_table.R
│       ├── render_highlight_context_map.R
│       └── [9 additional render functions]
├── contracts/
│   ├── data_contract_dictionary.md
│   ├── visual_contract_line.csv
│   └── visual_contract_scatter.csv
├── config/
│   └── visual_registry.yml       # Registry of all 17 chart types with status
├── templates/
│   └── chart_spec_template.md
└── docs/
    ├── visual_style_guide_and_standards.md   # Source of truth for visual rules
    ├── sample_library.md                     # Chart catalog and example questions
    ├── benchmark_defaults.md
    └── agent_skill_benchmark.md
```

### 3. Gold Layer SQL Definitions (`scripts/etl/gold/`)

Copy all Gold SQL files for reference and data regeneration. These define the tables the chatbot queries.

```
scripts/etl/gold/
├── gold_population_wide.sql          # Demographics base mart
├── gold_housing_core.sql             # Housing units, tenure, costs, structure
├── gold_affordability_wide.sql       # Rent-to-income, value-to-income, FMR gap
├── gold_migration_wide.sql           # ACS mobility and nativity flows
├── gold_transport_built_form_wide.sql
├── gold_economy_income.sql           # Income KPIs, per capita income
├── gold_economy_gdp.sql              # Regional GDP, real growth rates
├── gold_economy_labor.sql            # Employment, wages, unemployment
├── gold_economy_industry.sql         # BEA sector shares, HHI concentration
└── gold_economy_wide.sql             # Combined economics mart
```

> Note: `gold_tx_school_district.sql` is TX-specific and not needed for the chatbot.

### 4. Data Dictionary (`schemas/data_dictionary/`)

Copy the full directory. It contains `.md` and `.yml` definitions for every Gold and Silver table — field names, types, descriptions, grain, lineage, and caveats. This is the primary reference for building the semantic layer (metric catalog, table catalog) and for grounding the LLM in what data is actually available.

```
schemas/data_dictionary/
├── README.md
├── agent.md                           # How to use the dictionary as an agent/LLM context
├── layers/
│   ├── gold/                          # One .md + .yml per Gold table (9 chatbot-relevant tables)
│   │   ├── gold__population_demographics.{md,yml}
│   │   ├── gold__housing_core_wide.{md,yml}
│   │   ├── gold__affordability_wide.{md,yml}
│   │   ├── gold__migration_wide.{md,yml}
│   │   ├── gold__transport_built_form_wide.{md,yml}
│   │   ├── gold__economics_income_wide.{md,yml}
│   │   ├── gold__economics_gdp_wide.{md,yml}
│   │   ├── gold__economics_labor_wide.{md,yml}
│   │   ├── gold__economics_industry_wide.{md,yml}
│   │   └── checklist.md
│   └── silver/                        # Silver table definitions (source lineage reference)
├── docs/
│   ├── governance/                    # Data governance rules and standards
│   └── layer_guides/                  # How each layer is structured and maintained
└── artifacts/
    ├── audits/
    ├── backlog/
    └── coverage/                      # Coverage reports across sources and geographies
```

> The TX-specific entries (`gold__tx_isd_metrics`) can be skipped.

### 5. Key Reference Docs

| File | Why |
|---|---|
| `DBDesign.md` | Full database architecture, table schemas, implementation status, and planned future tables |
| `README.md` | Top-level project context and repo orientation |
| `documents/repo_taxonomy.md` | Goal-based taxonomy of repo structure |
| `config/visual_registry.yml` | Authoritative chart registry (status, priority, file references) |

---

## Do NOT Copy

| What | Why |
|---|---|
| `.Renviron` | Contains personal API keys (BEA, Census) and local data paths |
| `data/` directories | External data — regenerate from ETL |
| All staging ETL scripts (`scripts/etl/staging/`) | Not needed in chatbot repo; ETL runs upstream |
| All silver ETL scripts (`scripts/etl/silver/`) | Same — upstream concern |
| `notebooks/` | Analysis notebooks; not part of chatbot product |
| `products/rof/` | Separate product |
| `.Rproj.user/` | Local IDE state |
| Generated `outputs/` | Regenerable artifacts |

---

## Open Questions Before Build

These are documented in the spec but need decisions before implementation begins:

1. **Python-to-R rendering bridge** — How does the Python backend call R render functions and receive the chart artifact? (Options: subprocess, `rpy2`, separate R microservice)
2. **SQL generation approach** — Fully templated (safe, limited) vs. semi-templated with LLM slot-filling (flexible, riskier)
3. **Unsupported question handling** — Graceful fallback message or clarification prompt?
4. **Session state** — Does the chatbot retain context across follow-up questions in a session?
5. **Semantic layer implementation** — Metric catalog and table catalog exist in spec form; they need to be implemented as actual data structures (YAML files or a small DB table)
6. **Hosting** — Local DuckDB file vs. hosted DuckDB (MotherDuck) vs. other

---

## Suggested New Repo Structure

```
chatbot/
├── README.md
├── app/                          # Python FastAPI backend
│   ├── main.py
│   ├── intent/                   # LLM intent parsing
│   ├── query/                    # SQL generation and execution
│   ├── response/                 # Answer generation
│   └── config/
├── frontend/                     # Streamlit UI
├── semantic_layer/               # Metric catalog, table catalog, join rules, chart rules
│   ├── metric_catalog.yml
│   ├── table_catalog.yml
│   ├── join_rules.yml
│   └── chart_rules.yml
├── visual_library/               # Copied from metro_deep_dive
├── sql/
│   └── gold/                     # Gold DDL SQL files (copied from metro_deep_dive)
├── data_dictionary/              # Copied from schemas/data_dictionary/
├── docs/                         # Copied from products/chatbot/docs/
│   ├── architecture.md
│   ├── semantic_layer.md
│   ├── product_spec.md
│   ├── frontend.md
│   └── visual_library_integration.md
├── tests/
├── .env.example                  # Template for DB path and API keys (no actual values)
└── requirements.txt
```
