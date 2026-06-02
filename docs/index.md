# Autonomous Full-Stack SDLC Team

This knowledge base explains the reusable autonomous SDLC team framework.

The framework provides role prompts, durable memory, planning, hardening,
self-healing, requirements audit, maintenance, reliability scoring, and release
evidence. It does not include a built-in product runtime.

## Start Here

- [Agentic SDLC](agentic_sdlc.md): lifecycle loop and gates.
- [Spec-Driven Workflow](spec_driven_workflow.md): prompt specs before
  implementation, with `/goal` before `/spec` for broad work.
- [Agent Roles And Plumbing](agent_plumbing.md): how roles, reports, contracts,
  memory, state, and Make targets fit together.
- [How This Was Built](how_this_was_built.md): sanitized project history and
  public-source hygiene notes.
- [Agent Skills Integration](agent_skills_integration.md): how the external
  lifecycle taxonomy maps to this framework.
- [Improvement Mode](improvement_mode.md): bounded hardening workflow plus the
  improvement queue.
- [Maintenance](maintenance.md): recurring checks, repo-scoped conversation
  feedback, and release evidence.
- [Team Reliability](team_reliability.md): reliability score and feedback loop.
- [Memory](memory.md): durable context rules.

## Adoption

Bring your target codebase and product tests. Keep this repo focused on the
team method and evidence loop.

## Local URLs

- Knowledge Base: <http://localhost:8001>
- Combined Report: `state/reports/combined_report.html`

## Generated Output

- `site/` is the MkDocs static-site build output. It mirrors `docs/` as
  rendered HTML for local viewing or static hosting.
- `site/` is not a product runtime and is not source-of-truth documentation.
  Rebuild it with `make docs`.

## Source Artifacts

- `AGENTS.md`
- `.codex/agents/*.toml`
- `specs/prompt_spec_template.md`
- `contracts/team_framework.yaml`
- `contracts/agentic_framework_map.yaml`
- `contracts/expected_behavior.md`
- `memory/PROJECT_MEMORY.template.md`
- `state/sdlc_state.template.json`
- `state/reports/improvement-queue_report.json`
- `state/reports/conversation-feedback_report.json`
