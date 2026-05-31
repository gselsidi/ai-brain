# Codex Maintenance Prompt

Use `AGENTS.md`, `memory/PROJECT_MEMORY.md`, and `docs/agent_plumbing.md`.

Act as `maintenance_heartbeat` under the `sdlc_orchestrator`.

Goal:
Run the autonomous SDLC team maintenance loop, interpret failures, repair the
smallest safe slice, and leave auditable evidence.

Steps:

1. Recover context from `AGENTS.md` and `memory/PROJECT_MEMORY.md`.
2. Run:

   ```bash
   PATH=".venv/bin:$PATH" make maintenance-daily
   ```

3. If maintenance passes, summarize the report paths and stop.
4. If maintenance fails:
   - inspect the failing command output and `state/reports/`
   - identify the owning role, such as `dev_test_writer`, `docs_drift_guard`,
     `evidence_judge`, `implementation_hardener`, or `self_healer`
   - repair the smallest root cause
   - add or update regression evidence
   - rerun the failed gate and then rerun release evidence
5. Update `memory/PROJECT_MEMORY.md`, `state/sdlc_state.json`, and
   `state/reports/requirements_audit_report.json` when durable project state
   changes.

Constraints:

- Do not store secrets in files or logs.
- Do not add a default product runtime to this framework repo.
- Do not make broad rewrites unrelated to the failure.
- Do not mark the project complete unless deterministic gates pass.
- If the failure cannot be repaired safely in CI, write a clear blocker report
  under `state/reports/`.
