# Autonomous SDLC Team Framework

Drop this repo into a codebase, point your agent at `AGENTS.md`, and start using
the SDLC loop right away. It gives an LLM an autonomous full-stack SDLC team
harness: role prompts, prompt specs, local memory templates, deterministic
checks, evidence reports, and release gates.

It is LLM-provider-neutral. The checked-in agent files are Codex-shaped, but
the workflow can be adapted for Claude or any runtime that can read project
instructions and run shell commands.

This repo contains the team methodology: specialist role prompts, durable
memory, planning checkpoints, improvement hardening, requirements audit,
self-healing, maintenance, reliability scoring, and release evidence.

It has no default product runtime and no required model vendor. Bring your own
codebase, product surface, tests, domain rules, and provider/runtime adapter;
use this framework to run the delivery loop.

## Drop-In Adoption

1. Copy this framework into your project, or keep it as a harness repo next to
   the project you want it to run.
2. Tell your coding agent to read `AGENTS.md` before doing project work.
3. Keep `specs/prompt_spec_template.md`; local prompt specs created during work
   are ignored by default.
4. Copy `memory/PROJECT_MEMORY.template.md` to `memory/PROJECT_MEMORY.md` only
   if you want local durable memory.
5. Run the local checks:

```bash
./scripts/build_and_launch.sh
```

That command creates or updates `.venv`, installs development dependencies,
runs the framework evidence loop, and opens the local docs at
<http://localhost:8001>.

If the default docs port is busy:

```bash
KB_PORT=8012 ./scripts/build_and_launch.sh
```

## Core Files

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

## Checks

```bash
make setup
make build-all
make test
make lint
make framework-check
make framework-drift
make improvement-queue
make conversation-feedback
make harness-check
make team-reliability
make release-gate
make report-html
make maintenance-daily
```

The main release check is:

```bash
make release-gate
```

Generated outputs stay local:

- `site/`
- `state/reports/`
- `memory/PROJECT_MEMORY.md`
- `state/sdlc_state.json`

Those paths are ignored by git so private memory, run status, and evidence logs
do not get published by accident.

`make conversation-feedback` is optional and local. It scans Codex session files
only when they mention the configured project root, strips repeated boilerplate,
redacts common secret patterns, and writes ignored feedback reports under
`state/reports/`. `make maintenance-daily` runs the cadence-aware version so a
deployed project can learn from its own recurring friction without reading every
chat on the computer.

## Adapting It

For a real product repo, usually you only need to adjust these pieces:

- Replace `contracts/expected_behavior.md` with your product behavior contract.
- Add your product's test, lint, build, and deploy commands to `Makefile` or CI.
- Translate `.codex/agents/` into your provider's agent format if you are not
  using Codex.
- Keep provider-native `/goal` or planning as input only; the AI Brain spec,
  audit, self-heal, and release gates still decide whether work is done.

The framework supplies the autonomous SDLC team. The adopting team supplies the
product.

## License

MIT. Use it, fork it, adapt it, and improve it.
