# User Guide

This guide is the practical "how we work in this repo" reference. It focuses on the current chatbot build, especially the semantic layer and the generated knowledge graph artifacts.

## Repo Mental Model

The repo currently has five important working areas:

- [BUILD_PLAN.md]
  The execution checklist and phase tracker. Update this when a scoped piece of work is actually complete.
- [semantic_layer/]
  YAML source of truth for tables, metrics, joins, geography rules, chart rules, and query templates.
- [semantic_layer/artifacts/]
  Generated outputs from the semantic layer, including Mermaid and graph JSON.
- [tests/]
  Lightweight verification for semantic layer and future app behavior.
- [chatbot/] and [data_dictionary/]
  Product docs and the upstream schema references the semantic layer is grounded on.

## General Working Tips

- Treat YAML in `semantic_layer/` as the source of truth.
- Treat files in `semantic_layer/artifacts/` as generated outputs.
- Before starting a new implementation slice, read the relevant phase in [BUILD_PLAN.md].
- When changing semantic logic, update tests and regenerate artifacts in the same pass.
- Prefer small, explicit edits to the catalogs over broad speculative changes.

## Semantic Layer: What It Is

The semantic layer is the controlled contract between:

- the Gold tables
- the future query planner and validator
- chart selection logic
- human reviewers

Current semantic catalogs:

- [table_catalog.yml]
- [metric_catalog.yml]
- [geography_catalog.yml]
- [join_catalog.yml]
- [chart_rules.yml]
- [query_templates.yml]

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

1. Edit one or more YAML files in [semantic_layer/].
2. Regenerate graph artifacts:

```bash
python3 -m semantic_layer.visualize --format artifacts
```

3. Run semantic tests:

```bash
python3 -m unittest tests.test_semantic.test_phase1_catalogs tests.test_semantic.test_semantic_graph
```

4. If the change completes a planned task, update the corresponding checklist in [BUILD_PLAN.md].

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

- [graph_builder.py]
- [visualize.py]

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

- [semantic_graph.mmd]
- [semantic_graph_preview.md]
- [semantic_graph.json]
- [semantic_graph_summary.json]

## How To Visualize The Graph In VS Code

Since you installed a Mermaid plugin, the easiest path is:

1. Open [semantic_graph_preview.md]
2. Open Markdown preview in VS Code.
   Command Palette: `Markdown: Open Preview` or `Markdown: Open Preview to the Side`
3. Your Mermaid extension should render the fenced `mermaid` block automatically.

If your extension supports `.mmd` directly, you can also try:

1. Open [semantic_graph.mmd]
2. Run the extension’s preview command from the Command Palette.

If the `.mmd` file does not preview cleanly, use the Markdown preview file instead. That is the most reliable VS Code workflow.

## How To Visualize The Graph Outside VS Code

Options:

- Paste the Mermaid text into https://mermaid.live
- Use a Mermaid-enabled Markdown renderer
- Convert Mermaid to an image or PDF using external Mermaid CLI tools later if needed

## Common Semantic Layer Tasks

Add a new metric:

1. Update [metric_catalog.yml]
2. Check that the source table exists in [table_catalog.yml]
3. Regenerate artifacts
4. Run semantic tests

Add a new join:

1. Update [join_catalog.yml]
2. Confirm the join is real in the Gold layer or supported semantic contract
3. Regenerate artifacts
4. Review Mermaid output to make sure the relationship looks right

Change geography rules:

1. Update [geography_catalog.yml]
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

## QA Batch Loops

The QA system runs a fixed prompt library through the full pipeline and saves structured artifacts for human review.

### Files

- `qa/qa_prompt_library.yml` — the canonical set of QA cases. Each case has a `qa_case_id`, a question, an expected outcome, and a category.
- `runs/qa_batch/<loop-name>/` — output folder created per batch run, one subfolder per case.
- `runs/qa_batch/<loop-name>/batch_summary.json` — top-level pass/clarification/error counts.
- `runs/qa_batch/<loop-name>/<qa_case_id>/qa_run.json` — full structured artifact for one case.

### Running a loop

Full batch with chart rendering (recommended):

```bash
.venv/bin/python -m app.scripts.qa_batch --collection loop3 --render-chart
```

Without chart rendering (faster, use when iterating on parsing only):

```bash
.venv/bin/python -m app.scripts.qa_batch --collection loop3
```

Run only specific cases:

```bash
.venv/bin/python -m app.scripts.qa_batch --collection loop3 --cases qa_b_001 qa_b_002 qa_b_003
```

Run only one category:

```bash
.venv/bin/python -m app.scripts.qa_batch --collection loop3 --category golden
```

The `--collection` label becomes the output folder name under `runs/qa_batch/`. Use a consistent naming convention (`loop1`, `loop2`, etc.) so runs are easy to compare.

### Reviewing results

Open the QA review app:

```bash
.venv/bin/python -m streamlit run frontend/qa_review.py
```

Or read `batch_summary.json` directly for a quick pass/fail count:

```bash
cat runs/qa_batch/loop3/batch_summary.json
```

### Starting a new loop

A new QA loop is appropriate after any meaningful change to the pipeline (parser, generator, R rendering, assembler). The workflow is:

1. Make fixes.
2. Run the batch with a new `--collection` label (e.g. `loop3`).
3. Check `batch_summary.json` for the parsed / clarification / error split.
4. Open the review app and spot-check failures and regressions.
5. Write a fix brief (`qa/loop<N>_fix_brief.md`) for any issues found.
6. Repeat.

### Case categories

| Category | Meaning |
|---|---|
| `golden` | Exact or near-exact cases that should always parse correctly. Regressions here are blockers. |
| `provider_paraphrase` | Reworded questions that must go through the LLM. Tests generalization beyond heuristic matching. |
| `clarification` | Underspecified prompts where the system should ask a good clarifying question rather than guess. |

---

## Backend Testing

Before the Streamlit frontend exists, the main way to test the chatbot is through the CLI wrapper at [app/scripts/ask.py].

### Prerequisites

- Activate the repo venv:

```bash
source .venv/bin/activate
```

- Confirm `.env` uses the Ollama OpenAI-compatible endpoint:

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
```

- Start Ollama in a separate terminal:

```bash
ollama serve
```

- Verify the server:

```bash
curl http://localhost:11434/api/tags
curl http://localhost:11434/v1/models
```

### CLI Commands

Parser-only:

```bash
.venv/bin/python -m app.scripts.ask "Which states had the highest total population in 2024?" --parser-only
```

Parser-only with JSON:

```bash
.venv/bin/python -m app.scripts.ask "Which states had the highest total population in 2024?" --parser-only --json
```

Full backend run without chart rendering:

```bash
.venv/bin/python -m app.scripts.ask "Which states had the highest total population in 2024?" --json
```

Full backend run with chart rendering:

```bash
.venv/bin/python -m app.scripts.ask "Which states had the highest total population in 2024?" --render-chart --json
```

Full backend run with chart rendering and automatic test-log append:

```bash
.venv/bin/python -m app.scripts.ask "Which states had the highest total population in 2024?" --render-chart --show-timings --log-model-test
```

Force the request through Ollama:

```bash
.venv/bin/python -m app.scripts.ask "Rank the top 10 states by population for 2024" --parser-only --force-provider --json
```

Show step timings in human-readable mode:

```bash
.venv/bin/python -m app.scripts.ask "Rank the top 10 states by population for 2024" --render-chart --show-timings
```

### How To Read The Output

- `matched_example_id`
  Non-null means the question exactly matched a seeded example and did not need Ollama.
- `provider_used`
  Non-null means the configured provider handled parsing.
- `chart_type`
  The selected approved chart family after profiling the query result.
- `chart_path`
  Present only when `--render-chart` is used and rendering succeeds.
- `timings_ms`
  Per-stage backend timings. Use this to separate model latency from SQL or R rendering latency.
- `--log-model-test`
  Appends a ready-to-review run entry into [model_test.md].

### Recommended Testing Order

1. Run an exact-example question to confirm the deterministic path works.
2. Run a reworded version with `--force-provider` to test Ollama specifically.
3. Run the same question through full orchestration without chart rendering.
4. Run it again with `--render-chart` and open the PNG at `chart_path`.
5. Record results in [model_test.md].

### Useful Questions

- `Which states had the highest total population in 2024?`
- `Rank the top 10 states by population for 2024`
- `Which states had the highest population growth over 5 years?`
- `What are the fastest-growing states over the last five years?`
- `Show housing unit growth over time in California, Texas, and Florida.`
- `Show the distribution of state home values in 2024.`
- `Compare Florida population with the US in 2024.`
- `Which places are growing fastest?`
