"""Intent parsing from natural language into structured query plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
from typing import Any

import yaml

from app.llm.provider import LLMProvider
from app.query.catalogs import REPO_ROOT, load_semantic_catalogs


QUESTION_LIBRARY_PATH = REPO_ROOT / "examples" / "question_library.yml"
DEFAULT_FEW_SHOT_COUNT = 8

QUESTION_TYPE_ALIASES = {
    "compare": "comparison",
    "comparison": "comparison",
    "rank": "ranking",
    "ranking": "ranking",
    "trend": "trend",
    "distribution": "distribution",
    "benchmark": "benchmark",
    "growth": "growth",
}


class ValidationError(ValueError):
    """Compatibility error type used when local schema validation fails."""


@dataclass
class QueryPlan:
    """Normalized intent schema used between parsing and SQL planning."""

    question_type: str
    subject_area: str | None = None
    metric_id: str | None = None
    base_metric_id: str | None = None
    source_table: str | None = None
    geo_level: str | None = None
    target_geo_level: str | None = None
    target_geo_id: str | None = None
    geo_ids: list[str] | None = None
    geo_filters: dict[str, Any] | None = None
    benchmark_type: str | None = None
    benchmark_geo_level: str | None = None
    benchmark_geo_ids: list[str] | None = None
    comparison_label: str | None = None
    year: int | None = None
    start_year: int | None = None
    end_year: int | None = None
    window_years: int | None = None
    sort_direction: str | None = None
    limit: int | None = None
    template_id: str | None = None

    def __post_init__(self) -> None:
        question_type = QUESTION_TYPE_ALIASES.get(self.question_type.lower())
        if question_type is None:
            raise ValidationError(f"Unsupported question_type: {self.question_type}")
        self.question_type = question_type

        if self.sort_direction is not None:
            self.sort_direction = self.sort_direction.lower()

        if self.template_id is None:
            if self.base_metric_id:
                self.template_id = "growth"
            elif self.question_type == "comparison":
                self.template_id = "compare_selected"
            else:
                self.template_id = self.question_type

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "QueryPlan":
        normalized = dict(payload)
        if "growth_window" in normalized and "window_years" not in normalized:
            normalized["window_years"] = normalized.pop("growth_window")
        try:
            return cls(**normalized)
        except TypeError as exc:
            raise ValidationError(str(exc)) from exc

    def model_dump(
        self,
        *,
        exclude_none: bool = False,
        by_alias: bool = False,
    ) -> dict[str, Any]:
        payload = asdict(self)
        if by_alias and payload.get("window_years") is not None:
            payload["growth_window"] = payload.pop("window_years")
        if exclude_none:
            payload = {key: value for key, value in payload.items() if value is not None}
        return payload


@dataclass
class ClarificationRequest:
    """Targeted clarification emitted when required intent slots are missing."""

    message: str
    missing_fields: list[str]
    partial_plan: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "ClarificationRequest":
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ValidationError(str(exc)) from exc

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParseResult:
    """Union wrapper for a successful plan or a clarification request."""

    plan: QueryPlan | None = None
    clarification: ClarificationRequest | None = None
    matched_example_id: str | None = None
    provider_used: str | None = None

    @property
    def needs_clarification(self) -> bool:
        return self.clarification is not None


class IntentParser:
    """Parse natural language questions using examples, catalogs, and an optional LLM."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        few_shot_count: int = DEFAULT_FEW_SHOT_COUNT,
    ) -> None:
        self.provider = provider
        self.few_shot_count = few_shot_count
        self.catalogs = load_semantic_catalogs()
        self.examples = self._load_examples()

    def parse(self, question: str) -> ParseResult:
        example = self._match_example(question)
        if example is not None:
            plan = QueryPlan.model_validate(example["structured_query_plan"])
            return ParseResult(plan=plan, matched_example_id=example["example_id"])

        if self.provider is not None:
            payload = self.provider.complete_json(
                system_prompt=self.build_system_prompt(),
                user_prompt=self.build_user_prompt(question),
            )
            return self._parse_provider_payload(payload)

        heuristic_plan = self._heuristic_parse(question)
        if heuristic_plan is not None:
            return self._finalize_plan(heuristic_plan)

        return self._build_clarification(
            partial_plan={"question_type": self._infer_question_type(question)},
            missing_fields=["metric_id", "geo_level", "question_type"],
        )

    def build_system_prompt(self) -> str:
        metric_lines = [
            f"- {metric['metric_id']}: {metric['display_name']} "
            f"(subject_area={metric['subject_area']}, table={metric['source_table']})"
            for metric in self.catalogs["metric_catalog"]["metrics"]
            if metric.get("status") == "active"
        ]
        table_lines = [
            f"- {table['table_id']}: subject_area={table['subject_area']}, "
            f"geo_levels={', '.join(table['supported_geo_levels'])}"
            for table in self.catalogs["table_catalog"]["tables"]
            if table.get("status") == "active"
        ]
        geo_lines = [
            f"- {geo['geo_level']}: {geo['display_name']}"
            for geo in self.catalogs["geography_catalog"]["geo_levels"]
            if geo.get("supported_in_mvp")
        ]
        few_shots = "\n".join(self._few_shot_examples())
        return (
            "You convert user questions into a JSON query plan for a constrained analytics chatbot.\n"
            "Only use approved tables, metrics, and geographies from the catalogs below.\n"
            "If required slots are missing, return JSON with keys clarification_needed=true, "
            "missing_fields, message, and partial_plan.\n"
            "Otherwise return JSON with clarification_needed=false and a query_plan object.\n\n"
            "Supported question types: ranking, trend, comparison, distribution, benchmark, growth.\n\n"
            "Approved tables:\n"
            f"{chr(10).join(table_lines)}\n\n"
            "Approved metrics:\n"
            f"{chr(10).join(metric_lines)}\n\n"
            "Approved geo levels:\n"
            f"{chr(10).join(geo_lines)}\n\n"
            "Few-shot examples:\n"
            f"{few_shots}"
        )

    def build_user_prompt(self, question: str) -> str:
        return (
            "Return only JSON.\n"
            f"Question: {question}\n"
        )

    def _parse_provider_payload(self, payload: dict[str, Any]) -> ParseResult:
        if payload.get("clarification_needed"):
            clarification = ClarificationRequest.model_validate(
                {
                    "message": payload.get("message") or "Please clarify the missing intent slots.",
                    "missing_fields": payload.get("missing_fields") or [],
                    "partial_plan": payload.get("partial_plan") or {},
                }
            )
            return ParseResult(clarification=clarification, provider_used=type(self.provider).__name__)

        query_plan_payload = payload.get("query_plan", payload)
        try:
            plan = QueryPlan.model_validate(query_plan_payload)
        except ValidationError:
            heuristic_plan = self._heuristic_parse(json.dumps(query_plan_payload, sort_keys=True))
            if heuristic_plan is None:
                raise
            return self._finalize_plan(heuristic_plan, provider_used=type(self.provider).__name__)
        return self._finalize_plan(plan, provider_used=type(self.provider).__name__)

    def _finalize_plan(
        self,
        plan: QueryPlan | dict[str, Any],
        provider_used: str | None = None,
    ) -> ParseResult:
        query_plan = plan if isinstance(plan, QueryPlan) else QueryPlan.model_validate(plan)
        missing = self._required_missing_fields(query_plan)
        if missing:
            return self._build_clarification(query_plan.model_dump(exclude_none=True), missing, provider_used)
        return ParseResult(plan=query_plan, provider_used=provider_used)

    def _build_clarification(
        self,
        partial_plan: dict[str, Any],
        missing_fields: list[str],
        provider_used: str | None = None,
    ) -> ParseResult:
        labels = ", ".join(missing_fields)
        clarification = ClarificationRequest(
            message=f"I can help with that, but I need {labels} to build a safe query.",
            missing_fields=missing_fields,
            partial_plan=partial_plan,
        )
        return ParseResult(clarification=clarification, provider_used=provider_used)

    def _few_shot_examples(self) -> list[str]:
        rendered: list[str] = []
        for example in self.examples[: self.few_shot_count]:
            payload = {
                "clarification_needed": False,
                "query_plan": example["structured_query_plan"],
            }
            rendered.append(
                f"Q: {example['natural_language_question']}\nA: {json.dumps(payload, sort_keys=True)}"
            )
        return rendered

    def _match_example(self, question: str) -> dict[str, Any] | None:
        normalized_question = self._normalize_text(question)
        for example in self.examples:
            if self._normalize_text(example["natural_language_question"]) == normalized_question:
                return example
        return None

    def _heuristic_parse(self, question: str) -> QueryPlan | None:
        normalized = self._normalize_text(question)
        question_type = self._infer_question_type(normalized)
        metric = self._infer_metric(normalized)
        geo_level = self._infer_geo_level(normalized)
        year = self._infer_latest_year_reference(normalized)
        sort_direction = "desc"

        if metric is None and not any(token in normalized for token in ["growth", "growing", "increase", "gain"]):
            return None

        if "over time" in normalized or "trend" in normalized:
            return QueryPlan(
                question_type="trend",
                metric_id=metric["metric_id"] if metric else None,
                source_table=metric["source_table"] if metric else None,
                subject_area=metric["subject_area"] if metric else None,
                geo_level=geo_level,
                start_year=2015,
                end_year=year or 2024,
            )

        if "compare" in normalized and "vs" not in normalized:
            return QueryPlan(
                question_type="comparison",
                metric_id=metric["metric_id"] if metric else None,
                source_table=metric["source_table"] if metric else None,
                subject_area=metric["subject_area"] if metric else None,
                geo_level=geo_level,
                year=year,
            )

        if "distribution" in normalized or "spread" in normalized:
            return QueryPlan(
                question_type="distribution",
                metric_id=metric["metric_id"] if metric else None,
                source_table=metric["source_table"] if metric else None,
                subject_area=metric["subject_area"] if metric else None,
                geo_level=geo_level,
                year=year,
            )

        if "benchmark" in normalized or "compare" in normalized or " versus " in normalized or " vs " in normalized:
            target_geo_level = geo_level
            return QueryPlan(
                question_type="benchmark",
                metric_id=metric["metric_id"] if metric else None,
                source_table=metric["source_table"] if metric else None,
                subject_area=metric["subject_area"] if metric else None,
                target_geo_level=target_geo_level,
                year=year,
                benchmark_type="us" if " united states" in normalized or " us " in f" {normalized} " else None,
            )

        if any(token in normalized for token in ["growth", "growing", "increase", "gain"]):
            base_metric = metric
            if base_metric is None:
                base_metric = self._default_growth_metric(normalized)
            return QueryPlan(
                question_type=question_type,
                base_metric_id=base_metric["metric_id"] if base_metric else None,
                source_table=base_metric["source_table"] if base_metric else None,
                subject_area=base_metric["subject_area"] if base_metric else None,
                geo_level=geo_level,
                end_year=year,
                window_years=5 if "5 year" in normalized or "five year" in normalized else None,
                sort_direction=sort_direction,
                limit=10,
            )

        if question_type == "ranking":
            return QueryPlan(
                question_type="ranking",
                metric_id=metric["metric_id"] if metric else None,
                source_table=metric["source_table"] if metric else None,
                subject_area=metric["subject_area"] if metric else None,
                geo_level=geo_level,
                year=year,
                sort_direction=sort_direction,
                limit=10,
            )

        return None

    def _required_missing_fields(self, plan: QueryPlan) -> list[str]:
        if plan.template_id is None:
            return ["question_type"]

        template = self.catalogs["templates"].get(plan.template_id)
        if template is None:
            return ["question_type"]

        missing: list[str] = []
        payload = plan.model_dump(by_alias=False, exclude_none=True)
        for field in template.get("required_slots", []):
            if field not in payload or payload[field] in (None, [], ""):
                missing.append(field)
        return missing

    def _infer_question_type(self, question: str) -> str:
        if any(token in question for token in ["over time", "trend"]):
            return "trend"
        if any(token in question for token in ["distribution", "spread"]):
            return "distribution"
        if any(token in question for token in ["growth", "growing", "increase", "gain"]):
            return "growth"
        if "benchmark" in question or " vs " in f" {question} " or " versus " in question:
            return "benchmark"
        if "compare" in question:
            return "comparison"
        return "ranking"

    def _infer_metric(self, question: str) -> dict[str, Any] | None:
        metric_patterns = [
            ("population", "pop_total"),
            ("median age", "median_age"),
            ("hispanic", "pct_hispanic"),
            ("gross rent", "median_gross_rent"),
            ("rent burden", "pct_rent_burden_30plus"),
            ("home value", "median_home_value"),
            ("housing unit", "hu_total"),
            ("median household income", "median_hh_income"),
            ("household income", "median_hh_income"),
            ("per capita income", "calc_income_pc"),
            ("income", "calc_income_pc"),
            ("rent to income", "rent_to_income"),
        ]
        for pattern, metric_id in metric_patterns:
            if pattern in question:
                return self.catalogs["metrics"][metric_id]
        return None

    def _default_growth_metric(self, question: str) -> dict[str, Any] | None:
        if "population" in question:
            return self.catalogs["metrics"]["pop_total"]
        if "home value" in question:
            return self.catalogs["metrics"]["median_home_value"]
        if "rent" in question:
            return self.catalogs["metrics"]["median_gross_rent"]
        if "income" in question:
            return self.catalogs["metrics"]["calc_income_pc"]
        return None

    def _infer_geo_level(self, question: str) -> str | None:
        patterns = [
            ("states", "state"),
            ("state", "state"),
            ("cbsas", "cbsa"),
            ("cbsa", "cbsa"),
            ("metros", "cbsa"),
            ("metro", "cbsa"),
            ("counties", "county"),
            ("county", "county"),
            ("regions", "region"),
            ("region", "region"),
            ("divisions", "division"),
            ("division", "division"),
            ("us", "us"),
            ("united states", "us"),
        ]
        for pattern, geo_level in patterns:
            if pattern in question:
                return geo_level
        return None

    def _infer_latest_year_reference(self, question: str) -> int | None:
        match = re.search(r"\b(20\d{2})\b", question)
        if match:
            return int(match.group(1))
        if "latest" in question or "current" in question:
            return 2024
        return None

    def _load_examples(self) -> list[dict[str, Any]]:
        payload = yaml.safe_load(QUESTION_LIBRARY_PATH.read_text(encoding="utf-8"))
        return payload["examples"]

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())
