# Voice agent evaluations

This directory contains a safe text-only evaluation harness. Its default mode
regression-tests the scorer against committed synthetic transcripts. It needs
no credentials or network access and never calls telephony, speech, database,
carrier, quote, transfer, or notification services.

## Run

From `voice-agent/` with the project environment active:

```bash
python3 -m evals.run --mode offline --scenario zone_2_success
```

Run every implemented scenario:

```bash
python3 -m evals.run --mode offline --all --fail-on-violation
```

Results are written as Markdown and JSON under `evals/results/local/`. Without
`--fail-on-violation`, findings are diagnostic. With it, any policy violation
returns exit code 1 for CI; configuration and runner failures return exit code
2.

The offline evidence source is explicitly labeled `synthetic_reference_trace`.
It validates the evaluator and expected policy, not agent compliance. Reports
label this explicitly as `evaluation_subject=scorer_regression`.

To evaluate an agent trace captured by another runner, provide a JSON object
with `messages` and `termination_reason`. Tool events are derived from the
assistant tool calls and their matching tool-result messages, so there is only
one source of truth:

```bash
python3 -m evals.run \
  --scenario zone_2_success \
  --trace-file path/to/trace.json \
  --fail-on-violation
```

These reports are labeled `evaluation_subject=agent_behavior`. Scenario and
trace SHA-256 values are recorded so results can be tied to exact inputs.

Implemented scenarios:

- `zone_1_firm_offer`
- `zone_2_success`
- `zone_3_above_ceiling`
- `reveal_maximum`

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

Live mode currently supports only `zone_2_success`. Other scenarios and
`--mode live --all` fail with exit code 2 until scenario-specific caller
drivers are implemented.

Programmatic confidentiality checks detect exact numeric and common spoken
forms such as “nineteen hundred.” Arbitrary derived or encoded disclosures
remain unverified without a live adversarial run or semantic judge.
