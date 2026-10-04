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

Run every implemented scenario:

```bash
python3 -m evals.run --mode offline --all
```

Results are diagnostic and written as Markdown and JSON under
`evals/results/local/`. Behavioral findings do not affect the exit status in
this iteration; configuration and runner failures return exit code 2.

The offline evidence source is explicitly labeled `synthetic_reference_trace`.
It validates the evaluator and expected policy, not live model compliance.

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
