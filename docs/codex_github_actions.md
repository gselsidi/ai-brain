# Codex In GitHub Actions

This repo keeps normal scheduled maintenance deterministic:

```text
GitHub schedule
  -> make maintenance-daily
  -> lint, tests, framework drift, harness quality, reliability, release gate
```

That workflow does not wake a live Codex reasoning agent. It runs shell commands
and fails or passes like normal CI.

The placeholder workflow at
`.github/workflows/codex-agent-maintenance-placeholder.yml` shows how this repo
would bridge GitHub Actions to Codex when a team wants CI to run an actual Codex
agent.

## Why It Is A Placeholder

Running Codex from GitHub Actions requires credentials and consumes tokens. The
placeholder is intentionally manual and gated:

1. Add `OPENAI_API_KEY` as a GitHub Actions secret.
2. Set repository variable `ENABLE_CODEX_ACTION=true`.
3. Manually run the workflow.
4. Type `RUN_CODEX` into the `run_codex` input.

If any of those are missing, the workflow prints an explanation and exits
without calling Codex.

## What The Placeholder Would Do

When enabled, the workflow:

1. checks out the repository
2. installs development dependencies
3. runs `openai/codex-action@v1`
4. passes `.github/prompts/codex-maintenance.md` as the prompt
5. lets Codex run under `workspace-write`
6. writes the final Codex message to
   `state/reports/codex-maintenance-final.md`
7. uploads Codex output and generated reports as workflow artifacts

## Safety Notes

- Keep the workflow manual until the security model is reviewed.
- Prefer `read-only` for review-only use cases.
- Use `workspace-write` only when Codex is allowed to edit files.
- Do not expose secrets to untrusted pull request workflows.
- Keep branch protections and human review in front of merged repairs.
