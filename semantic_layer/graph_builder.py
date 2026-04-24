"""Build graph representations of the semantic layer catalogs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by runtime guard
    yaml = None

try:
    import networkx as nx
    from networkx.readwrite import json_graph
except ImportError:  # pragma: no cover - exercised by runtime guard
    nx = None
    json_graph = None


CATALOG_FILES = {
    "table_catalog": "table_catalog.yml",
    "metric_catalog": "metric_catalog.yml",
    "geography_catalog": "geography_catalog.yml",
    "join_catalog": "join_catalog.yml",
    "chart_rules": "chart_rules.yml",
    "query_templates": "query_templates.yml",
}


def _require_dependencies() -> None:
    missing = []
    if yaml is None:
        missing.append("PyYAML")
    if nx is None:
        missing.append("networkx")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Missing required dependencies: {joined}. "
            "Install them with `python3 -m pip install --user PyYAML networkx`."
        )


def semantic_layer_dir(base_dir: str | Path | None = None) -> Path:
    if base_dir is None:
        return Path(__file__).resolve().parent
    return Path(base_dir)


def load_catalogs(base_dir: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load all semantic YAML catalogs from disk."""
    _require_dependencies()
    root = semantic_layer_dir(base_dir)
    catalogs: dict[str, dict[str, Any]] = {}
    for catalog_name, filename in CATALOG_FILES.items():
        path = root / filename
        with path.open("r", encoding="utf-8") as handle:
            catalogs[catalog_name] = yaml.safe_load(handle)
    return catalogs


def _node_id(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _add_node(graph: Any, kind: str, value: str, label: str | None = None, **attrs: Any) -> str:
    node_id = _node_id(kind, value)
    graph.add_node(node_id, kind=kind, value=value, label=label or value, **attrs)
    return node_id


def build_semantic_graph(catalogs: dict[str, dict[str, Any]]) -> Any:
    """Build a directed multigraph from semantic catalogs."""
    _require_dependencies()
    graph = nx.MultiDiGraph(name="semantic_layer")

    for table in catalogs["table_catalog"]["tables"]:
        table_id = table["table_id"]
        table_node = _add_node(
            graph,
            "table",
            table_id,
            label=table_id,
            subject_area=table.get("subject_area"),
            status=table.get("status"),
        )
        for geo_level in table.get("supported_geo_levels", []):
            geo_node = _add_node(graph, "geo_level", geo_level, label=geo_level)
            graph.add_edge(table_node, geo_node, relation="supports_geo_level")

    for metric in catalogs["metric_catalog"]["metrics"]:
        metric_id = metric["metric_id"]
        metric_node = _add_node(
            graph,
            "metric",
            metric_id,
            label=metric_id,
            subject_area=metric.get("subject_area"),
            status=metric.get("status"),
            growth_eligible=metric.get("growth_eligible"),
        )
        table_node = _add_node(
            graph,
            "table",
            metric["source_table"],
            label=metric["source_table"],
        )
        graph.add_edge(metric_node, table_node, relation="from_table", column=metric.get("source_column"))
        for geo_level in metric.get("valid_geo_levels", []):
            geo_node = _add_node(graph, "geo_level", geo_level, label=geo_level)
            graph.add_edge(metric_node, geo_node, relation="valid_for_geo_level")

    for geo in catalogs["geography_catalog"]["geo_levels"]:
        _add_node(
            graph,
            "geo_level",
            geo["geo_level"],
            label=geo.get("display_name", geo["geo_level"]),
            supported_in_mvp=geo.get("supported_in_mvp"),
            hierarchy_rank=geo.get("hierarchy_rank"),
        )

    for edge in catalogs["geography_catalog"]["hierarchy_edges"]:
        child = _add_node(graph, "geo_level", edge["child_geo_level"], label=edge["child_geo_level"])
        parent = _add_node(graph, "geo_level", edge["parent_geo_level"], label=edge["parent_geo_level"])
        graph.add_edge(
            child,
            parent,
            relation="rolls_up_to",
            relationship_type=edge.get("relationship_type"),
            valid_for_rollup=edge.get("valid_for_rollup"),
            source_table=edge.get("source_table"),
        )

    for join_rule in catalogs["join_catalog"]["join_rules"]:
        left = _add_node(graph, "table", join_rule["left_table"], label=join_rule["left_table"])
        right = _add_node(graph, "table", join_rule["right_table"], label=join_rule["right_table"])
        graph.add_edge(
            left,
            right,
            relation="joins_to",
            join_id=join_rule["join_id"],
            compatibility=join_rule.get("compatibility"),
            join_type=join_rule.get("join_type"),
        )

    for template in catalogs["query_templates"]["templates"]:
        template_id = template["template_id"]
        template_node = _add_node(graph, "template", template_id, label=template_id)
        for question_type in template.get("question_types", []):
            question_node = _add_node(graph, "question_type", question_type, label=question_type)
            graph.add_edge(question_node, template_node, relation="uses_template")

    for rule in catalogs["chart_rules"]["rules"]:
        question_type = rule["question_type"]
        question_node = _add_node(graph, "question_type", question_type, label=question_type)
        for chart_type in rule.get("approved_chart_types", []):
            chart_node = _add_node(graph, "chart_type", chart_type, label=chart_type)
            graph.add_edge(question_node, chart_node, relation="approved_chart")
        for chart_type in rule.get("fallback_chart_types", []):
            chart_node = _add_node(graph, "chart_type", chart_type, label=chart_type)
            graph.add_edge(question_node, chart_node, relation="fallback_chart")

    return graph


def graph_summary(graph: Any) -> dict[str, Any]:
    _require_dependencies()
    counts: dict[str, int] = {}
    for _, attrs in graph.nodes(data=True):
        kind = attrs["kind"]
        counts[kind] = counts.get(kind, 0) + 1

    edge_counts: dict[str, int] = {}
    for _, _, attrs in graph.edges(data=True):
        relation = attrs["relation"]
        edge_counts[relation] = edge_counts.get(relation, 0) + 1

    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "node_kinds": counts,
        "edge_relations": edge_counts,
    }


def graph_to_node_link_json(graph: Any) -> str:
    _require_dependencies()
    return json.dumps(json_graph.node_link_data(graph), indent=2)


def mermaid_from_graph(graph: Any) -> str:
    _require_dependencies()

    kind_order = ["table", "metric", "geo_level", "template", "question_type", "chart_type"]
    kind_labels = {
        "table": "Tables",
        "metric": "Metrics",
        "geo_level": "Geographies",
        "template": "Templates",
        "question_type": "Question Types",
        "chart_type": "Chart Types",
    }
    relation_labels = {
        "from_table": "from table",
        "supports_geo_level": "supports",
        "valid_for_geo_level": "valid for",
        "rolls_up_to": "rolls up to",
        "joins_to": "joins to",
        "uses_template": "uses",
        "approved_chart": "approved",
        "fallback_chart": "fallback",
    }

    lines = ["flowchart LR"]
    by_kind: dict[str, list[tuple[str, dict[str, Any]]]] = {kind: [] for kind in kind_order}
    for node_id, attrs in sorted(graph.nodes(data=True), key=lambda item: (item[1]["kind"], item[1]["value"])):
        by_kind.setdefault(attrs["kind"], []).append((node_id, attrs))

    for kind in kind_order:
        nodes = by_kind.get(kind, [])
        if not nodes:
            continue
        lines.append(f"  subgraph {kind_labels[kind]}")
        for node_id, attrs in nodes:
            safe_id = _mermaid_id(node_id)
            label = attrs.get("label", attrs["value"]).replace('"', "'")
            lines.append(f'    {safe_id}["{label}"]')
        lines.append("  end")

    for source, target, attrs in sorted(
        graph.edges(data=True),
        key=lambda item: (
            graph.nodes[item[0]]["kind"],
            graph.nodes[item[0]]["value"],
            attrs_sort_key(item[2]),
            graph.nodes[item[1]]["kind"],
            graph.nodes[item[1]]["value"],
        ),
    ):
        label = relation_labels.get(attrs["relation"], attrs["relation"]).replace('"', "'")
        lines.append(f"  {_mermaid_id(source)} -->|{label}| {_mermaid_id(target)}")

    return "\n".join(lines) + "\n"


def attrs_sort_key(attrs: dict[str, Any]) -> str:
    return str(attrs.get("relation", ""))


def _mermaid_id(node_id: str) -> str:
    return node_id.replace(":", "_").replace("-", "_")


def write_default_artifacts(base_dir: str | Path | None = None) -> dict[str, Path]:
    root = semantic_layer_dir(base_dir)
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    catalogs = load_catalogs(root)
    graph = build_semantic_graph(catalogs)
    summary = graph_summary(graph)

    mermaid_path = artifacts_dir / "semantic_graph.mmd"
    mermaid_path.write_text(mermaid_from_graph(graph), encoding="utf-8")

    json_path = artifacts_dir / "semantic_graph.json"
    json_path.write_text(graph_to_node_link_json(graph), encoding="utf-8")

    summary_path = artifacts_dir / "semantic_graph_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "mermaid": mermaid_path,
        "json": json_path,
        "summary": summary_path,
    }
