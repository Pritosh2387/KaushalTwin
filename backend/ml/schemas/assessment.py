"""
KaushalTwin ML Service — Pydantic Schemas: Assessment / Task Selection (Module 5)
"""

from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Competency state input (for task selection)
# ---------------------------------------------------------------------------

class CompetencyStateInput(BaseModel):
    nos_id: str
    mandatory: bool = False
    importance: float = Field(1.0, ge=0.0, le=2.0)
    weight: float = Field(1.0, ge=0.0, le=2.0, description="Alias for importance")
    evidence_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    evidence_coverage: float = Field(0.0, ge=0.0, le=1.0)
    competency_score: float = Field(0.0, ge=0.0, le=100.0)


# ---------------------------------------------------------------------------
# Task NOS coverage
# ---------------------------------------------------------------------------

class TaskNOSCoverage(BaseModel):
    nos_id: str
    coverage: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Task criterion
# ---------------------------------------------------------------------------

class TaskCriterion(BaseModel):
    id: str
    name: str
    weight: float
    max_score: float = 5.0


# ---------------------------------------------------------------------------
# Task variant
# ---------------------------------------------------------------------------

class TaskVariant(BaseModel):
    id: str
    code: str
    label: str
    parameters: dict = {}


# ---------------------------------------------------------------------------
# Task (in/out)
# ---------------------------------------------------------------------------

class TaskInput(BaseModel):
    id: str
    title: str
    description: str = ""
    trade: str = "electrician"
    difficulty: str = "medium"
    duration_minutes: int = 10
    mandatory: bool = False
    active: bool = True
    randomizable: bool = False
    nos_coverage: list[TaskNOSCoverage] = []
    criteria: list[TaskCriterion] = []
    variants: list[TaskVariant] = []


# ---------------------------------------------------------------------------
# Next task request/response
# ---------------------------------------------------------------------------

class NextTaskRequest(BaseModel):
    competency_states: list[CompetencyStateInput] = Field(..., min_length=1)
    available_tasks: Optional[list[TaskInput]] = Field(None, description="If omitted, uses built-in demo tasks")
    exclude_task_ids: Optional[list[str]] = None


class RankedTask(BaseModel):
    id: str
    title: str
    description: str
    duration_minutes: int
    mandatory: bool
    priority_score: float
    reason: list[str]
    nos_coverage: list[TaskNOSCoverage]


class NextTaskResponse(BaseModel):
    selected_task: Optional[RankedTask]
    priority_score: float
    reason: list[str]
    alternatives: list[RankedTask] = []
    note: str = "Task selection is deterministic. No LLM was used to choose this task."


# ---------------------------------------------------------------------------
# Rank tasks
# ---------------------------------------------------------------------------

class RankTasksRequest(BaseModel):
    competency_states: list[CompetencyStateInput] = Field(..., min_length=1)
    available_tasks: Optional[list[TaskInput]] = None
    exclude_task_ids: Optional[list[str]] = None


class RankTasksResponse(BaseModel):
    ranked_tasks: list[RankedTask]
    count: int


# ---------------------------------------------------------------------------
# Variant selection
# ---------------------------------------------------------------------------

class VariantSelectRequest(BaseModel):
    task_id: str
    available_tasks: Optional[list[TaskInput]] = None
    exclude_variant_codes: Optional[list[str]] = None
    seed: Optional[int] = Field(None, description="Set for reproducible selection in tests")


class VariantSelectResponse(BaseModel):
    task_id: str
    task_title: str
    variant: Optional[TaskVariant]


# ---------------------------------------------------------------------------
# Early stopping
# ---------------------------------------------------------------------------

class ContinuationRequest(BaseModel):
    competency_states: list[CompetencyStateInput]
    coverage_threshold: float = Field(0.8, ge=0.0, le=1.0)


class ContinuationResponse(BaseModel):
    should_continue: bool
    reason: str
    mandatory_gaps: list[str]
    note: str = "Full probabilistic Commit/Abstain logic is reserved for a future module."
