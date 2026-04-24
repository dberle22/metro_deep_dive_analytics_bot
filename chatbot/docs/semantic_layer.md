# Semantic Layer
## US Demographic and Economic Analytics Chatbot

## 1. Purpose

The semantic layer provides the controlled analytical contract between the application and the Gold layer.

It serves three roles:

- exposes the Gold layer in a safe and queryable way for the app and LLM
- defines metrics, dimensions, joins, and business rules consistently
- acts as a lightweight business context layer for supported analytical questions

The semantic layer exists to improve trust, reduce ambiguity, and prevent the application from generating unsupported or incorrect SQL.

## 2. Semantic Assets

The MVP semantic layer should include the following assets.

### Required Asset Set
- metric catalog
- table catalog
- dimension catalog
- join catalog
- geography hierarchy catalog
- benchmark rules
- query templates
- semantic scaffolds for future peer group support

### Scaffold Notes
This repo should include scaffolds for each of these assets even if some are incomplete at the start. The goal is to establish the semantic contract early and fill in missing definitions incrementally during implementation.

## 3. Core Entities and Grains

### Initial Gold Tables
The first semantic layer should support these Gold assets:

- `population_demographics`
- `housing_core_wide`
- `economic_income_wide`
- `economic_gdp_wide`
- geography dimension assets from the `geo` schema
- future `peer_group` mapping assets

### Primary Grain Pattern
The default grain contract for MVP is:

- one row per geography per year for most subject area tables

This should be the expected shape for:
- population
- income
- housing / rent

Business activity may require extensions where an additional industry dimension is present.

### Future Grain Extensions
The semantic layer should remain flexible enough to support:
- geography by year by industry
- derived benchmark rows at query time
- additional subject specific grain patterns later

## 4. Metric and Dimension Rules

### Metric Catalog Standard
Each metric should support these fields where available:

- `metric_id`
- `display_name`
- `description`
- `formula_logic`
- `source_table`
- `valid_geographies`
- `valid_time_grains`
- `unit_format`
- `subject_area`
- `caveats`

Not every metric must have every field fully populated at the start, but this is the target structure for the catalog.

### Metric Family Design
Growth measures should be modeled as metric families with explicit parameters rather than fully separate standalone metrics.

Example:
- base metric: `population`
- derived metric family: `population_growth`
- supported parameter: `window_years`
- default: `5`
- allowed overrides: `3`, `1`

This same pattern should apply to other growth eligible metrics where appropriate.

### Initial Dimension Set
The first semantic layer should support these dimensions:

- geography dimensions
- time dimensions
- industry dimension
- benchmark type
- peer group identifier

Additional dimensions can be added later as subject area coverage expands.

## 5. Geography and Benchmark Rules

### Canonical Geography Dimensions
The semantic layer should define canonical geography dimensions for:

- Region
- Division
- State
- CBSA
- County
- ZCTA

These should be available as first class data assets in the catalog, not only hidden implementation details.

### Geography Hierarchy Design
The semantic layer should expose hierarchy relationships and crosswalks as cataloged assets so the app can reason safely about supported grains and rollups.

This includes:
- geography identifiers
- geography names
- parent child relationships where applicable
- supported rollup paths
- known limitations where direct rollup is not valid

### Benchmark Logic
Benchmarks should be defined as query patterns, not stored metrics.

Supported benchmark types:
- United States
- Region
- Division
- State
- peer group

Benchmark comparisons should be derived at query time using standard semantic rules.

### Peer Group Design
Peer groups should be represented through a mapping structure:

- `peer_group_id`
- `geography_id`

This should be designed as a semantic data asset rather than only session state so peer groups can scale and remain reusable.

## 6. Query Planning Contract

The semantic layer should define the contract the app uses before SQL generation.

Each structured query plan should identify:

- question type
- subject area
- metric or metric family
- metric parameters if applicable
- geography grain
- geography filters
- benchmark type if applicable
- time logic
- output shape
- template type

### Template Organization
Query templates should be organized by analytical pattern rather than by table.

Initial template groups:
- ranking
- time trend
- compare selected geographies
- distribution
- benchmark comparison
- growth calculation

This keeps the system extensible across tables and subject areas.

## 7. Join and Validation Rules

### Join Rules
The semantic layer should maintain an explicit join catalog that defines:

- approved join paths
- join keys
- grain compatibility
- allowed subject area combinations

The system should not infer joins outside this catalog.

### Validation Rules
The semantic layer should reject:

- unsupported geography and metric combinations
- unsupported benchmark combinations
- unsupported time windows
- ambiguous metric names that do not map to approved metrics

This validation happens before SQL execution and is a core safety mechanism for the app.

## 8. Example Library Boundary

The example question library is related to the semantic layer but should remain a separate asset.

This keeps the semantic documentation focused on the analytical contract rather than training examples.

The example library can later reference:
- template type
- metric mapping
- geography grain
- benchmark type
- sample SQL
- expected chart type

## 9. Open Decisions

The following semantic design questions still need to be resolved during implementation:

- which exact metrics are included first under each subject area
- which metrics are growth eligible
- which business activity fields are available by geography and year in the current Gold layer
- how industry mix is represented semantically
- how peer groups are defined, loaded, and maintained
- which geography crosswalks are required for all supported benchmark paths
- how much metadata must be complete before a metric becomes app eligible
- whether GDP remains scaffold only or becomes active in V1 expansion