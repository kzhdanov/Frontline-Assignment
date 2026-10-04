# Voice agent evaluations

This directory contains a safe text-only evaluation harness. Its default mode
scores a committed synthetic transcript and tool trace using deterministic
checks. It needs no credentials or network access and never calls telephony,
speech, database, carrier, quote, transfer, or notification services.

## Run

From `voice-agent/` with the project environment active:

```bash
python3 -m evals.run --mode offline --scenario zone_2_success
```

Results are diagnostic and written as Markdown and JSON under
`evals/results/local/`. Behavioral findings do not affect the exit status in
this iteration; configuration and runner failures return exit code 2.

The offline evidence source is explicitly labeled `synthetic_reference_trace`.
It validates the evaluator and expected policy, not live model compliance.

## Test the harness

```bash
python -m pytest evals/tests -v --tb=short
```

These tests are offline and make no model or service calls.
They can also run without pytest:

```bash
python -m unittest discover -s evals/tests -v
```

## Optional live mode

Live agent execution and three-run LLM judging remain available only when a
development API credential and API-accessible model names are supplied:

```bash
export OPENAI_API_KEY="<development key>"
python -m evals.run --mode live --scenario zone_2_success --judge-runs 3
```
