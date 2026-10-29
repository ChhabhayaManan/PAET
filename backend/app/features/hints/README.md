# hints

The hint ladder. Each request for a problem gives the next rung, from a nudge up to a
concrete pointer, never the fix itself. Every LLM-written hint passes a guardrail that
rejects quoted reference code and asks a judge whether the hint states the fix. Approach
hints (before any code is written) serve the chat. Hint use is recorded so mastery and the
leak rate can account for it.

## Endpoints

None of its own. Hints are served by `POST /api/v1/feedback/hint` (`feedback/router.py`)
and by the chat's `get_hint` tool.

## Tables

- Writes: `hint_events`
- Reads: `problems`, `test_cases`, `code_submissions`, `code_evaluations`, `learning_events`

## Files

```
service.py           request_hint(), approach_hint(), next_level(), leak_rate()
logic/guardrail.py   code-quote check and the states_fix judge
logic/prompts.py     one template per ladder level, plus approach templates
models.py            HintEvent
```
