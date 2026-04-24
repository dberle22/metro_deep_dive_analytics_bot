# US Demographic and Economic Analytics Chatbot

An analytics chatbot for US demographic and economic data that converts natural language questions into trusted SQL, structured answers, and standardized visuals.

The application is built around a curated Gold layer of normalized public data, a reusable visual library, and a controlled query pipeline that prioritizes reliability, transparency, and analytical usefulness.

## Overview

This project is designed to let a user ask questions such as:

- Which midsize metros had the fastest population growth over the last 5 years?
- Show counties in Florida with high rent growth and lower home values
- Compare labor force participation and median income across Northeast states
- Map Census Tracts in a metro by educational attainment

The system interprets the question, maps it to approved data assets, generates and validates SQL, executes the query, chooses a chart type, renders a visual, and returns a concise analytical response.

## Core Goals

- Make curated US demographic and economic data easier to explore through natural language
- Generate reliable SQL against approved Gold layer tables
- Standardize charts using a reusable visual library
- Return transparent, inspectable outputs including SQL and assumptions
- Create a foundation for future analytical copilots and data apps

## What This App Does

The chatbot workflow is:

1. Accept a user question
2. Parse intent, metrics, geography, and timeframe
3. Build a structured query plan
4. Generate SQL from approved semantic metadata
5. Validate SQL for correctness and safety
6. Execute the query against the Gold layer
7. Profile the result shape
8. Select an appropriate chart type
9. Render the chart using the visual library
10. Return:
   - a concise written answer
   - a chart
   - a supporting table
   - the SQL used
   - assumptions or definitions where relevant

## Key Inputs

This application is built on three major assets:

### 1. Gold Layer
A curated analytical layer that normalizes public data sources such as:

- ACS
- BEA
- BLS
- HUD
- Zillow
- and other approved public datasets

The data spans multiple geographic levels, from Census Tracts up to Regions.

### 2. Visual Library
A standardized charting system with visual rules and reusable functions across multiple chart types.

Examples include:
- ranked bar charts
- line charts
- scatterplots
- choropleths
- boxplots
- heatmap tables
- highlight maps

### 3. Example Question Library
A training and evaluation set of:
- natural language questions
- sample SQL
- expected chart types
- expected outputs

This library helps bootstrap prompting, template selection, testing, and QA.

## Product Principles

### Reliability over openness
The system should answer a narrower set of questions well rather than support unlimited free form analysis poorly.

### Transparent analytics
Users should be able to inspect the SQL, assumptions, and metric definitions behind each answer.

### Controlled SQL generation
The LLM should not have unconstrained freedom to invent tables, joins, or fields. Query generation should be grounded in metadata and approved templates.

### Visual consistency
All visual outputs should follow the project’s chart standards and rendering contracts.

### Iterative scope
The first version should support a limited set of subject areas, geographic grains, and chart types, then expand over time.

## Proposed MVP Scope

### Supported question types
- ranking and top or bottom lists
- trends over time
- comparisons across geographies
- distributions
- scatter or relationship questions
- basic map driven questions
- benchmark comparisons

### Suggested geography levels
- Region
- State
- CBSA
- County
- Census Tract

### Suggested subject areas
- population
- income and earnings
- housing and rent
- labor market
- education
- migration or price parity if stable in the Gold layer

### Suggested chart types
- bar
- line
- scatter
- choropleth
- boxplot
- histogram
- heatmap table
- highlight context map

## High Level Architecture

The recommended system has five major layers.

### 1. Frontend
A lightweight chat style interface where users can:
- ask questions
- review answers
- inspect charts
- inspect SQL
- review assumptions and metric definitions

Possible options:
- Streamlit for fastest MVP
- Shiny if the project remains closely tied to R
- Next.js for a more production ready frontend

### 2. Application Backend
Handles:
- question interpretation
- semantic planning
- SQL generation
- SQL validation
- execution orchestration
- chart selection
- answer generation

Recommended option:
- Python with FastAPI

### 3. Data Access Layer
Provides safe, structured access to the Gold layer through:
- approved schemas
- table metadata
- join rules
- metric definitions
- geography rules

### 4. LLM Orchestration Layer
The LLM should be used for:
- intent parsing
- query planning
- constrained SQL generation
- chart selection
- response writing

It should not directly control execution without validation.

### 5. Visualization Layer
A rendering layer that accepts chart type plus config and produces charts using the project’s visual library.

## Recommended Query Pipeline

The core execution pipeline should follow this flow:

1. User question
2. Intent and entity parsing
3. Structured request object
4. Semantic mapping to approved metadata
5. SQL generation from templates and rules
6. SQL validation
7. Query execution
8. Result profiling
9. Chart recommendation
10. Chart rendering
11. Final response generation

## Semantic Layer Requirements

A machine readable semantic contract is one of the most important parts of the project.

The project should maintain metadata for:

### Metric Catalog
For each metric:
- name
- definition
- formula
- valid grains
- valid time grains
- source table
- caveats

### Table Catalog
For each table:
- schema
- name
- description
- grain
- time field
- geography fields
- subject area

### Join Catalog
For each allowed join:
- join path
- keys
- cardinality notes
- grain compatibility

### Geography Hierarchy Catalog
Defines relationships such as:
- Tract to County
- County to CBSA
- State to Region

### Chart Recommendation Rules
Maps question types and result shapes to allowed chart types.

### Example Library
Stores tagged examples for prompting and QA:
- question
- query pattern
- SQL
- chart type
- expected output shape

## Recommended Tech Stack

This is the recommended starting stack for an MVP:

- **Backend:** Python + FastAPI
- **Frontend:** Streamlit
- **Data Access:** DuckDB, Postgres, Snowflake, or another approved analytical store
- **LLM Orchestration:** Prompt chain with structured outputs and validation
- **Visualization:** Existing R visual library if already mature, otherwise Python chart layer
- **Testing:** SQL regression tests, prompt evaluation set, chart QA set

## Repository Structure

```text
.
├── README.md
├── docs/
│   ├── product_spec.md
│   ├── architecture.md
│   ├── semantic_layer.md
│   ├── frontend.md
│   ├── visual_library_integration.md
│   ├── roadmap.md
│   └── decisions.md
├── data/
│   ├── sample_questions/
│   ├── metric_catalog/
│   ├── table_catalog/
│   ├── join_catalog/
│   └── geography_catalog/
├── app/
│   ├── frontend/
│   ├── backend/
│   ├── llm/
│   ├── sql/
│   ├── charts/
│   └── services/
├── tests/
│   ├── prompts/
│   ├── sql/
│   ├── charts/
│   └── integration/
└── notebooks/