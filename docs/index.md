# Autonomous Full-Stack SDLC Team

This knowledge base explains the reusable autonomous SDLC team framework.

The framework provides role prompts, durable memory, planning, hardening,
self-healing, requirements audit, maintenance, reliability scoring, and release
evidence. It does not include a built-in product runtime.

Use Git subtree when you want AI Brain to live as normal files inside another
repo while still being able to pull upstream updates:

```bash
git subtree add --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
git subtree pull --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
```

Do not commit a plain nested checkout that still contains `ai-brain/.git`; use a
subtree, an intentional submodule, or a clean exported bundle instead. For
one-off vendoring, run `make dropin-bundle` from an AI Brain checkout and copy
`dist/ai-brain-dropin/` into the target repo.

If you already manually copied a live AI Brain folder into a target repo, run
`make -C ai-brain manual-copy-clean` before `git add ai-brain`. It removes the
nested `.git` and local generated artifacts only when the folder is inside a
parent Git repo.

Run `make init-repo` after adding AI Brain to a codebase. If AI Brain lives in
an `ai-brain/` subfolder, run `make -C ai-brain init-repo TARGET_ROOT=..`. The
initializer detects target repo metadata and writes ignored target-local memory,
state, repo-profile, work-spec, and report files under `.ai-brain/`. It also
updates target `.gitignore` for `.ai-brain/` and creates or updates the target
repo root `AGENTS.md` with an AI Brain AGENTS.md bridge so future Codex sessions
know to read `ai-brain/AGENTS.md` before repo work. Use
`INSTALL_ROOT_AGENTS=0` for private local-only installs that should not add a
root bridge.

Target repo checks are first-class. `make target-check` runs safe detected repo
commands and `make target-drift` checks repo-profile and work-spec evidence.

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

Bring your target codebase. AI Brain initializes local context from the checkout
instead of asking you to copy memory templates or replace generic contracts by
hand.

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
- `contracts/domain_agent_routing.yaml`
- `contracts/marketing_skill_integration.yaml`
- `contracts/rampstack_skill_integration.yaml`
- `contracts/expected_behavior.md`
- `memory/PROJECT_MEMORY.template.md`
- `memory/PROJECT_MEMORY.md`
- `state/sdlc_state.template.json`
- `state/ai_brain_repo_profile.local.json`
- `state/reports/target-command_report.json`
- `state/reports/target-drift_report.json`
- `state/reports/improvement-queue_report.json`
- `state/reports/conversation-feedback_report.json`
