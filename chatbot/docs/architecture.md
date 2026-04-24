# Architecture
## US Demographic and Economic Analytics Chatbot

## 1. System Overview

The application is a controlled analytics chatbot that converts natural language questions into trusted SQL, standardized visuals, and concise analytical answers.

The MVP architecture is designed to optimize for reliability, transparency, and low technical debt. It uses Python for orchestration, DuckDB as the initial analytical engine, Streamlit for the frontend, and R for chart rendering because the visual library already exists there.

The system should be modular so it can later evolve from a shareable demo app into a more production ready deployment without major rework.

## 2. Core Components

### Frontend
Streamlit based interface for:
- question input
- result display
- chart display
- result table display
- SQL inspection
- assumptions and definitions
- expandable technical details

### Application Orchestrator
Python service responsible for:
- question parsing
- follow up state handling
- structured query planning
- SQL template selection
- SQL generation
- SQL validation
- query execution
- chart request generation
- final response assembly
- run logging

### LLM Layer
Single provider first, with an open source model and local inference as the preferred direction.

Responsibilities:
- parse the user question into a structured request
- identify ambiguity and trigger clarification
- help choose the right query pattern
- assist with chart recommendation
- draft the final concise answer

The LLM should not directly execute SQL or invent schema logic.

### Semantic and Query Layer
A controlled metadata layer that defines:
- approved tables and views
- approved metrics
- approved joins
- geography rules
- benchmark rules
- query templates
- chart eligibility rules

This layer is the main guardrail for correctness.

### Data Layer
DuckDB serves as the initial analytical engine for the Gold layer.

This layer should be abstracted behind a query service so the storage engine can later be swapped for Postgres or a cloud warehouse if needed.

### Visualization Layer
R based rendering layer using the existing visual library.

Python should pass a structured chart request and result dataset to R, and R should return a rendered visual artifact for the frontend.

### Logging Layer
Store:
- user question
- structured query plan
- generated SQL
- execution errors

This is sufficient for MVP debugging and evaluation.

## 3. End to End Request Flow

1. User submits a question in the Streamlit app
2. Python orchestrator checks session context for prior turn state
3. LLM parses the question into a structured request
4. If the request is ambiguous but solvable, the system asks a clarifying question
5. If the request is clear, the orchestrator maps it to approved semantic metadata
6. The system selects a supported query pattern or template
7. SQL is generated from structured inputs plus approved templates
8. SQL validator checks:
   - approved tables only
   - approved metrics only
   - approved joins only
   - supported filters and grains only
9. DuckDB executes the validated query
10. The result is profiled to determine output shape
11. The system selects an approved chart type
12. Python sends the result and chart config to R
13. R renders the chart using the visual library
14. Python assembles:
   - short answer
   - chart
   - result table
   - SQL
   - assumptions and definitions
   - expandable technical details
15. The run artifacts are logged

## 4. Decision Logic and Guardrails

### Query Generation Approach
The system uses a hybrid approach:
- LLM creates a structured query plan
- application logic selects a query template
- template parameters are filled from the structured plan

This avoids fully free form SQL generation.

### Guardrails
The MVP enforces strict controls:
- only approved tables and views
- only approved metrics
- only approved joins
- unsupported requests are rejected or clarified rather than improvised

### Clarification Logic
When the system cannot answer directly but can recover with more specificity, it should ask a clarifying question.

Common clarification cases:
- missing geography grain
- ambiguous metric name
- unclear benchmark level
- undefined peer group
- unsupported time logic

### Chart Selection Logic
Chart selection should be rule driven first, with limited LLM assistance if needed.

The system should map result shapes and question types to approved chart types from the visual library.

### Unsupported Requests
If a request falls outside supported scope:
- ask a clarifying question if the request can be narrowed into scope
- otherwise return a guided unsupported response with a suggested rewrite

## 5. State and Session Handling

The system should support lightweight conversational follow ups.

### Session State to Retain
For the active analysis thread, retain:
- metric or measure
- geography grain
- geography filters
- benchmark type
- time window
- growth window
- chart intent where applicable

This allows follow ups such as:
- show counties instead
- filter to the Northeast
- compare against the US
- use 3 year growth instead

### Peer Group Handling
Peer groups in MVP should support:
- selection from a table backed by peer mappings in the Gold layer
- custom manual peer submission by geography name

Peer mapping should be designed as a data layer asset, not only as app configuration, so it can scale and stay consistent across analyses.

## 6. Deployment Shape

The MVP should be structured as a shareable cloud demo app.

### Recommended Shape
- Streamlit frontend
- Python orchestration layer
- DuckDB packaged or mounted with the Gold layer
- R runtime available for chart rendering
- open source LLM accessed through a local inference friendly interface where feasible

### Storage Strategy
DuckDB is acceptable for MVP and demo deployment if:
- data size remains manageable
- concurrency needs are low
- refresh workflows are simple

The architecture should isolate data access so migration to Postgres or a cloud warehouse remains straightforward later.

### Model Strategy
The initial design should assume one model provider path, with a bias toward local inference to support learning and reduce dependency on external APIs.

The model integration should still be wrapped behind a small interface so the model can be swapped later without changing the rest of the app.

## 7. Open Technical Decisions

The following decisions still need to be resolved:

- how Python will call R for rendering
- which open source model to use first
- whether inference will run fully local or through a hosted endpoint during early development
- the exact shape of the structured query plan schema
- how benchmark logic is encoded for each geography level
- how peer mapping tables are defined and maintained
- how technical details are exposed in the UI
- how DuckDB is packaged and refreshed in demo deployment