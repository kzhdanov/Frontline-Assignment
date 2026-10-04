from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .checks import evaluate_checks
from .conversation import run_conversation
from .judge import run_judges
from .models import EvaluationResult
from .offline import load_reference_trace, load_trace_file
from .openai_client import ModelError, OpenAIChatClient
from .report import write_reports
from .scenario import load_scenario
from .trace import derive_tool_events


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe text evaluation of the voice agent")
    parser.add_argument("--scenario", default="zone_2_success")
    parser.add_argument("--all", action="store_true", help="Run every available scenario")
    parser.add_argument("--trace-file", type=Path, help="Score an externally captured agent trace")
    parser.add_argument("--fail-on-violation", action="store_true")
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument("--judge-runs", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results/local"))
    parser.add_argument("--agent-model", default=os.getenv("EVAL_AGENT_MODEL", "gpt-4.1"))
    parser.add_argument("--judge-model", default=os.getenv("EVAL_JUDGE_MODEL", "gpt-5.6-sol"))
    return parser.parse_args(argv)


def _run_one(args: argparse.Namespace, scenario_name: str) -> tuple[EvaluationResult, Path, Path]:
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    scenario = load_scenario(scenario_name)
    if args.trace_file:
        messages, events, termination, evidence_source = load_trace_file(args.trace_file)
        agent_usage = {}
        judge_usage = {}
        judge_results = []
        medians = {}
        evaluation_subject = "agent_behavior"
    elif args.mode == "offline":
        messages, events, termination, evidence_source = load_reference_trace(scenario.name)
        agent_usage: dict[str, int] = {}
        judge_usage: dict[str, int] = {}
        judge_results = []
        medians = {}
        evaluation_subject = "scorer_regression"
    else:
        client = OpenAIChatClient()
        messages, simulator, termination, agent_usage = run_conversation(scenario, client, args.agent_model)
        events = derive_tool_events(messages)
        evidence_source = "live_model_conversation"
        evaluation_subject = "agent_behavior"
        judge_results, medians, judge_usage = run_judges(
            client, args.judge_model, scenario, messages, events, args.judge_runs
        )
    findings = evaluate_checks(scenario, messages, events, termination)
    scenario_hash = hashlib.sha256(json.dumps(asdict(scenario), sort_keys=True).encode()).hexdigest()
    trace_hash = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()

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
        tool_events=events,
        findings=findings,
        judge_results=judge_results,
        median_scores=medians,
        usage=usage,
        execution_mode=args.mode,
        evidence_source=evidence_source,
        evaluation_subject=evaluation_subject,
        scenario_hash=scenario_hash,
        trace_hash=trace_hash,
    )
    markdown, json_path = write_reports(result, args.output_dir)
    return result, markdown, json_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.judge_runs < 1:
        print("error: --judge-runs must be positive", file=sys.stderr)
        return 2
    if args.mode == "live" and (args.all or args.scenario != "zone_2_success"):
        print("error: live mode currently supports only --scenario zone_2_success", file=sys.stderr)
        return 2
    if args.trace_file and args.all:
        print("error: --trace-file cannot be combined with --all", file=sys.stderr)
        return 2
    names = [args.scenario]
    if args.all:
        names = sorted(path.stem for path in (Path(__file__).parent / "scenarios").glob("*.json"))
    try:
        outputs = [_run_one(args, name) for name in names]
    except (ValueError, ModelError) as exc:
        print(f"evaluation infrastructure error: {exc}", file=sys.stderr)
        return 2
    total_ok = total_violations = 0
    for result, markdown, json_path in outputs:
        ok = sum(f.status == "ok" for f in result.findings)
        violations = len(result.findings) - ok
        total_ok += ok
        total_violations += violations
        label = "Scorer fixture validation" if result.evaluation_subject == "scorer_regression" else "Agent evaluation"
        print(f"{label} complete: {result.scenario}")
        print(f"Programmatic findings: {ok} ok, {violations} violations")
        for criterion, score in result.median_scores.items():
            print(f"  {criterion}: {score:g}/5")
        print(f"Report: {markdown}")
        print(f"JSON: {json_path}")
    if len(outputs) > 1:
        print(f"Suite summary: {len(outputs)} scenarios, {total_ok} ok, {total_violations} violations")
    return 1 if args.fail_on_violation and total_violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
