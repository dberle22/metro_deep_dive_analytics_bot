# Product Spec
## US Demographic and Economic Analytics Chatbot

## 1. Purpose

Build a polished portfolio application that allows a user to ask analytical questions about US demographic and economic data in natural language and receive a trusted answer, a standardized visual, a supporting table, and the SQL used to produce the result.

The product should prioritize clarity, reliability, and transparency. It should be designed so the MVP can expand later without major rework or unnecessary technical debt.

## 2. Users

### Primary Users
- Product owner / analyst power user
- Business users who want analytical answers without writing SQL

### User Characteristics
- Interested in demographic and economic analysis
- Comfortable interpreting charts and rankings
- May not know the underlying data model
- Need outputs that are understandable, inspectable, and presentation ready

## 3. MVP Scope

### Included Question Types
- Rankings
- Trends over time
- Comparisons across selected geographies
- Distributions
- Benchmarks against broader geographies or user defined peer groups

### Supported Geography Levels
- Region
- Census Division
- State
- CBSA
- County
- ZCTA

### Supported Subject Areas
- Population
- Income
- Housing / Rent
- Business Activity

### Business Activity Metrics in Scope
- Employment
- Payroll
- Industry mix

### Benchmark Types
- United States
- Region
- Division
- State
- User defined peer group

### Time Support
- Point in time comparisons
- Trends over time
- Standard 5 year growth by default
- Standard 3 year growth when explicitly requested
- Standard 1 year growth when explicitly requested

The system should support reusable SQL patterns using standard CTEs and window logic for growth calculations where applicable.

### Required Output Components
Every response should include:
- Short written answer
- Chart
- Result table
- SQL used
- Assumptions and definitions

### Conversational Scope
- Support basic follow up questions
- Examples:
  - Show this at the county level
  - Filter to the South
  - Compare against the US
  - Use a 3 year growth view instead

### Explicitly Out of Scope for V1
- Fully open ended conversation
- Arbitrary custom SQL editing
- Forecasting
- User uploaded datasets
- Dashboards with many visuals at once
- Automated insight generation beyond a short summary
- Maps

## 4. Core Workflow

1. User asks a question in natural language
2. System interprets the analytical intent, metric, geography, comparison type, and time frame
3. System determines whether the request is sufficiently specific
4. If the request is unclear, the system asks a clarifying question
5. System builds a structured query plan
6. System generates SQL against approved Gold layer tables
7. System validates SQL for correctness and safety
8. System executes the query
9. System selects a chart type from the approved visual library
10. System renders the chart and result table
11. System returns a concise written answer with SQL and assumptions

## 5. Functional Requirements

### Question Understanding
The system must identify:
- Question type
- Subject area
- Geography grain
- Geography filters
- Time frame
- Comparison logic
- Ranking or benchmark intent
- Growth logic where requested or implied

### Clarification Handling
If the question is too vague, ambiguous, or unsupported, the system should ask a clarifying question rather than guessing.

This is especially important for:
- unclear geography grain
- unclear benchmark target
- ambiguous metric naming
- peer group requests without a defined peer set
- unsupported combinations of subject, grain, and time logic

### Query Planning
The system must convert each supported question into a structured query plan before SQL generation.

The plan should specify:
- subject area
- metric or metrics
- geography grain
- filters
- benchmark target if applicable
- time logic
- output shape

### SQL Generation
The system must generate SQL only against approved Gold layer assets and supported query patterns.

The system should rely on reusable SQL patterns for:
- rankings
- benchmark comparisons
- time series trends
- 5 year growth
- 3 year growth
- 1 year growth

### SQL Validation
The system must validate SQL before execution to reduce incorrect joins, unsupported fields, and unsafe queries.

### Result Rendering
The system must return:
- A concise written answer
- One chart selected from the approved visual library
- A supporting result table
- SQL used
- Assumptions and metric definitions

### Follow Up Support
The system should support lightweight follow ups that modify:
- Geography level
- Geography filter
- Comparison group
- Time frame
- Ranking direction
- Growth window

## 6. System Boundaries

### Inputs
- Natural language user questions
- Approved Gold layer tables
- Approved semantic metadata
- Approved visual library functions
- Example question and SQL library

### Outputs
- Short analytical answer
- Single chart
- Supporting table
- SQL
- Assumptions and definitions

### Constraints
- Read only analytical querying
- No user supplied data
- No unconstrained SQL editing
- No multi chart dashboard generation
- No map rendering in MVP
- Peer groups must be explicitly defined by the user through a manual list in session

## 7. Success Criteria

The MVP is successful if it can reliably answer a focused set of analytical questions across the approved subjects and geographies with outputs that are understandable and trustworthy.

### Product Success Indicators
- Users can get answers without knowing the schema
- Outputs are visually consistent and presentation ready
- SQL is inspectable and aligned to the intended question
- Clarification behavior works well when questions are underspecified
- Benchmark outputs are easy to interpret
- Growth calculations are consistent and reusable
- The app feels polished enough to serve as a public portfolio project

## 8. Open Decisions

These decisions should be resolved during implementation design:

- Which frontend framework will power the MVP
- Which backend framework will orchestrate query generation and execution
- Whether chart rendering remains in R or moves to Python
- Which exact metrics are included first under each subject area
- How benchmark logic is implemented for each geography level
- How user defined peer groups are entered and stored in session
- How basic follow up state is stored and managed
- What validation rules must pass before SQL execution
- How unsupported questions are surfaced in the UI