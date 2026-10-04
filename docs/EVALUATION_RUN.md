# Evaluation Run Evidence

## Environment

- Date: 2026-10-04 UTC
- Python: 3.11.2
- Scenario: `zone_2_success`
- Requested judge runs: 3
- Agent model: `gpt-4.1` (default)
- Judge model: `gpt-5.6-sol` (default)

## Offline harness validation

Command:

```bash
cd voice-agent
python3 -m unittest discover -s evals/tests -v
```

Result:

```text
Ran 8 tests in 0.002s
OK
```

The completed tests cover:

- safe in-memory tool success and fail-closed behavior;
- complete scripted conversation and initial-to-negotiation prompt transition;
- expected tool ordering and normal termination;
- programmatic happy-path findings;
- confidential-value and termination violation detection;
- strict judge response validation; and
- preservation of three judge runs with median score calculation.

No external service was called by these tests.

## Live behavioral evaluation attempt

Command:

```bash
cd voice-agent
PYTHONPATH=.:../shared python3 -m evals.run \
  --scenario zone_2_success \
  --judge-runs 3 \
  --output-dir evals/results/local
```

Result:

```text
evaluation infrastructure error: OPENAI_API_KEY is required for a live evaluation
```

Exit code: `2`, as designed for an infrastructure/configuration error.

The assessment workspace does not provide an `OPENAI_API_KEY` to subprocesses,
so no live agent transcript or LLM-judge scores were generated. This is not a
behavioral result and must not be interpreted as an agent failure. No synthetic
score was substituted. Once a development key with access to both configured
models is supplied, rerun the command above to produce the Markdown and JSON
behavioral artifacts.
