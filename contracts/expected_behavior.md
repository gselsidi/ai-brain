# Expected Behavior Contract

This contract describes the reusable autonomous full-stack SDLC team framework.
It has no default product runtime and does not ship a default application
surface.
Adopting teams bring their own codebase. `make init-repo` inspects that checkout
and writes ignored local memory, lifecycle state, repo-profile facts, specs,
and evidence at the target repo root. For subfolder installs, those
target-local artifacts live outside `ai-brain/` so the embedded framework
folder remains replaceable. This repo provides the generic team operating model
and evidence loop.

## Mission

The framework should help a team run repeatable autonomous delivery:

- recover context from durable memory
- initialize local repo context with `make init-repo`
- keep target-local memory, state, specs, and evidence outside replaceable
  `ai-brain/` framework code for subfolder installs
- install a target repo root `AGENTS.md` bridge for subfolder installs so Codex
  discovers `ai-brain/AGENTS.md` on future repo work
- prefer an existing AI Brain virtualenv for Makefile commands and fail with a
  clear Python-version message when only an unsupported system Python is
  available
- support safe vendoring through Git subtree, a guarded manual-copy cleanup, or
  a clean exported bundle instead of plain nested `.git` checkouts
- prefer provider-native `/goal` or planning input when the active runtime
  supports it, otherwise clarify inside AI Brain, then always continue through
  AI Brain's SDLC loop
- clarify broad or ambiguous work with `/goal` before the prompt spec
- read each project-work prompt as a routing signal, select a primary division,
  choose core SDLC roles, and add adjacent specialists only when justified
- treat routed roles as review lenses while requiring a separate delegation
  decision for substantial work
- when a safe independent workstream exists, start at least one and at most
  four bounded children without inherited conversation
  and give it a compact task packet instead of making it repeat AI Brain
  bootstrap, memory, routing, specs, or lifecycle work
- convert project-work prompts into durable prompt specs with auditable
  requirements
- keep target repo work specs under target-root `specs/work/`
- plan small implementation slices
- define product or handoff interfaces before broad changes
- build incrementally
- write and run regression evidence
- run target repo commands and target drift checks from the local repo profile
- harden weak implementations
- run a deterministic improvement queue with a strict score and ranked next
  items for maintainability debt
- review security, docs, and release risk
- audit requirements back to artifacts
- self-heal failed gates
- maintain reliability over time
- use an architect-engineer execution loop: compact tool work and concise final
  explainers, expanding only for user-requested, safety, audit, or release need

## Core Artifacts

- `AGENTS.md`: operating instructions for the main orchestrator.
- `.codex/agents/*.toml`: specialist role prompts for the autonomous SDLC team.
- `contracts/agentic_framework_map.yaml`: mapping from general lifecycle skills
  to local roles, artifacts, and gates.
- `contracts/domain_agent_routing.yaml`: division-first prompt-to-agent routing
  contract for mapping prompt signals to framework agents, specialist lenses,
  deferred specialists, and verification gates.
- `contracts/rampstack_skill_integration.yaml`: metadata-only mapping from
  RampStack's 103-skill catalog into existing AI Brain lifecycle lanes or
  optional source-catalog lenses.
- `contracts/marketing_skill_integration.yaml`: metadata-only mapping from
  Corey Haines' 44 Marketing Skills plus a supplemental Direct Response Copy
  gist lens into existing AI Brain/RampStack lanes or optional marketing
  source-catalog lenses.
- `contracts/team_framework.yaml`: machine-readable framework contract.
- `memory/PROJECT_MEMORY.template.md`: tracked safe template for local durable
  context.
- `state/sdlc_state.template.json`: tracked safe template for local lifecycle
  state and report pointers.
- `memory/PROJECT_MEMORY.md` and `state/sdlc_state.json`: ignored local
  workspace files generated or updated by `make init-repo`.
- `state/ai_brain_repo_profile.local.json`: ignored machine-readable profile of
  the target checkout.
- `tools/export_dropin_bundle.py`: clean bundle exporter for one-off vendoring
  without Git internals or local generated artifacts.
- `tools/clean_manual_copy.py`: guarded cleanup for manually copied AI Brain
  folders that still contain nested Git metadata.
- `tools/check_python.py`: compatibility guard for setup, initialization, and
  evidence commands.
- `tools/install_root_agents.py`: target repo root `AGENTS.md` bridge installer
  that points Codex to nested AI Brain instructions.
- `specs/work/YYYY-MM-DD_short_slug.md`: repo-level work spec for target repo
  changes and evidence.
- `state/reports/target-command_report.json`: target repo command evidence
  generated by target checks.
- `state/reports/target-drift_report.json`: target repo profile/spec drift
  evidence.
- `/goal`: provider-aware DEFINE-phase command. It can use provider-native goal
  or planning input when available, or AI Brain's own clarification step when
  not; either way it records outcome, success criteria, non-goals, constraints,
  assumptions, open questions, and evidence expectations before the SDLC loop
  continues.
- `specs/prompt_spec_template.md`: standard structure for each project-work
  prompt spec.
- `specs/YYYY-MM-DD_short_slug.md`: durable prompt spec for a requested slice.
- `tools/select_agent_route.py`: deterministic selector that reads a prompt and
  emits the primary division, adjacent divisions, selected framework agents,
  selected specialists, deferred specialists, selected source skills, deferred
  source skills, and verification gates.
- `tools/*.py`: deterministic validators and report builders.
- `state/reports/*.json`: machine-readable evidence.
- `state/reports/improvement-queue_report.json`: Desloppify-inspired scan,
  strict score, ranked queue, and rescan evidence for the harness itself.
- `state/reports/combined_report.html`: source-backed human evidence.
- `docs/*.md`: adoption and operation guide.

## Required Lifecycle

Substantial work follows:

```text
requirements intake -> /goal -> prompt spec -> planning checkpoint -> interface contract -> build
-> dev tests -> quality exploration -> adversarial review
-> implementation hardening -> evidence judge -> security review
-> docs drift check -> requirements audit -> self-healing repair
-> regression -> PR review -> release gate -> scheduled maintenance
```

The loop may iterate. A failure report is a routing signal, not permission to
hand-wave completion.

## Role Set

The expected specialist roles are:

- `sdlc_orchestrator`
- `delivery_planner`
- `product_context_analyst`
- `interface_contract_architect`
- `dev_builder`
- `dev_test_writer`
- `quality_explorer`
- `adversarial_reviewer`
- `evidence_judge`
- `implementation_hardener`
- `security_reviewer`
- `docs_drift_guard`
- `requirements_auditor`
- `self_healer`
- `maintenance_heartbeat`
- `pr_reviewer`
- `release_gate`

## Required Bounded Subagent Execution

- The primary/root orchestrator owns AI Brain startup, routing, memory, specs,
  lifecycle evidence, and the completion decision.
- The default subagent budget is four. Selected roles and specialists remain
  lenses; role selection alone does not trigger a spawn.
- For substantial work, including controlled and release tiers, the
  orchestrator must spawn at least one child when a safe independent research,
  audit, disjoint implementation, test-matrix, adversarial-review, or
  verification workstream exists.
- If substantial work stays single-agent, the orchestrator records that no safe
  independent stream exists, delegation is unavailable or user-disabled, or
  shared mutable state makes delegation unsafe.
- Child work must be genuinely independent; child write scopes must be
  disjoint. Runtime concurrency may be lower than the four-child ceiling.
- Every child starts with `fork_turns="none"` and a compact task packet with a
  short task-specific summary. It does not inherit the parent conversation or
  repeat AI Brain bootstrap by default.
- Child agents do not run `/goal`, create specs, read project memory/profile or
  routing catalogs, generate lifecycle reports, execute release gates, or spawn
  more agents unless the task packet explicitly requires that exact work.
- The parent integrates child results, reruns deterministic verification, owns
  unsafe external/release actions, and alone declares completion.

## Execution Discipline

- Use the compact architect-engineer loop: assess, act, verify.
- Working responses contain only decision, evidence, blocker, or next action.
- Keep private reasoning private; do not narrate routine tool work.
- Batch safe independent work and use the smallest tool payload that preserves
  objective, scope, and verification.
- Use the native format of the task or tool; child handoffs stay compact:
  result, evidence, risk, next action.
- Final handoffs remain concise but include outcome, verification, and material
  risk. Expand for user-requested detail or necessary safety/audit/release work.

## Release Window Discipline

- Consecutive related follow-up corrections remain in one active release window.
- The window performs bootstrap, `/goal` clarification when needed, routing, and
  durable spec creation once; later corrections update the same spec.
- Iteration uses the narrowest relevant checks. It does not repeat full
  discovery, full suites, builds, reports, or deployment per correction.
- Full evidence, release gates, commit/push, and deployment run once when the
  user explicitly closes the window by asking to finish, commit, push, deploy,
  release, or equivalent.
- A material objective or product/security-boundary change, or a focused-check
  blocker, reopens full planning. Narrow safety checks remain immediate.

## Evidence Rules

- Every substantial change has a requirements checklist.
- `/goal` mode is documented as provider-native input or AI Brain clarification
  when the prompt is broad or ambiguous.
- Provider-native `/goal` cannot bypass or replace prompt specs, tests,
  hardening, requirements audit, or release gates.
- Broad or ambiguous work records a clarified `/goal` before the prompt spec.
- Every project-work prompt that changes artifacts has a durable spec under
  `specs/` before implementation starts.
- Prompt specs break work into small chunks with owners, affected artifacts, and
  verification commands.
- Prompt specs record division-first prompt-to-agent routing for project-work
  prompts: primary division, adjacent divisions, selected framework agents,
  selected specialists, deferred specialists, selected source skills, deferred
  source skills, routing assumptions, and verification gates.
- Routing is token-thrifty by default. Engineering/programming, marketing,
  sales, design, product, security, testing, and support are treated as
  divisions; adjacent specialists are added only when the prompt, source
  artifacts, or failed evidence justify the extra lens.
- Source skill catalogs are also token-thrifty. RampStack- and
  MarketingSkills-derived catalog entries are selected only when the prompt
  matches their lens and are deferred when plausible but not immediately needed.
  Duplicate slugs across catalogs should not activate twice. Tool-dependent
  lenses require an adopting team's credentials, MCPs, URLs, analytics/ad data,
  CRM data, market data, or web research before execution.
- Target repo changes keep an auditable repo work spec under `specs/work/`.
- Target repo commands and target drift checks run when a target repo profile
  exists.
- The improvement queue can surface non-blocking maintainability debt, but
  release decisions fail closed for blocker findings or a low strict score.
- Public behavior or team workflow changes update contracts and docs.
- Repairs include regression evidence.
- Test reports include actual test source code.
- Combined reports render source-backed evidence.
- Release decisions come from deterministic reports, not conversational claims.
- Durable state changes update local memory and `state/sdlc_state.json` when
  present; the tracked templates stay generic.

## Adoption Boundary

This framework intentionally does not include a default product implementation.
When another team adopts it, the product already lives in the target repo. AI
Brain should infer local context from that repo instead of requiring manual
replacement of generic framework files.

Default vendoring guidance is Git subtree when the target repo should contain
AI Brain as ordinary committed files while retaining an upstream update path.
For one-off vendoring, `make dropin-bundle` creates a clean copy without `.git`,
virtualenvs, caches, local memory, local state, generated reports, or local
dated specs. A Git submodule is an intentional alternative only when the target
repo should store a pointer to a separate checkout. A plain nested `.git`
directory is not a supported committed state.

If a user manually copied the live AI Brain checkout into a target repo,
`make -C ai-brain manual-copy-clean` moves non-conflicting local AI Brain
memory, state, reports, and dated specs to the target repo root, then removes
the nested AI Brain `.git` and remaining generated artifacts before staging.
Conflicts must be preserved in place instead of overwritten or deleted. The
command must refuse to remove `.git` from a standalone AI Brain source checkout
when no parent target repo is detected.

When AI Brain lives under an `ai-brain/` prefix in the target repo, initialize
local context with `make -C ai-brain init-repo TARGET_ROOT=..` so repo profiling
uses the target checkout rather than the framework subfolder.

For subfolder installs, the initializer must write target-local memory, state,
repo profile, repo work specs, and reports to target-root `memory/`, `state/`,
`specs/`, and `state/reports/`, and it must update the target repo `.gitignore`
so generated local data remains local by default. If old local data already
exists inside nested `ai-brain/memory/`, `ai-brain/state/`,
`ai-brain/specs/`, or a legacy hidden data home from older builds, init must
migrate non-conflicting memory, state, repo profiles, reports, dated prompt
specs, and repo work specs to the target repo root before writing the
refreshed profile. Any stale command or environment value that points at the
legacy hidden data home as active storage must be treated as legacy and
normalized to `TARGET_ROOT`. Updating or replacing `ai-brain/` should not
delete target-local project memory, specs, state, or evidence.

AI Brain commands require Python 3.11 or newer. The Makefile should prefer
`ai-brain/.venv/bin/python` when it exists, then compatible Python executables
such as `python3.12`, `python3.13`, or `python3.11`. If a machine only exposes
an old macOS system Python, the version check should tell the user to install a
newer Python or run with the existing AI Brain virtualenv.

A nested `ai-brain/AGENTS.md` is not enough by itself to control future Codex
work in the target repo. For subfolder installs, `make -C ai-brain init-repo
TARGET_ROOT=..` should create or update root `AGENTS.md` with a marker-delimited
AI Brain bridge that tells Codex to read `ai-brain/AGENTS.md`, local AI Brain
memory under `memory/PROJECT_MEMORY.md`, local AI Brain repo profile under
`state/ai_brain_repo_profile.local.json`, and routing contracts
before repo work. The bridge must treat every new repo prompt as an AI Brain
routing signal, require selected/deferred specialists and selected/deferred
source skills to be identified before action, and require AI Brain
specs/evidence for project-work prompts. Existing root `AGENTS.md` content must
be preserved outside the managed bridge block. Private local-only installs can
disable the bridge with
`INSTALL_ROOT_AGENTS=0`.

The tracked files under `contracts/` describe AI Brain itself: roles, gates,
memory rules, prompt specs, checks, and release behavior. They are not populated
from the product repo during normal use.

- product source code
- detectable package and source metadata
- test, lint, build, and deployment commands where the repo exposes them
- domain-specific invariant checks where the repo exposes them
- human clarification when the repo does not contain enough signal

The framework supplies the autonomous SDLC team, not the target product.
