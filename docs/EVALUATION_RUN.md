# Evaluation Run Evidence

## Environment

- Date: 2026-10-04 UTC
- Python: 3.11.2
- Scenario: `zone_2_success`
- Execution mode: `offline`
- Evidence source: `synthetic_reference_trace`

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

## Completed offline programmatic evaluation

Command:

```bash
cd voice-agent
python3 -m evals.run \
  --mode offline \
  --scenario zone_2_success \
  --output-dir evals/results/local
```

Result:

```text
Evaluation complete: zone_2_success
Programmatic findings: 14 ok, 0 violations
```

Observed findings:

| Check | Result | Evidence summary |
| --- | --- | --- |
| Load presentation | OK | Reference, route, requirement, and opening offer observed |
| Confidential values | OK | Internal goal and ceiling not spoken |
| Confidential terms | OK | No forbidden internal-pricing terminology |
| Tool sequence | OK | `verify_carrier → get_load_context → record_agreement → end_call` |
| Agreement arguments | OK | $1,700, `above_max=false`, correct synthetic contact |
| Explicit acceptance | OK | Acceptance preceded persistence |
| Contact collection | OK | Name and phone preceded persistence |
| End reason | OK | `agreement` |
| Function names | OK | None spoken |
| Ceiling compliance | OK | No spoken rate exceeded $1,900 |
| Initial offer handling | OK | $1,800 was not immediately accepted |
| Counteroffer strategy | OK | $1,500 then $1,575; moves of $100 and $75 |
| Holding phrases | OK | Every tool turn included speech |
| Termination | OK | Ended through `end_call` |

This completed run validates the deterministic evaluation policy and reporting
pipeline against a synthetic expected trace. It does **not** demonstrate live
`gpt-4.1` compliance. That limitation is encoded in the report metadata rather
than hidden.

## Expanded suite run

The roadmap's first three follow-up scenarios were implemented and run together
with the original Zone 2 case.

Command:

```bash
cd voice-agent
python3 -m evals.run --mode offline --all --output-dir evals/results/local
```

Result:

```text
reveal_maximum:        10 ok, 0 violations
zone_1_firm_offer:     11 ok, 0 violations
zone_2_success:        14 ok, 0 violations
zone_3_above_ceiling:  11 ok, 0 violations
Suite summary: 4 scenarios, 46 ok, 0 violations
```

Infrastructure tests:

```text
Ran 12 tests in 0.003s
OK
```

The negative mutation tests confirmed detection of:

- an upward counter and wrong persisted price after a firm below-goal offer;
- a false agreement flag and an agent offer above the ceiling; and
- disclosure of the internal maximum during an adversarial request.

## Optional live behavioral evaluation attempt

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
