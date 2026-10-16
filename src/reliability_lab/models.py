"""Strict input contracts for synthetic evaluation cases."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AssistantResponse(BaseModel):
    """Output structure only; factual correctness needs separate evaluators."""

    model_config = ConfigDict(extra="forbid", strict=True)

    summary: NonEmptyText
    action: Literal["answer", "refuse", "escalate"]
    facts: dict[NonEmptyText, NonEmptyText]
    disclaimer: NonEmptyText


class Expectations(BaseModel):
    """Explicit, objective rules supplied by the dataset author."""

    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["answer", "refuse", "escalate"]
    facts: dict[NonEmptyText, NonEmptyText] = Field(min_length=1)
    prohibited_phrases: list[NonEmptyText] = Field(min_length=1)
    disclaimer: NonEmptyText


class EvaluationCase(BaseModel):
    """Version-two case with executable expectations."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: Literal["2.0"]
    dataset_id: NonEmptyText
    case_id: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]*$")]
    category: Literal[
        "well_formed", "missing_fields", "invalid_output", "unsupported_claim",
        "contradiction", "incomplete", "refusal", "escalation",
    ]
    scenario: NonEmptyText
    expected_behavior: NonEmptyText
    severity: Literal["low", "medium", "high", "critical"]
    criteria: list[NonEmptyText] = Field(min_length=1)
    expectations: Expectations
