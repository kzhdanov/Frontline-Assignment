from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ToolEvent:
    index: int
    turn: int
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass
class Finding:
    check: str
    status: str
    evidence: str


@dataclass
class JudgeScore:
    criterion: str
    score: int
    evidence: str


@dataclass
class JudgeResult:
    run: int
    scores: list[JudgeScore]
    summary: str


@dataclass
class EvaluationResult:
    run_id: str
    scenario: str
    started_at: str
    agent_model: str
    judge_model: str
    execution_mode: str
    evidence_source: str
    evaluation_subject: str
    scenario_hash: str
    trace_hash: str
    termination_reason: str
    duration_seconds: float
    messages: list[dict[str, Any]]
    tool_events: list[ToolEvent]
    findings: list[Finding]
    judge_results: list[JudgeResult] = field(default_factory=list)
    median_scores: dict[str, float] = field(default_factory=dict)
    usage: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
