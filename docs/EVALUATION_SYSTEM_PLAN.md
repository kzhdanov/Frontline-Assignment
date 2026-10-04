# Voice Agent Evaluation Plan

## Goal

Build a safe, text-based evaluation harness for the freight negotiation voice agent. The first iteration is fully offline and programmatic: it generates structured diagnostic findings without credentials, external services, a release threshold, or an overall pass/fail decision.

## Scope: iteration 1

- Evaluate one complete Zone 2 negotiation conversation.
- Use the production negotiation prompt and production tool schemas.
- Evaluate one committed synthetic reference trace and its tool events.
- Exercise the production prompt builders and production-compatible tool contracts in offline tests.
- Replace every external or side-effecting tool with an in-memory implementation.
- Do not invoke Daily, STT, TTS, Supabase, Salesforce, Highway, quote submission, Slack, or phone transfer services.
- Evaluate the transcript and tool trace with programmatic checks only.
- Do not evaluate the frontend.
- Do not include audio input in this iteration.

## Evaluation flow

1. Load the Zone 2 scenario and its committed synthetic reference trace.
2. Validate the transcript and ordered tool events with deterministic checks.
3. Record each finding with concrete turn, tool, and value evidence.
4. Write human-readable and JSON result artifacts.
5. Separately run offline unit tests that prove known violations are detected and that the production prompt transition and in-memory tools work.

## Case 1: Zone 2 successful negotiation

### Load fixture

| Field | Value |
| --- | --- |
| Reference | `LOAD-1001` |
| Origin | Atlanta, Georgia |
| Destination | Chicago, Illinois |
| Pickup | October 6, 2026 at 9:00 AM |
| Delivery | October 7, 2026 at 3:00 PM |
| Equipment | Dry Van |
| Requirement | Driver must accept tracking |
| Opening offer | $1,400 |
| Internal goal | $1,600 |
| Internal ceiling | $1,900 |

The carrier opens at $1,800, inside Zone 2.

### Scripted caller

1. Provide an MC number.
2. Confirm the carrier returned by `verify_carrier`.
3. Provide reference `LOAD-1001`.
4. Offer $1,800 after the load presentation.
5. Reject the first counteroffer.
6. Respond to the second counteroffer with $1,700.
7. Explicitly accept an agreement at $1,700.
8. Provide a contact name and phone number when requested.
9. Finish after the agent confirms the agreement.

The caller responds to conversation state and tool results, not exact agent wording.

### Expected tool sequence

```text
verify_carrier
→ get_load_context
→ record_agreement
→ end_call
```

Expected final arguments include an agreed price of `$1,700`, `above_max=false`, the supplied contact details, and `end_call(reason="agreement")`.

## Programmatic findings

The report records each check independently. There is no aggregate pass/fail result in iteration 1.

- Required load details and opening offer appeared in the presentation.
- Internal goal and ceiling did not appear in agent speech.
- Forbidden internal-pricing terminology did not appear.
- Counteroffers stayed within the ceiling.
- The agent did not accept the carrier's initial $1,800 offer immediately.
- Counteroffer count and concession sizes matched the prompt strategy.
- The explicitly accepted price stayed consistent.
- Contact information was collected before `record_agreement`.
- Tool names, order, arguments, and call counts were correct.
- `record_agreement` occurred only after explicit acceptance.
- The agent did not speak internal function names.
- The run terminated normally rather than reaching the turn limit.

Every finding includes observed evidence such as turn numbers, tool-call indices, and relevant values.

## Optional LLM judge (deferred)

LLM judging is not part of the required iteration 1 run because the task provides no callable model API or credential to repository code. The existing live path may use `gpt-5.6-sol` as a judge when an external development model gateway is available.

Score applicable criteria from 1 to 5:

| Score | Meaning |
| --- | --- |
| 1 | Failed the objective or behaved dangerously |
| 2 | Partial success with an important error or omission |
| 3 | Acceptable outcome with noticeable weaknesses |
| 4 | Correct with only a minor issue |
| 5 | Fully satisfies the criterion |

Criteria:

- Load presentation
- Pricing compliance
- Confidentiality
- Negotiation quality
- Agreement handling
- Tool usage
- Conversation quality

When enabled later, the judge must return structured JSON and cite transcript turns or tool-call indices for every score. It runs three times against the same agent transcript and tool trace, preserving all outputs and calculating the median per criterion. Judge output cannot erase or override programmatic findings.

## Result artifacts

Each execution writes:

- A readable summary with scenario metadata, evidence source, transcript, tool trace, and programmatic findings.
- A JSON artifact containing the same data for later comparison and thresholding.
- Model identifiers, timestamp, prompt/scenario version, token usage, latency, and termination reason when available.

Results must redact credentials and avoid storing unrelated caller data. Fixtures use synthetic identities and phone numbers.

## Proposed layout

```text
voice-agent/evals/
├── README.md
├── run.py
├── models.py
├── conversation.py
├── offline.py
├── simulated_tools.py
├── checks.py
├── judge.py
├── scenarios/
│   └── zone_2_success.json
├── fixtures/
│   └── zone_2_success_trace.json
└── tests/
    ├── test_checks.py
    └── test_simulated_tools.py
```

Generated result files should go to an ignored output directory rather than being committed by default. One sanitized completed run will be committed as assessment evidence.

## Configuration

- Live API credentials come from environment variables and are never committed.
- Offline mode is the default and requires no credentials.
- Live agent and judge model names remain separate optional settings.
- Optional live mode uses maximum turns and request timeouts to prevent hanging or uncontrolled spend.

## How to run

The implementation exposes a Python module runnable from `voice-agent/`. The
default offline evaluation needs only Python 3.11. It does not require either
voice service process, the web application, credentials, or network access.

### 1. Run the offline evaluation

```bash
cd voice-agent
python3 -m evals.run --mode offline --scenario zone_2_success
```

Optional output selection:

```bash
python3 -m evals.run \
  --mode offline \
  --scenario zone_2_success \
  --output-dir evals/results/local
```

This evaluates the committed synthetic reference trace. It validates the
programmatic evaluation policy and report pipeline; it does not claim that a
live `gpt-4.1` conversation was executed.

### 2. Inspect results

The command prints a compact summary and writes two files:

```text
evals/results/local/zone_2_success-<run-id>.md
evals/results/local/zone_2_success-<run-id>.json
```

The Markdown report is for human review. The JSON report is the canonical
machine-readable record and contains:

- run and model metadata;
- the complete synthetic transcript;
- ordered tool calls and results;
- each programmatic finding with evidence;
- token usage, latency, and termination reason when available.

Because iteration 1 is diagnostic, behavioral findings do not produce an
overall pass/fail status and do not cause a nonzero process exit. The command
returns nonzero only when it cannot complete the evaluation due to invalid
configuration, malformed fixture data, or an internal runner error.

### 3. Run harness tests

Unit tests for checks and simulated tools must not call an LLM or any external
service:

```bash
cd voice-agent
python -m pytest evals/tests -v --tb=short
```

The tests are also runnable without pytest:

```bash
python3 -m unittest discover -s evals/tests -v
```

These tests validate the evaluation infrastructure and known-failure
detection. They make no model or external-service calls.

## Deferred work

- Additional pricing, failure, transfer, adversarial, and identity scenarios
- Release thresholds and aggregate pass/fail policy
- Multiple agent runs for measuring agent variance
- Required live agent and LLM-judge execution when a development gateway is available
- Audio, STT, TTS, latency, interruption, Daily, and real transfer evaluation
- Frontend evaluation
- CI execution of credentialed live evaluations

## Implementation order

1. Define scenario, trace, and result schemas.
2. Implement the safe tool simulator and tool trace.
3. Implement programmatic checks with unit tests.
4. Add offline CLI execution and artifact generation.
5. Run the scenario, inspect all evidence, and commit one sanitized result.
6. Keep live conversation and three-run judge support optional until model access is supplied.
