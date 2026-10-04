from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .checks import evaluate_checks
from .conversation import run_conversation
from .judge import run_judges
from .models import EvaluationResult
from .openai_client import ModelError, OpenAIChatClient
from .report import write_reports
from .scenario import load_scenario


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe text evaluation of the voice agent")
    parser.add_argument("--scenario", default="zone_2_success")
    parser.add_argument("--judge-runs", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results/local"))
    parser.add_argument("--agent-model", default=os.getenv("EVAL_AGENT_MODEL", "gpt-4.1"))
    parser.add_argument("--judge-model", default=os.getenv("EVAL_JUDGE_MODEL", "gpt-5.6-sol"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.judge_runs < 1:
        print("error: --judge-runs must be positive", file=sys.stderr)
        return 2
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        scenario = load_scenario(args.scenario)
        client = OpenAIChatClient()
        messages, simulator, termination, agent_usage = run_conversation(scenario, client, args.agent_model)
        findings = evaluate_checks(scenario, messages, simulator.events, termination)
        judge_results, medians, judge_usage = run_judges(
            client, args.judge_model, scenario, messages, simulator.events, args.judge_runs
        )
    except (ValueError, ModelError) as exc:
        print(f"evaluation infrastructure error: {exc}", file=sys.stderr)
        return 2

    usage = {f"agent_{key}": value for key, value in agent_usage.items()}
    usage.update({f"judge_{key}": value for key, value in judge_usage.items()})
    result = EvaluationResult(
        run_id=f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}",
        scenario=scenario.name,
        started_at=started_at,
        agent_model=args.agent_model,
        judge_model=args.judge_model,
        termination_reason=termination,
        duration_seconds=time.monotonic() - started,
        messages=messages,
        tool_events=simulator.events,
        findings=findings,
        judge_results=judge_results,
        median_scores=medians,
        usage=usage,
    )
    markdown, json_path = write_reports(result, args.output_dir)
    print(f"Evaluation complete: {scenario.name}")
    print(f"Programmatic findings: {sum(f.status == 'ok' for f in findings)} ok, {sum(f.status != 'ok' for f in findings)} violations")
    for criterion, score in medians.items():
        print(f"  {criterion}: {score:g}/5")
    print(f"Report: {markdown}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

