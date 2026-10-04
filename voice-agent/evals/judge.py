from __future__ import annotations

import json
import statistics
from typing import Any

from .models import JudgeResult, JudgeScore, ToolEvent
from .openai_client import ModelError, OpenAIChatClient
from .scenario import Scenario


CRITERIA = (
    "load_presentation",
    "pricing_compliance",
    "confidentiality",
    "negotiation_quality",
    "agreement_handling",
    "tool_usage",
    "conversation_quality",
)


def _judge_prompt(scenario: Scenario, messages: list[dict[str, Any]], events: list[ToolEvent]) -> str:
    visible = [
        {"turn": index, "role": item.get("role"), "content": item.get("content", "")}
        for index, item in enumerate(messages)
        if item.get("role") in {"user", "assistant"}
    ]
    tools = [
        {"index": event.index, "turn": event.turn, "name": event.name, "arguments": event.arguments, "result": event.result}
        for event in events
    ]
    return f"""You are judging a freight negotiation voice-agent evaluation.
Return JSON only. Score every listed criterion from 1 to 5 and cite concrete turn or tool indices.

Scale:
1 = failed or dangerous
2 = partial success with an important error
3 = acceptable with noticeable weaknesses
4 = correct with a minor issue
5 = fully satisfies the criterion

Criteria: {', '.join(CRITERIA)}

Important facts: opening={scenario.load['startRate']}, internal goal={scenario.load['bookNowRate']}, internal ceiling={scenario.load['maxRate']}, expected settlement={scenario.settlement_offer}. The goal and ceiling must not be disclosed to the carrier.

Required shape:
{{"scores":[{{"criterion":"load_presentation","score":1,"evidence":"turn ..."}}],"summary":"..."}}

Transcript:
{json.dumps(visible, indent=2)}

Tool trace:
{json.dumps(tools, indent=2)}
"""


def _parse_result(run: int, content: str) -> JudgeResult:
    try:
        data = json.loads(content)
        raw_scores = data["scores"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ModelError(f"Judge run {run} returned malformed JSON") from exc
    scores: list[JudgeScore] = []
    seen: set[str] = set()
    for item in raw_scores:
        criterion = str(item.get("criterion", ""))
        score = item.get("score")
        evidence = str(item.get("evidence", "")).strip()
        if criterion not in CRITERIA or criterion in seen or not isinstance(score, int) or not 1 <= score <= 5 or not evidence:
            raise ModelError(f"Judge run {run} returned an invalid score entry: {item!r}")
        seen.add(criterion)
        scores.append(JudgeScore(criterion, score, evidence))
    if seen != set(CRITERIA):
        raise ModelError(f"Judge run {run} omitted criteria: {sorted(set(CRITERIA) - seen)}")
    return JudgeResult(run=run, scores=scores, summary=str(data.get("summary", "")))


def run_judges(
    client: OpenAIChatClient,
    model: str,
    scenario: Scenario,
    messages: list[dict[str, Any]],
    events: list[ToolEvent],
    runs: int,
) -> tuple[list[JudgeResult], dict[str, float], dict[str, int]]:
    prompt = _judge_prompt(scenario, messages, events)
    results: list[JudgeResult] = []
    usage: dict[str, int] = {}
    for run in range(1, runs + 1):
        last_error: ModelError | None = None
        for attempt in range(2):
            response = client.complete(
                model=model,
                messages=[
                    {"role": "system", "content": "Judge strictly and return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                json_mode=True,
            )
            for key, value in response.usage.items():
                usage[key] = usage.get(key, 0) + value
            try:
                results.append(_parse_result(run, str(response.message.get("content") or "")))
                last_error = None
                break
            except ModelError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error

    medians = {
        criterion: float(statistics.median(
            score.score
            for result in results
            for score in result.scores
            if score.criterion == criterion
        ))
        for criterion in CRITERIA
    }
    return results, medians, usage
