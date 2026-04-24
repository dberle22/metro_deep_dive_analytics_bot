"""End-to-end orchestration for the Phase 3 text-to-SQL pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency in bare environments
    pd = None

from app.intent.parser import ClarificationRequest, IntentParser, ParseResult, QueryPlan
from app.llm.provider import LLMProvider, get_llm_provider
from app.query.executor import QueryExecutor
from app.query.generator import QueryGenerator, RenderedQuery
from app.query.planner import PlannedQuery, QueryPlanner
from app.query.validator import QueryValidator, ValidationResult


@dataclass
class OrchestrationResult:
    """Full Phase 3 pipeline output for one user question."""

    question: str
    parse_result: ParseResult
    query_plan: QueryPlan | None = None
    planned_query: PlannedQuery | None = None
    rendered_query: RenderedQuery | None = None
    validation: ValidationResult | None = None
    dataframe: pd.DataFrame | None = None

    @property
    def clarification(self) -> ClarificationRequest | None:
        return self.parse_result.clarification

    @property
    def needs_clarification(self) -> bool:
        return self.parse_result.needs_clarification

    @property
    def sql(self) -> str | None:
        return None if self.rendered_query is None else self.rendered_query.sql


class Orchestrator:
    """Wire intent parsing through execution with validation in the middle."""

    def __init__(
        self,
        *,
        parser: IntentParser | None = None,
        planner: QueryPlanner | None = None,
        generator: QueryGenerator | None = None,
        validator: QueryValidator | None = None,
        executor: QueryExecutor | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self.parser = parser or IntentParser(provider=provider)
        self.planner = planner or QueryPlanner()
        self.generator = generator or QueryGenerator()
        self.validator = validator or QueryValidator()
        self.executor = executor

    @classmethod
    def from_env(cls) -> "Orchestrator":
        """Construct an orchestrator using the configured LLM provider and database."""

        provider = get_llm_provider()
        return cls(provider=provider, executor=QueryExecutor())

    def run(self, question: str) -> OrchestrationResult:
        parse_result = self.parser.parse(question)
        result = OrchestrationResult(question=question, parse_result=parse_result)
        if parse_result.needs_clarification:
            return result

        assert parse_result.plan is not None
        result.query_plan = parse_result.plan
        result.planned_query = self.planner.build(parse_result.plan)
        result.rendered_query = self.generator.render(result.planned_query.plan)
        result.validation = self.validator.validate(result.rendered_query)
        result.validation.raise_for_errors()

        if self.executor is not None:
            result.dataframe = self.executor.execute(result.rendered_query)

        return result

    def preview(self, question: str) -> dict[str, Any]:
        """Convenience method for REPL debugging."""

        result = self.run(question)
        return {
            "needs_clarification": result.needs_clarification,
            "clarification": None
            if result.clarification is None
            else result.clarification.model_dump(),
            "query_plan": None
            if result.query_plan is None
            else result.query_plan.model_dump(exclude_none=True),
            "sql": result.sql,
            "row_count": None if result.dataframe is None else len(result.dataframe),
        }
