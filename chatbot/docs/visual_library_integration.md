# Visual Library Integration
## US Demographic and Economic Analytics Chatbot

## 1. Purpose

This document defines how the application selects, renders, and displays charts using the existing visual library.

The goal is to ensure that analytical results are translated into consistent, readable visuals through a controlled integration between Python orchestration and the R based charting system.

## 2. Role of the Visual Library

The visual library is the approved rendering system for the application.

It is responsible for:
- applying chart standards
- rendering supported chart types
- formatting titles, subtitles, labels, and annotations
- returning a visual artifact ready for display and export

The visual layer should not make major analytical decisions on its own. It should receive shaped data and a chart configuration from the application layer.

A small amount of semantic context is acceptable, such as:
- metric format
- benchmark type
- growth window

## 3. Supported Chart Types

The MVP should support this initial chart set:

- bar charts
- line charts
- scatter plots
- histograms
- heatmap tables
- boxplots

Each chart type should have a strict input contract.

## 4. Chart Eligibility and Selection Rules

### Selection Approach
Chart selection should follow this order:

1. deterministic rules based on question type and result shape
2. limited LLM assistance only when more than one chart type is plausibly valid

The system should not rely on open ended model judgment for chart choice.

### Eligibility Rules
Each supported chart type should define:
- required data shape
- required field mappings
- optional fields
- supported annotations
- expected sorting behavior
- benchmark support rules

### User Control
Users should not manually switch chart types in MVP.

The system selects the chart.

## 5. Rendering Contract

The application should pass a structured chart configuration to the visual library.

### Target Chart Config Fields
- `chart_type`
- `x_field`
- `y_field`
- `group_field`
- `label_field`
- `title`
- `subtitle`
- `footnote`
- `sort_order`
- `highlight_rules`
- `benchmark_markers`
- `formatting_hints`

Not every field must be required for every chart type, but this is the target contract.

### Required vs Optional Fields
Each chart type should define:
- minimum required config fields
- optional enrichments
- sensible fallbacks when optional fields are missing

## 6. Python to R Handoff

The integration should conceptually work as:

- Python prepares the shaped result dataset
- Python builds the chart config object
- Python passes the dataset and config to R
- R renders the chart using the visual library
- R returns a rendered artifact for frontend display and export

The exact transport mechanism can remain open during early implementation, but the contract should be based on:
- dataframe or shaped dataset
- structured chart config

## 7. Titles, Subtitles, and Annotation Logic

The system should automatically generate:
- title
- subtitle
- key annotation hints

This keeps chart text consistent and scalable.

### Benchmark Display
Benchmark display depends on chart type.

Preferred approach:
- use reference lines where appropriate
- otherwise use chart specific comparison methods such as separate points, bars, or labels
- benchmark context should also appear in chart subtitle when relevant

### Growth Metric Display
Growth metrics should follow consistent visual rules:
- display as percentages when applicable
- call out the growth window in titles and subtitles
- use standardized wording for 5 year, 3 year, and 1 year growth

## 8. Output Handling and UI Integration

The rendered chart should be:
- displayed in the main result area
- consistent with app visual tone
- exportable in MVP

Chart export should be available as a frontend action once a valid chart artifact is returned.

## 9. Failure and Fallback Rules

### Unsupported Result Shape
If a result does not cleanly fit a supported chart:
- show the result table
- show a concise note explaining that no chart was rendered for this result shape

### Rendering Failure
If R chart rendering fails:
- show the written answer
- show the result table
- do not fail the whole response
- log the rendering error

A Python fallback chart layer can be added later if needed, but it is not required for MVP.

## 10. Visual Standards Scope

The MVP should enforce core visual standards first.

This includes:
- chart type consistency
- readable labels
- metric formatting
- title and subtitle conventions
- basic benchmark and growth notation

Richer annotation behavior and edge case polish can be added after MVP.

## 11. Chart QA Standard

The minimum chart QA standard for MVP is:

- correct chart chosen for the result shape
- labels are readable
- formatting is correct for the metric type
- benchmark wording is consistent
- growth wording is consistent
- chart renders successfully without breaking the response

## 12. Open Decisions

The following implementation details still need to be finalized:

- exact transport method between Python and R
- exact config schema per chart type
- how annotation hints are encoded in config
- how benchmark markers are represented across chart types
- what chart file formats are supported for export
- whether a Python fallback renderer is needed after MVP