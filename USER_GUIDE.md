# User Guide

This guide is the practical "how we work in this repo" reference. It focuses on the current chatbot build, especially the semantic layer and the generated knowledge graph artifacts.

## Repo Mental Model

The repo currently has five important working areas:

- [BUILD_PLAN.md](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/BUILD_PLAN.md:1)
  The execution checklist and phase tracker. Update this when a scoped piece of work is actually complete.
- [semantic_layer/](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer)
  YAML source of truth for tables, metrics, joins, geography rules, chart rules, and query templates.
- [semantic_layer/artifacts/](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts)
  Generated outputs from the semantic layer, including Mermaid and graph JSON.
- [tests/](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/tests)
  Lightweight verification for semantic layer and future app behavior.
- [chatbot/](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/chatbot) and [data_dictionary/](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/data_dictionary)
  Product docs and the upstream schema references the semantic layer is grounded on.

## General Working Tips

- Treat YAML in `semantic_layer/` as the source of truth.
- Treat files in `semantic_layer/artifacts/` as generated outputs.
- Before starting a new implementation slice, read the relevant phase in [BUILD_PLAN.md](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/BUILD_PLAN.md:1).
- When changing semantic logic, update tests and regenerate artifacts in the same pass.
- Prefer small, explicit edits to the catalogs over broad speculative changes.

## Semantic Layer: What It Is

The semantic layer is the controlled contract between:

- the Gold tables
- the future query planner and validator
- chart selection logic
- human reviewers

Current semantic catalogs:

- [table_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/table_catalog.yml:1)
- [metric_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/metric_catalog.yml:1)
- [geography_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/geography_catalog.yml:1)
- [join_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/join_catalog.yml:1)
- [chart_rules.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/chart_rules.yml:1)
- [query_templates.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/query_templates.yml:1)

## Semantic Layer: How To Use It

Use the semantic layer when you need to answer questions like:

- Which metrics are officially supported?
- Which geographies are valid for a metric?
- Which tables can be joined?
- Which chart types are approved for a question type?
- Which SQL templates exist for a given analysis shape?

For human review:

- open the YAML directly
- inspect the generated Mermaid graph
- inspect the graph summary JSON

For programmatic use:

- load the catalogs with `semantic_layer.graph_builder`
- build the `networkx` graph
- query nodes and edges in Python

## Semantic Layer: How To Update It

Recommended workflow:

1. Edit one or more YAML files in [semantic_layer/](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer).
2. Regenerate graph artifacts:

```bash
python3 -m semantic_layer.visualize --format artifacts
```

3. Run semantic tests:

```bash
python3 -m unittest tests.test_semantic.test_phase1_catalogs tests.test_semantic.test_semantic_graph
```

4. If the change completes a planned task, update the corresponding checklist in [BUILD_PLAN.md](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/BUILD_PLAN.md:1).

When updating, keep these rules in mind:

- If you add a metric, make sure its table and valid geo levels are correct.
- If you add a table, make sure join rules and supported geo levels are reviewed too.
- If you change geography hierarchy logic, review both `geography_catalog.yml` and any affected join assumptions.
- If you change chart or template logic, regenerate the graph because question-type relationships will change.

## Knowledge Graph: What It Represents

The knowledge graph is generated from the YAML catalogs. It currently models:

- `table` nodes
- `metric` nodes
- `geo_level` nodes
- `template` nodes
- `question_type` nodes
- `chart_type` nodes

And edges like:

- `metric -> table`
- `table -> geo_level`
- `table -> table` join approvals
- `geo_level -> geo_level` rollups
- `question_type -> template`
- `question_type -> chart_type`

The graph builder lives here:

- [graph_builder.py](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/graph_builder.py:1)
- [visualize.py](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/visualize.py:1)

## Knowledge Graph: How To Explore It In Python

Example:

```python
from semantic_layer.graph_builder import load_catalogs, build_semantic_graph

catalogs = load_catalogs()
graph = build_semantic_graph(catalogs)

print(graph.number_of_nodes(), graph.number_of_edges())

growth_metrics = [
    (node, attrs)
    for node, attrs in graph.nodes(data=True)
    if attrs["kind"] == "metric" and attrs.get("growth_eligible")
]

housing_edges = list(graph.out_edges("table:housing_core_wide", data=True))
```

Useful exploration patterns:

- list all metrics for one table
- list all geographies supported by one metric
- list approved joins from one table
- list chart options for a question type
- inspect rollup paths between geography levels

## How To Generate Graph Outputs

Print a summary:

```bash
python3 -m semantic_layer.visualize --format summary
```

Print Mermaid text to the terminal:

```bash
python3 -m semantic_layer.visualize --format mermaid
```

Regenerate all saved artifacts:

```bash
python3 -m semantic_layer.visualize --format artifacts
```

Generated files:

- [semantic_graph.mmd](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts/semantic_graph.mmd:1)
- [semantic_graph_preview.md](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts/semantic_graph_preview.md:1)
- [semantic_graph.json](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts/semantic_graph.json:1)
- [semantic_graph_summary.json](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts/semantic_graph_summary.json:1)

## How To Visualize The Graph In VS Code

Since you installed a Mermaid plugin, the easiest path is:

1. Open [semantic_graph_preview.md](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts/semantic_graph_preview.md:1)
2. Open Markdown preview in VS Code.
   Command Palette: `Markdown: Open Preview` or `Markdown: Open Preview to the Side`
3. Your Mermaid extension should render the fenced `mermaid` block automatically.

If your extension supports `.mmd` directly, you can also try:

1. Open [semantic_graph.mmd](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/artifacts/semantic_graph.mmd:1)
2. Run the extension’s preview command from the Command Palette.

If the `.mmd` file does not preview cleanly, use the Markdown preview file instead. That is the most reliable VS Code workflow.

## How To Visualize The Graph Outside VS Code

Options:

- Paste the Mermaid text into https://mermaid.live
- Use a Mermaid-enabled Markdown renderer
- Convert Mermaid to an image or PDF using external Mermaid CLI tools later if needed

## Common Semantic Layer Tasks

Add a new metric:

1. Update [metric_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/metric_catalog.yml:1)
2. Check that the source table exists in [table_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/table_catalog.yml:1)
3. Regenerate artifacts
4. Run semantic tests

Add a new join:

1. Update [join_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/join_catalog.yml:1)
2. Confirm the join is real in the Gold layer or supported semantic contract
3. Regenerate artifacts
4. Review Mermaid output to make sure the relationship looks right

Change geography rules:

1. Update [geography_catalog.yml](/Users/danberle/Documents/projects/metro_deep_dive_chatbot/semantic_layer/geography_catalog.yml:1)
2. Re-read rollup caveats carefully
3. Regenerate artifacts
4. Review summary and Mermaid output

## Current Limitations

- The graph is generated from YAML, not a live database.
- The Mermaid view is intentionally broad and can get crowded as the semantic layer grows.
- The graph JSON is best suited for programmatic use, not direct manual reading.
- The current graph does not yet model every future concept such as peer groups, benchmarks as first-class nodes, or richer column-level lineage.

## Recommended Habits

- Keep the source-of-truth rule strict: edit YAML, not generated artifacts.
- Regenerate artifacts after semantic changes.
- Run tests before marking a task complete.
- Use the Markdown Mermaid preview file for visual review.
- Use the `networkx` graph when you want to ask relationship questions in code.
