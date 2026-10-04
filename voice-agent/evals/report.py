from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationResult


def write_reports(result: EvaluationResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{result.scenario}-{result.run_id}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Evaluation: {result.scenario}",
        "",
        f"- Run: `{result.run_id}`",
        f"- Agent model: `{result.agent_model}`",
        f"- Judge model: `{result.judge_model}`",
        f"- Execution mode: `{result.execution_mode}`",
        f"- Evidence source: `{result.evidence_source}`",
        f"- Termination: `{result.termination_reason}`",
        f"- Duration: `{result.duration_seconds:.2f}s`",
        "",
        "## Programmatic findings",
        "",
    ]
    lines.extend(f"- **{item.status.upper()}** `{item.check}` — {item.evidence}" for item in result.findings)
    if result.median_scores:
        lines.extend(["", "## Median judge scores", ""])
        lines.extend(f"- `{name}`: {score:g}/5" for name, score in result.median_scores.items())
    lines.extend(["", "## Transcript", ""])
    for index, message in enumerate(result.messages):
        if message.get("role") in {"user", "assistant"}:
            lines.append(f"**Turn {index} — {message['role']}**: {message.get('content') or '[tool call]'}")
            lines.append("")
    lines.extend(["## Tool trace", ""])
    for event in result.tool_events:
        lines.append(f"- `{event.index}` `{event.name}` args={json.dumps(event.arguments, sort_keys=True)} result={json.dumps(event.result, sort_keys=True)}")
    if result.judge_results:
        lines.extend(["", "## Judge runs", ""])
        for judge in result.judge_results:
            lines.append(f"### Run {judge.run}")
            lines.append("")
            for score in judge.scores:
                lines.append(f"- `{score.criterion}`: {score.score}/5 — {score.evidence}")
            lines.append(f"- Summary: {judge.summary}")
            lines.append("")
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return markdown_path, json_path
