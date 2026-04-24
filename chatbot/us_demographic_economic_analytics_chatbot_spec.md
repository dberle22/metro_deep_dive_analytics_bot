# US Demographic and Economic Analytics Chatbot

## Product Spec and Delivery Plan

## 1. Product Summary

Build a web application where a user can ask natural language questions about US demographic and economic conditions across geographies and receive:

- a concise written answer
- a chart rendered using the visual library
- a supporting results table
- the SQL used to answer the question
- optional assumptions and metric definitions

The application sits on top of the Metro Deep Dive DuckDB Gold layer.

This is a controlled analytics copilot rather than a fully open ended chat product. The product value comes from trustworthy answers, explainable SQL, and standardized visual outputs.

---

## 2. Product Goals

### Primary Goal
Allow users to ask natural language questions about US demographic and economic data and receive a reliable answer with a strong chart.

### Secondary Goals
- Reduce the technical effort required to query curated data
- Standardize visual outputs through the visual library
- Create a repeatable workflow that can later power saved analyses, deeper research workflows, and more advanced agents

### Non Goals for V1
- Open web search
- Fully free form statistical analysis
- Arbitrary end user data uploads
- Rich long term conversational memory
- Full dashboard builder

---

## 3. Existing Assets

The application already has strong foundational inputs:

1. **Gold Layer of US Demographic and Economic Data**  
   Curated analytical tables that normalize ACS, BEA, BLS, and similar sources across multiple geographies ranging from Census Tracts to Census Regions.

2. **Visual Library**  
   Visual standards and functions for approximately 15 chart types.

3. **Question and Training Library**  
   A set of example questions, sample SQL, and charts that can be used for training, prompting, testing, and evaluation.

The core product task is to operationalize these assets into a reliable chatbot workflow.

---

## 4. Core User Workflow

### User Flow
1. User enters a question
2. System interprets the question and identifies intent, geography, metrics, and timeframe
3. System maps the request to the approved semantic layer
4. System generates SQL against approved Gold tables
5. System validates SQL for safety and semantic correctness
6. System executes the query
7. System profiles the results
8. System selects the most appropriate chart type
9. System renders the visual using the visual library
10. System returns:
   - short written answer
   - chart
   - supporting table
   - SQL
   - assumptions or metric notes if relevant

### Example
**Question:**  
Which midsize metros had the fastest population growth and median rent growth over the last 5 years?

**Response:**
- short analytical summary
- chart
- key result table
- SQL used
- note about how midsize metros and 5 year growth were defined

---

## 5. Product Requirements

## 5.1 Functional Requirements

### A. Natural Language Question Intake
The system should extract or infer:
- question intent
- geography grain
- geography filter
- subject area
- metric or KPI
- time window
- comparison logic
- whether the user wants ranking, trend, distribution, relationship, or mapping

### B. Semantic Query Planner
The system should first convert the question into a structured request object before generating SQL.

Example structure:

```json
{
  "intent": "ranking",
  "subject_area": "population",
  "metric": "pop_growth_5yr",
  "geo_grain": "cbsa",
  "geo_filter": {"region": "South"},
  "time_range": {"start_year": 2019, "end_year": 2024},
  "sort": "desc",
  "limit": 15
}
```

This step is essential for reliability and explainability.

### C. SQL Generation
The system should generate SQL only from approved tables, views, metrics, and join rules.

### D. SQL Validation
Before execution, validate that:
- only approved schemas and tables are used
- grain is appropriate
- requested fields exist
- joins are allowed
- the query is read only
- filters and row limits are reasonable

### E. Result Shaping
After execution, the system should profile:
- row count
- number of dimensions and measures
- presence of time series
- presence of geography columns
- ranking or comparison structure

### F. Chart Selection Engine
Based on question intent and result shape, choose the best chart from the approved visual library.

### G. Chart Rendering
Use a fixed rendering contract so the LLM recommends a chart type and config, while code handles the actual rendering.

### H. Written Answer Generation
Generate:
- concise narrative summary
- key findings
- assumptions if needed
- metric definitions on demand

### I. Transparency Features
Strongly recommended for trust and debugging:
- SQL shown to the user
- tables used
- metric definitions
- chart rationale
- assumptions or caveats

---

## 6. Recommended V1 Scope

Keep V1 narrow, reliable, and easy to test.

### Supported Question Types
- Top and bottom rankings
- Trend over time
- Compare selected geographies
- Scatter or relationship analysis
- Distribution analysis
- Basic map questions
- Benchmarking versus national, regional, or peer groups

### Supported Geography Grains
Recommended initial set:
- Census Region
- State
- CBSA
- County
- Census Tract

### Supported Subject Areas
Recommended initial set:
- Population
- Income and earnings
- Housing and rent
- Labor market
- Education
- Migration or price parity if already stable in the Gold layer

### Recommended Chart Types for V1
Start with 6 to 8 high value chart types:
- Bar chart
- Line chart
- Scatter plot
- Choropleth map
- Boxplot
- Histogram
- Heatmap table
- Highlight or context map

---

## 7. Product Architecture

## 7.1 High Level Architecture

### Frontend
A simple chat style interface with:
- input box
- answer panel
- chart panel
- results table
- SQL panel
- assumptions and definitions panel

### Application Backend
Responsible for:
- question parsing
- semantic planning
- SQL generation
- SQL validation
- query execution
- chart selection
- chart rendering orchestration
- answer formatting

### Data Access Layer
Provides controlled access to the Gold layer and should expose:
- approved schemas and tables
- metadata registry
- metric definitions
- geography hierarchy rules
- safe query execution

### LLM Orchestration Layer
Recommended role of the LLM:
- classify the question
- build a structured analysis plan
- generate SQL within metadata constraints
- choose the chart type
- generate the final narrative answer

### Metadata and Semantic Layer
This is one of the most important product assets. It should include machine readable metadata for:
- tables
- columns
- metrics
- allowed joins
- geography grains
- time grains
- example questions
- chart suitability rules

### Visualization Layer
The visual library should expose a rendering contract such as:
- input dataframe
- chart type
- x and y variables
- grouping or color logic
- title and subtitle
- annotation instructions
- output object for the frontend

---

## 8. Most Important Architectural Decisions

### 1. How constrained should SQL generation be?
**Recommendation:** Very constrained.

Do not allow the model to invent joins, fields, or table paths. Use:
- approved tables and views
- approved metrics
- approved joins
- structured request objects
- SQL generation templates where possible

### 2. Should SQL be generated directly or through semantic templates?
**Recommendation:** Use a hybrid approach.

The LLM should interpret the question and fill in a structured query pattern, not invent everything from scratch.

### 3. Should chart rendering be in Python or R?
**Recommendation:** Use the language that minimizes rework.

If the visual library is already substantially implemented in R, keep chart rendering in R for V1 and call it from the backend. If not, consider Python for simplicity.

### 4. Should V1 support multi turn conversations?
**Recommendation:** Only lightly.

Support simple follow ups such as:
- now show only the Northeast
- compare that against the national median
- make that counties instead of metros

Avoid building rich memory or full conversation state at the start.

### 5. Should users see the SQL?
**Recommendation:** Yes.

This is an analytical product. Transparency builds trust.

### 6. Should V1 support all metrics and all geographies?
**Recommendation:** No.

Start with a curated subset that is well documented and well tested.

---

## 9. Suggested System Pipeline

### Step 1. Question Understanding
Input: natural language question  
Output: structured request object

### Step 2. Semantic Planning
Map the request to:
- subject area
- metric
- geography grain
- filters
- table or view
- expected result shape
- candidate chart types

### Step 3. SQL Generation
Generate SQL only from approved metadata and query patterns.

### Step 4. SQL Validation
Run rule based validation before execution.

### Step 5. Query Execution
Run read only SQL against the Gold layer.

### Step 6. Result Interpretation
Determine whether the result represents a ranking, trend, comparison, distribution, or map ready dataset.

### Step 7. Chart Selection
Apply deterministic chart selection logic first, with LLM help inside approved options.

### Step 8. Chart Rendering
Use the visual library to render the final visual.

### Step 9. Answer Generation
Return the chart, summary, result table, SQL, and assumptions if needed.

---

## 10. Data and Semantic Assets Required

The app will need a machine readable semantic contract on top of the Gold layer.

### Required Metadata Components

#### A. Metric Catalog
For each metric:
- metric name
- display name
- description
- formula
- source table
- valid geography grains
- valid time grains
- caveats

#### B. Table Catalog
For each table:
- schema
- table name
- description
- grain
- subject area
- available dimensions
- available measures
- time field
- geography fields

#### C. Join Catalog
- allowed joins
- join keys
- grain compatibility
- one to one or one to many notes

#### D. Geography Hierarchy Catalog
- tract to county
- county to CBSA
- state to region
- and other supported hierarchies

#### E. Chart Recommendation Catalog
Map question intents and result shapes to approved chart types.

#### F. Example Question Library
Store example questions in structured form with tags for:
- intent
- metric family
- geography grain
- chart type
- complexity

This will help with prompting, retrieval, evaluation, and regression testing.

---

## 11. Frontend Spec

## Recommended V1 Interface

### Main Components
- chat input
- response history
- chart panel
- supporting results table
- SQL tab
- assumptions tab
- definitions tab

### Core Actions
- ask a question
- refine a prior question
- inspect SQL
- inspect assumptions
- download chart
- copy SQL
- save analysis

### Suggested V1 Enhancements
- example prompts
- suggested questions
- visibility into supported geography grains and subject areas

---

## 12. Engineering Plan

## Phase 0. Define the Contract
Goal: turn current assets into app ready contracts.

### Work
- define supported metrics for MVP
- define supported geography grains
- define semantic metadata schema
- define SQL template strategy
- define chart rendering contract
- define unsupported query behavior

### Estimated Effort
1 to 2 weeks

## Phase 1. Build the Semantic Layer for the App
Goal: make the Gold layer understandable to the application.

### Work
- metric catalog
- table catalog
- join rules
- geography rules
- example question library formatting
- chart mapping rules

### Estimated Effort
2 to 4 weeks

## Phase 2. Build the Query Pipeline
Goal: turn questions into validated SQL.

### Work
- structured request parser
- prompting and orchestration logic
- SQL templates or query patterns
- SQL validator
- query executor
- error handling
- unsupported question handling

### Estimated Effort
3 to 5 weeks

## Phase 3. Build Visualization Orchestration
Goal: turn result sets into charts consistently.

### Work
- result profiler
- chart selector
- chart config builder
- renderer integration
- chart QA process

### Estimated Effort
2 to 4 weeks

## Phase 4. Build the Frontend
Goal: create a usable web interface.

### Work
- chat UI
- answer rendering
- chart rendering
- table display
- SQL panel
- assumptions panel
- history and loading states

### Estimated Effort
2 to 4 weeks

## Phase 5. Evaluation and Hardening
Goal: make the product reliable.

### Work
- test against example question library
- evaluate SQL correctness
- evaluate chart appropriateness
- handle edge cases
- improve latency
- add logging and QA workflows

### Estimated Effort
2 to 4 weeks

---

## 13. Rough Effort Estimate

### Focused MVP
For a limited scope MVP with an existing Gold layer and partial visual library:

- **One strong builder part time:** 8 to 14 weeks
- **One strong builder full time:** 4 to 8 weeks
- **With help on frontend or platform:** 4 to 6 weeks

### Broader V1 with More Polish
10 to 16 weeks depending on how production ready the tool needs to be.

### Biggest Variable
The main complexity is not the frontend. The main complexity is the semantic layer, SQL validation, and reliability of the question to query workflow.

---

## 14. Major Risks

### Ambiguous Questions
Users may ask open ended questions such as:
- best places for young professionals
- growing but still affordable areas

These require interpretation, composite metrics, or prebuilt scorecards.

**Mitigation:** Start with clear analytical question types and add composites later.

### Geography Grain Mismatches
Users may accidentally mix county, metro, tract, and state concepts in one question.

**Mitigation:** Build geography validation and clear assumption handling.

### Metric Definition Conflicts
Similar concepts may exist across ACS, BEA, and BLS with different definitions.

**Mitigation:** Use a strict metric catalog and surface definitions to the user.

### Overly Open SQL Generation
Too much freedom creates incorrect joins and invented fields.

**Mitigation:** Constrain generation through metadata, templates, and validation.

### Chart Misuse
The model may recommend weak or flashy chart types.

**Mitigation:** Use deterministic chart rules first and restrict the available options.

---

## 15. Recommended MVP Decisions

If this were scoped tightly for a first build, the recommended choices are:

### Stack
- Python backend with FastAPI
- Streamlit for the first frontend unless stronger app polish is required immediately
- warehouse or database connector to the Gold layer
- R chart rendering only if it materially saves time because the visual library already exists there

### Scope
- 5 geography grains maximum
- 4 to 6 subject areas
- 6 to 8 chart types
- read only analytics
- single answer flow with light follow ups
- SQL transparency enabled

### LLM Strategy
- use the model for intent parsing, semantic planning, chart selection, and narrative answer generation
- use deterministic code for validation, execution, and rendering
- use the example question library for few shot prompting and testing

---

## 16. Suggested Backlog

### Foundation
- define supported domains
- define supported grains
- create metric catalog
- create table catalog
- create join rules
- create geography rules

### Query Intelligence
- question classifier
- structured request schema
- SQL pattern library
- SQL validator
- unsupported request handler

### Visualization
- result profiler
- chart recommendation engine
- chart config generator
- visual library integration
- export support

### Product
- frontend shell
- response layout
- SQL tab
- assumptions tab
- saved question history

### QA
- benchmark question set
- regression tests for SQL outputs
- chart QA review set
- logging and latency review

---

## 17. Repo Structure Suggestion

```text
analytics-chatbot/
├── README.md
├── docs/
│   ├── product_spec.md
│   ├── semantic_layer.md
│   ├── frontend_notes.md
│   └── architecture.md
├── metadata/
│   ├── metric_catalog.yml
│   ├── table_catalog.yml
│   ├── join_catalog.yml
│   ├── geography_catalog.yml
│   └── chart_rules.yml
├── examples/
│   ├── training_questions.yml
│   ├── sample_sql/
│   └── sample_outputs/
├── app/
│   ├── frontend/
│   ├── backend/
│   ├── llm/
│   ├── sql/
│   ├── charts/
│   └── utils/
├── tests/
│   ├── test_semantics/
│   ├── test_sql/
│   ├── test_charts/
│   └── test_examples/
└── data/
    └── optional_local_configs/
```

---

## 18. Questions to Answer Before and During Codex Build

These are the key questions that should be answered as the build moves into Codex.

## A. Product and Scope Questions
1. Is the first version meant to be an internal prototype, a portfolio app, or a production ready tool?
2. Who is the primary user for V1?
   - the creator only
   - technical analysts
   - non technical end users
3. Should the app focus on single turn analytical answers first, or do follow up conversations matter in MVP?
4. Should V1 prioritize trust and transparency over breadth of supported questions?
5. Should the output always be one chart plus one table, or should some questions support multiple visuals?

## B. Data and Semantic Layer Questions
6. What database or warehouse is the Gold layer currently stored in?
7. What are the exact MVP geography grains?
8. What are the exact MVP subject areas?
9. Which metrics are stable enough to expose in V1?
10. Do any metrics require special caveats or geography limits?
11. What are the approved join paths between geography and subject area tables?
12. Are there any subject areas that should be read only through prebuilt views instead of raw table logic?

## C. SQL and Orchestration Questions
13. Will SQL generation be fully templated, semi templated, or more open ended within metadata constraints?
14. What level of unsupported question handling is needed?
15. Should the app ask clarifying questions when geography or timeframe is ambiguous, or should it make assumptions and explain them?
16. How much SQL should be exposed in the UI?
17. Should users ever be allowed to edit and rerun SQL in the interface?

## D. Visualization Questions
18. Is the visual library already implemented in code, or is it partly a design spec that still needs implementation?
19. Is chart rendering better done in R, Python, or both?
20. Which 6 to 8 chart types are required for MVP?
21. Should maps be included in MVP or deferred to V1.1?
22. What chart level metadata needs to be stored for automated selection and rendering?

## E. Frontend and UX Questions
23. Should the first frontend be built in Streamlit, Shiny, or a more production oriented framework such as Next.js?
24. Should the UI show SQL and assumptions by default or behind expandable sections?
25. Should the app include suggested prompts or starter analyses?
26. Should users be able to save analyses or export charts in MVP?
27. What level of session history is needed?

## F. Reliability and Evaluation Questions
28. What is the benchmark set of questions that V1 must answer correctly?
29. How will SQL correctness be evaluated?
30. How will chart appropriateness be evaluated?
31. What failure modes should be logged and reviewed?
32. What latency is acceptable for V1?
33. How will regressions be detected as the example question library grows?

## G. Delivery and Engineering Questions
34. What is the preferred thin slice milestone?
35. What is the preferred build order: semantic metadata first, app shell first, or question pipeline first?
36. Should the team start with one domain and one geography grain to validate the architecture before scaling?
37. What parts of the build should be fully reusable as future agent infrastructure?
38. Should the semantic layer be designed as repo managed YAML or as database metadata tables?

---

## 19. Recommended Next Build Artifacts

Once this moves into Codex, the next most useful artifacts are:

1. **Implementation Plan with Epics and Milestones**  
   Break the work into buildable phases and thin slices.

2. **Semantic Layer Contract**  
   Define the metadata model for metrics, tables, joins, geographies, and chart rules.

3. **Prompt and Orchestration Design**  
   Document how the model interprets questions, generates query plans, selects charts, and produces answers.

4. **Frontend Wireframe Spec**  
   Define the chat layout, result panels, and user actions.

5. **Evaluation Framework**  
   Define how to test question understanding, SQL correctness, chart selection, and overall answer quality.

---

## 20. Recommendation

The best delivery strategy is to treat this as a constrained analytical application, not a general chatbot.

The critical path is:
1. semantic metadata
2. validated SQL generation
3. chart selection rules
4. visual rendering integration
5. simple frontend

A narrow, highly reliable MVP will create much more value than a broad but fragile chatbot.
