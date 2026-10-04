# Voice agent evaluations

This directory contains a safe text-only evaluation harness. It calls the live
agent and judge models, but all agent tools execute against synthetic in-memory
fixtures. It never calls telephony, speech, database, carrier, quote, transfer,
or notification services.

## Run

From `voice-agent/` with the project environment active:

```bash
export OPENAI_API_KEY="<development API key>"
export EVAL_AGENT_MODEL="gpt-4.1"
export EVAL_JUDGE_MODEL="gpt-5.6-sol"
python -m evals.run --scenario zone_2_success --judge-runs 3
```

Results are diagnostic and written as Markdown and JSON under
`evals/results/local/`. Behavioral findings do not affect the exit status in
this iteration; configuration and runner failures return exit code 2.

## Test the harness

```bash
python -m pytest evals/tests -v --tb=short
```

These tests are offline and make no model or service calls.
They can also run without pytest:

```bash
python -m unittest discover -s evals/tests -v
```
