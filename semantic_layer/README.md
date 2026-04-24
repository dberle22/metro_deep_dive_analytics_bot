# Semantic Layer Utilities

The YAML files in this directory remain the source of truth. The graph tooling builds secondary artifacts from those catalogs for documentation and exploration.

## Generate artifacts

```bash
python3 -m semantic_layer.visualize --format artifacts
```

This writes:

- `semantic_layer/artifacts/semantic_graph.mmd`
- `semantic_layer/artifacts/semantic_graph.json`
- `semantic_layer/artifacts/semantic_graph_summary.json`

## Print a summary

```bash
python3 -m semantic_layer.visualize --format summary
```

## Print Mermaid to stdout

```bash
python3 -m semantic_layer.visualize --format mermaid
```

## Explore in Python

```python
from semantic_layer.graph_builder import load_catalogs, build_semantic_graph

catalogs = load_catalogs()
graph = build_semantic_graph(catalogs)

metric_nodes = [
    node for node, attrs in graph.nodes(data=True)
    if attrs["kind"] == "metric" and attrs.get("growth_eligible")
]
```
