# Voice Agent Evaluation Plan

## Goal

Build a safe, text-based evaluation harness for the freight negotiation voice agent. The first iteration is diagnostic: it generates structured results but does not enforce a release threshold or overall pass/fail decision.

## Scope: iteration 1

- Evaluate one complete Zone 2 negotiation conversation.
- Use the production negotiation prompt and production tool schemas.
- Call the agent model through a live API. Keep the agent model configurable; default to the model used by the voice agent.
- Replace every external or side-effecting tool with an in-memory implementation.
- Do not invoke Daily, STT, TTS, Supabase, Salesforce, Highway, quote submission, Slack, or phone transfer services.
- Evaluate the completed transcript and tool trace with programmatic checks and an LLM judge.
- Do not evaluate the frontend.
- Do not include audio input in this iteration.

## Evaluation flow

1. Load the scenario and construct the real production prompt.
2. Start a text conversation with the agent model.
3. Drive the caller with a deterministic scripted state machine.
4. Execute requested tools against safe in-memory fixtures using the production tool contracts.
5. Stop at `end_call`, a turn limit, or an unrecoverable protocol error.
6. Run deterministic checks over the transcript and tool trace.
7. Ask `gpt-5.6-sol` to judge the same completed run three independent times.
8. Report each judge result and the median score for every criterion.
9. Write human-readable and JSON result artifacts.

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

## LLM judge

Use `gpt-5.6-sol` only as the judge. Give it the scenario, scoring rubric, transcript, and tool trace. Do not give it access to external tools or production services.

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

The judge must return structured JSON and cite transcript turns or tool-call indices for every score. Run the judge three times against the same agent transcript and tool trace. Preserve all three results and calculate the median per criterion. Judge output cannot erase or override programmatic findings.

## Result artifacts

Each execution writes:

- A readable summary with scenario metadata, transcript, tool trace, programmatic findings, three judge results, and median scores.
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
├── simulated_tools.py
├── checks.py
├── judge.py
├── scenarios/
│   └── zone_2_success.yaml
└── tests/
    ├── test_checks.py
    └── test_simulated_tools.py
```

Generated result files should go to an ignored output directory rather than being committed by default. One sanitized completed run will be committed as assessment evidence.

## Configuration

- Live API credentials come from environment variables and are never committed.
- Agent and judge model names are separate settings.
- Judge model defaults to `gpt-5.6-sol`.
- The initial runner is live-only; replay support is deferred.
- Maximum turns and request timeouts prevent hanging or uncontrolled spend.

## Deferred work

- Additional pricing, failure, transfer, adversarial, and identity scenarios
- Release thresholds and aggregate pass/fail policy
- Replay mode and deterministic regression fixtures
- Multiple agent runs for measuring agent variance
- Audio, STT, TTS, latency, interruption, Daily, and real transfer evaluation
- Frontend evaluation
- CI execution of credentialed live evaluations

## Implementation order

1. Define scenario and result schemas.
2. Implement the safe tool simulator and tool trace.
3. Implement the live text conversation runner and scripted caller.
4. Implement programmatic checks with unit tests.
5. Implement the three-run structured LLM judge and median aggregation.
6. Add CLI documentation and artifact generation.
7. Run the scenario, inspect all evidence, and commit one sanitized result.
