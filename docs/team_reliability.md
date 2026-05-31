# Team Reliability

The reliability layer answers a process question:

```text
Is the autonomous SDLC team becoming more or less trustworthy over time?
```

Run it with:

```bash
PATH=".venv/bin:$PATH" make team-reliability
```

The scorer reads reports under `state/reports/`, writes
`state/reports/team-reliability_report.json`, and appends a compact history
entry to `state/reports/team-reliability_history.jsonl`.

## Scoring Rules

The score does not punish the team for catching a real regression. If tests or
review gates fail because they found a real issue, that is classified as a
caught regression. It still blocks release, but it is evidence the process
worked.

The score goes down when:

- a required report is missing or malformed
- framework drift or harness quality fails
- feedback later identifies an escaped regression
- feedback identifies false positives or noisy checks

## Feedback Input

Future bug-ticket or production feedback can be added as newline-delimited JSON
in `state/team_feedback.jsonl`.

Example:

```json
{"id":"BUG-123","classification":"escaped_regression","severity":"high","summary":"A release gap escaped review."}
```

Useful classifications:

- `caught_regression`, `caught_by_review`, `caught_by_tests`
- `escaped_regression`, `missed_regression`, `process_miss`
- `false_positive`, `false_alarm`
