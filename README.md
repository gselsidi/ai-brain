# Autonomous SDLC Team Framework

Reusable, LLM-provider-neutral framework for an autonomous full-stack SDLC team.
It can be run from Codex, adapted for Claude, or wired into another agent
runtime that can read the instructions and execute the local checks.

This repo contains the team methodology: specialist role prompts, durable
memory, planning checkpoints, improvement hardening, requirements audit,
self-healing, maintenance, reliability scoring, and release evidence.

It has no default product runtime and no required model vendor. Bring your own
codebase, product surface, tests, domain rules, and provider/runtime adapter;
use this framework to run the delivery loop.

## What Is Here

- `AGENTS.md`: project-wide operating protocol and definition of done.
- `.codex/agents/`: specialist role prompts for the autonomous SDLC team. These
  files are Codex-shaped in this checkout, but the role text and SDLC gates are
  provider-neutral and can be ported to Claude or another agent runtime.
- `contracts/team_framework.yaml`: machine-readable framework contract.
- `contracts/agentic_framework_map.yaml`: lifecycle skill map.
- `contracts/expected_behavior.md`: human-readable behavior contract.
- `memory/PROJECT_MEMORY.template.md`: safe template for local durable memory.
- `state/sdlc_state.template.json`: safe template for local lifecycle state.
- `tools/`: deterministic validation, reliability, release, and report tooling.
- `tests/`: framework regression tests with source-backed reporting.
- `docs/`: adoption and operation guide.
- `docs/how_this_was_built.md`: sanitized build history for people curious
  about how the framework came together.
- `specs/prompt_spec_template.md`: durable spec template for project-work
  prompts.

## Prompt Specs

For broad or ambiguous work, start with `/goal`. It clarifies outcome, success
criteria, non-goals, constraints, assumptions, and open questions before the
spec is written.

If the active provider supports a native `/goal` or planning feature, AI Brain
can use it to clarify the work. But that does not replace AI Brain's SDLC loop.
After `/goal`, the work still goes through the durable spec, memory, checks,
evidence, audits, and release gates. If native `/goal` is unavailable, disabled,
or incompatible, AI Brain does the same clarification step itself.

For example, a Claude-based setup can load the same operating instructions,
role prompts, specs, memory rules, and Make targets, then use Claude's own
planning features where available. The important contract is still the AI Brain
loop and evidence, not the provider name.

For every project-work prompt that changes artifacts, the framework creates or
updates a local durable spec under `specs/` before implementation starts. The
`delivery_planner` breaks the prompt into requirements, small chunks, owners,
affected artifacts, and verification commands; the `sdlc_orchestrator`
implements from that spec and audits completion against it.

This public repo intentionally tracks only `specs/prompt_spec_template.md`.
Adopter-specific prompt specs are ignored by git so teams can drop the framework
into their own work without inheriting this repo's build notes.

## Generated Outputs

- `site/`: generated MkDocs static site output. It is built from `docs/` and
  `mkdocs.yml`, ignored by git, safe to delete locally, and recreated by
  `make docs` or `mkdocs build --strict --clean`.
- `state/reports/`: generated evidence reports from the framework gates. The
  source of truth is the contracts, tools, tests, docs, memory, and role
  prompts that produce these reports.
- `memory/PROJECT_MEMORY.md` and `state/sdlc_state.json`: local workspace files
  copied from the templates when needed. They are ignored by git so private
  memory, run status, and adoption details are not published.

## Quick Start

```bash
./scripts/build_and_launch.sh
```

Open:

- Knowledge Base: <http://localhost:8001>
- Combined Report: `state/reports/combined_report.html`

The script creates or updates `.venv`, installs development dependencies, runs
the full local framework evidence loop, then launches the searchable MkDocs
knowledge base. Stop it with `Ctrl-C`.

If the default knowledge-base port is busy:

```bash
KB_PORT=8012 ./scripts/build_and_launch.sh
```

## Useful Commands

```bash
make setup
make build-all
make test
make lint
make framework-check
make framework-drift
make improvement-queue
make harness-check
make team-reliability
make release-gate
make report-html
make maintenance-daily
```

`make improvement-queue` writes a Desloppify-inspired strict score and ranked
next-item queue for harness maintainability debt. `make report-html` combines
JSON evidence under `state/reports/` into `state/reports/combined_report.html`.

## Adoption

To apply this methodology to another team:

1. Copy or reference `AGENTS.md`, `.codex/agents/`, and the docs that describe
   the lifecycle. If your provider is not Codex, translate the `.codex/agents/`
   role prompts into that provider's agent, project-instruction, or subagent
   format.
2. Replace `contracts/expected_behavior.md` with the adopting team's product
   behavior contract.
3. Keep `specs/prompt_spec_template.md` or replace it with the team's stricter
   spec template. Local dated specs created during work are ignored by default.
4. Add target-specific tests and commands to that team's Makefile or CI.
5. Copy `memory/PROJECT_MEMORY.template.md` to local
   `memory/PROJECT_MEMORY.md` when you want durable workspace context.
6. Use provider-native `/goal` or planning when available, then continue through
   the AI Brain spec, plan, harden, audit, self-heal, and release gates. With
   Claude, that means Claude can help clarify the goal, but the AI Brain
   evidence loop still decides whether the work is actually done.

The framework supplies the autonomous SDLC team. The adopting team supplies the
product.

## License

MIT. Use it, fork it, adapt it, and improve it.
