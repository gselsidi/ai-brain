# AI Brain Orchestrator Harness

## Start Here: Add AI Brain To Another Repo

Most people should not copy a live cloned AI Brain folder into another repo.
That can bring along `ai-brain/.git`, and the target repo will not commit the
framework files the way you expect.

First decide whether AI Brain should be committed to the target repo.

If AI Brain is only a local helper for you or your agent, do not commit it. Add
this to the target repo's `.gitignore`:

```gitignore
ai-brain/
```

Then keep using the local folder without staging it.

If the target repo should include AI Brain for the whole team, use one of the
commit-safe paths below.

For ongoing updates from the AI Brain repo, use Git subtree from the target repo
root:

```bash
git subtree add --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
```

For a manual copy, copy a clean artifact that already has no `.git`: GitHub's
downloaded ZIP, a release archive, or `dist/ai-brain-dropin/` produced by
`make dropin-bundle`. Then commit it normally:

```bash
git add ai-brain
git commit -m "Add AI Brain framework"
```

If you already copied a live checkout by mistake, clean it before staging:

```bash
make -C ai-brain manual-copy-clean
git add ai-brain
git commit -m "Add AI Brain framework"
```

After AI Brain is added under `ai-brain/`, initialize it against the target repo:

```bash
make -C ai-brain setup
make -C ai-brain init-repo TARGET_ROOT=..
```

That init command creates sticky target-local AI Brain data under `.ai-brain/`
at the target repo root:

- `.ai-brain/memory/PROJECT_MEMORY.md`
- `.ai-brain/state/sdlc_state.json`
- `.ai-brain/state/ai_brain_repo_profile.local.json`
- `.ai-brain/specs/work/`
- `.ai-brain/state/reports/`

It also creates or updates the target repo `.gitignore` so `.ai-brain/` stays
local by default. This makes `ai-brain/` replaceable framework code: you can
copy/paste or subtree-pull a new version of AI Brain over `ai-brain/` without
deleting the target repo's memory, specs, state, or evidence.

The init command also creates or updates the target repo root `AGENTS.md` with
an AI Brain bridge. This bridge is what tells future Codex sessions to read
`ai-brain/AGENTS.md` before doing repo work and to read sticky local context
from `.ai-brain/`. Existing root `AGENTS.md` content is preserved outside a
managed block. For a private local-only AI Brain helper, disable the bridge:

```bash
make -C ai-brain init-repo TARGET_ROOT=.. INSTALL_ROOT_AGENTS=0
```

After creating or updating the root bridge, start a new Codex session from the
target repo root or explicitly ask Codex to reread root `AGENTS.md`; a session
that started before the bridge existed may not reload it automatically.

For manual AI Brain updates, replace or overlay only `ai-brain/`. Do not delete
`.ai-brain/` unless you intentionally want to erase the target repo's local
memory, work specs, state, and reports.

AI Brain requires Python 3.11+. On macOS, `/usr/bin/python3` may still be
Python 3.9. The Makefile automatically prefers `ai-brain/.venv/bin/python` when
it exists, then looks for `python3.12`, `python3.13`, or `python3.11`. If only an
old system Python is available, install a newer Python and rerun `make -C
ai-brain setup`.

AI Brain is a reusable agent orchestration harness. Drop it into a codebase,
point your coding agent at `AGENTS.md`, and it gives the agent a disciplined
way to read a prompt, classify the work, choose the right roles and source-skill
lenses, preserve memory, run deterministic evidence, and decide when the slice
is actually done.

The original center of gravity is an autonomous full-stack SDLC team, and that
still matters. The broader purpose is now larger: AI Brain is a
provider-neutral orchestrator for agentic work. The SDLC lifecycle is one
execution loop inside the harness, not the whole identity.

It has no default product runtime and no required model vendor. Bring your own
codebase, product surface, tests, domain rules, credentials, and
provider/runtime adapter. AI Brain supplies the orchestration method:
prompt-to-agent routing, source-skill catalogs, durable specs, local memory,
target-repo checks, hardening loops, reliability scoring, and release evidence.

## What It Does

AI Brain helps an agent answer four practical questions before it spends tokens:

- What kind of work is this prompt asking for?
- Which division, framework roles, and specialists are actually needed?
- Which source skills add useful context, and which should stay deferred?
- What evidence proves the work is complete?

The orchestrator starts small. It can route a programming task into engineering,
a marketing task into SEO/copy/CRO/analytics, a sales task into RevOps or
enablement, or a product task into requirements and roadmap work. It records
plausible adjacent agents and source skills as deferred options instead of
loading a whole folder of prompts up front.

## Core Capabilities

- **Prompt-to-agent routing:** `tools/select_agent_route.py` reads the prompt
  and returns a primary division, adjacent divisions, selected framework agents,
  selected specialists, deferred specialists, selected source skills, deferred
  source skills, and verification gates.
- **Token-thrifty source skills:** source catalogs are metadata-only. The
  router uses slugs, categories, summaries, and trigger terms to pick a few
  useful lenses without loading every skill body.
- **Durable Prompt Specs:** every project-work prompt that changes artifacts
  gets a local spec under `specs/` before implementation starts. Target repo
  work specs live under `.ai-brain/specs/work/` for subfolder installs.
- **Target repo adapter:** `make init-repo` detects the product checkout,
  writes ignored local memory/state/profile files under target `.ai-brain/`,
  and lets AI Brain run target repo checks without turning AI Brain into the
  product.
- **Evidence-first execution:** tests, lint, target commands, drift checks,
  harness quality, improvement queue, reliability score, and release gate turn
  agent work into auditable evidence.
- **SDLC lifecycle mode:** for software delivery, the harness runs the full
  requirements -> `/goal` -> spec -> plan -> build -> verify -> review -> ship
  loop with specialist roles.

## Source Skill Catalogs

AI Brain uses external skill repos as source-backed routing catalogs. It does
not vendor upstream skill bodies or reference files.

| Catalog | Contract | Count | Purpose |
| --- | --- | --- | --- |
| RampStack Claude Skills | `contracts/rampstack_skill_integration.yaml` | 103 | Broad web-lifecycle lenses for brand, content, SEO, product, growth, design, research, operations, and delivery work. |
| Corey Haines Marketing Skills + Direct Response Copy gist | `contracts/marketing_skill_integration.yaml` | 45 | Focused marketing lenses for CRO, copywriting, direct-response copy, SEO, analytics, growth engineering, GTM, sales, RevOps, retention, and monetization. |

Each source skill is classified as:

- `merge_existing`: AI Brain already has a close lifecycle lane or specialist.
- `add_catalog_lens`: the skill adds a useful optional domain lens.
- `tool_dependent_lens`: the skill needs adopter-provided URLs, accounts,
  credentials, analytics/ad data, CRM data, market data, MCPs, or web research
  before execution.

Overlapping slugs across catalogs represent the same concept and are deduped by
the selector.

## Marketing Skill Coverage

The Marketing Skills catalog adds sharper marketing routing. Current groups:

| Group | Skills |
| --- | --- |
| Marketing foundation | `product-marketing`, `customer-research`, `marketing-plan`, `marketing-ideas`, `marketing-psychology` |
| Conversion optimization | `cro`, `signup`, `onboarding`, `popups`, `paywalls`, `ab-testing` |
| Content and copy | `copywriting`, `direct-response-copy`, `copy-editing`, `cold-email`, `emails`, `social`, `image`, `video`, `sms` |
| SEO and discovery | `seo-audit`, `ai-seo`, `programmatic-seo`, `site-architecture`, `schema`, `content-strategy`, `competitors`, `competitor-profiling`, `aso`, `directory-submissions` |
| Paid and measurement | `ads`, `ad-creative`, `analytics` |
| Growth and retention | `churn-prevention`, `co-marketing`, `community-marketing`, `free-tools`, `referrals`, `lead-magnets` |
| GTM, sales, and RevOps | `launch`, `pricing`, `revops`, `sales-enablement`, `prospecting`, `public-relations` |

Examples:

```bash
python tools/select_agent_route.py --prompt "Set up GA4 tracking for paid ads and write cold outreach emails"
python tools/select_agent_route.py --prompt "Plan programmatic SEO pages at scale with schema markup"
python tools/select_agent_route.py --prompt "Create a launch plan with pricing, sales enablement, and RevOps lead routing"
```

## Token-Thrifty Routing

The default routing caps are intentionally conservative:

| Cap | Default | Meaning |
| --- | ---: | --- |
| `max_primary_specialists` | 3 | Select up to three specialists from the primary division. |
| `max_adjacent_specialists` | 2 | Select up to two specialists from one adjacent division. |
| `max_adjacent_divisions` | 1 | Usually branch into only one nearby division. |
| `max_source_skills` | 4 | Select up to four source-catalog skills. |
| `max_deferred_source_skills` | 8 | Record up to eight plausible source skills as deferred. |

Selected means the orchestrator should use the role or lens now. Deferred means
AI Brain records it as a likely next helper without loading or running it yet.
That is the main guard against burning tokens on agents that are only
tangentially related.

## Drop-In Adoption

Recommended ongoing-update path: add AI Brain as a Git subtree. From the target
repo root:

```bash
git subtree add --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
```

Later updates use the same prefix:

```bash
git subtree pull --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
```

Subtree keeps `ai-brain/` as normal files in the target repo, so ordinary
clones, deploys, and commits see the framework without submodule setup. Do not
copy a live AI Brain checkout with its nested `.git` directory into another repo
and commit it; the outer repo will not store those files in the way you expect.

If you already manually copied the live folder into a target repo, clean it
before staging:

```bash
make -C ai-brain manual-copy-clean
git add ai-brain
git commit -m "Add AI Brain framework"
```

The cleanup command removes nested AI Brain Git metadata and local generated
artifacts only when `ai-brain/` is inside another Git repo. It refuses to run
against the standalone AI Brain source checkout.

For one-off vendoring without an upstream update path, export a clean bundle:

```bash
make dropin-bundle
```

That writes `dist/ai-brain-dropin/` without `.git`, virtualenvs, caches, local
memory, local state, generated reports, or dated local specs. Copy that exported
folder into the target repo when you want plain committed files.

After AI Brain is in the target repo, run the initializer. If AI Brain is the
repo root:

```bash
make init-repo
```

If AI Brain lives in an `ai-brain/` subfolder:

```bash
make -C ai-brain init-repo TARGET_ROOT=..
```

That inspects the checkout and creates ignored local files:

- `.ai-brain/memory/PROJECT_MEMORY.md`
- `.ai-brain/state/sdlc_state.json`
- `.ai-brain/state/ai_brain_repo_profile.local.json`
- `.ai-brain/specs/work/`
- `.ai-brain/state/reports/`

Tell your coding agent to read `AGENTS.md` before doing project work. Then run
the local checks and knowledge base:

```bash
./scripts/build_and_launch.sh
```

That command creates or updates `.venv`, installs development dependencies,
runs `make init-repo`, runs the framework evidence loop, and opens the local
docs at <http://localhost:8001>.

If the default docs port is busy:

```bash
KB_PORT=8012 ./scripts/build_and_launch.sh
```

## Prompt Specs And `/goal`

For broad or ambiguous work, start with `/goal`. It clarifies outcome, success
criteria, non-goals, constraints, assumptions, and open questions before the
spec is written.

If the active provider supports a native `/goal` or planning feature, AI Brain
can use it to clarify the work. But provider-native planning does not replace
AI Brain's spec, memory, evidence, audit, or release gates. If provider-native
`/goal` is unavailable, disabled, or incompatible, AI Brain performs the same
clarification inside the harness.

For every project-work prompt that changes artifacts, the framework creates or
updates a local durable spec under `specs/` before implementation starts. The
spec records the prompt, clarified goal, requirements checklist, routing
decision, owners, implementation chunks, affected artifacts, and verification
commands.

When AI Brain is operating on a target repo, target work evidence belongs in
repo work specs under `specs/work/`. Those specs are the repo's delivery ledger:
prompt, goal, affected files, target commands, docs updates, reports, and
completion audit.

This public repo intentionally tracks only `specs/prompt_spec_template.md`.
Adopter-specific prompt and work specs are ignored here by default.

## SDLC Lifecycle Mode

For implementation work, AI Brain can run the full Agentic SDLC loop:

```text
requirements intake -> /goal -> prompt spec -> planning checkpoint -> interface contract -> build
-> dev tests -> quality exploration -> adversarial review
-> implementation hardening -> evidence judge -> security review
-> docs drift check -> requirements audit -> self-healing repair
-> regression -> PR review -> release gate -> scheduled maintenance
```

That loop is strongest for software delivery, automation, docs, tests, and team
workflow changes. For narrower strategy, marketing, research, or support work,
the same harness can still route the prompt, select lenses, preserve evidence,
and avoid unnecessary fan-out.

## Core Files

- `AGENTS.md`: project-wide operating protocol and definition of done.
- `.codex/agents/`: specialist role prompts for the autonomous full-stack SDLC
  team. The files are Codex-shaped in this checkout, but the role text and
  gates are provider-neutral.
- `contracts/domain_agent_routing.yaml`: prompt-to-agent routing contract for
  primary divisions, adjacent divisions, specialists, source catalogs, deferred
  work, and evidence gates.
- `contracts/marketing_skill_integration.yaml`: metadata-only mapping of Corey
  Haines' 44 Marketing Skills plus one supplemental Direct Response Copy gist
  lens.
- `contracts/rampstack_skill_integration.yaml`: metadata-only mapping of
  RampStack's 103-skill catalog.
- `contracts/team_framework.yaml`: machine-readable framework contract.
- `contracts/agentic_framework_map.yaml`: lifecycle and unique-capability map.
- `contracts/expected_behavior.md`: human-readable AI Brain behavior contract.
- `specs/prompt_spec_template.md`: durable spec template for project-work
  prompts.
- `memory/PROJECT_MEMORY.template.md`: safe template for local durable memory.
- `.ai-brain/memory/PROJECT_MEMORY.md`: ignored target-local memory generated
  and updated by `make -C ai-brain init-repo TARGET_ROOT=..` and the
  orchestration loop.
- `state/sdlc_state.template.json`: safe template for local lifecycle state.
- `.ai-brain/state/ai_brain_repo_profile.local.json`: ignored target-local repo
  profile generated from package metadata, source markers, git metadata, and
  common commands.
- `.ai-brain/specs/work/*.md`: repo-level work specs for target-repo changes.
- `tools/`: deterministic validation, routing, reliability, release, and report
  tooling.
- `tests/`: framework regression tests with source-backed reporting.
- `docs/`: adoption and operation guide.
- `docs/how_this_was_built.md`: sanitized build history and public-source
  hygiene notes.

## Checks

```bash
make setup
make init-repo
make build-all
make test
make lint
make framework-check
make framework-drift
make target-check
make target-drift
make target-release
python tools/select_agent_route.py --prompt "Fix the checkout API bug and add tests"
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
- `.ai-brain/` in target repo installs
- `state/reports/` when AI Brain itself is the repo root
- `state/ai_brain_repo_profile.local.json` when AI Brain itself is the repo root
- `specs/work/*.md` when AI Brain itself is the repo root
- `memory/PROJECT_MEMORY.md` when AI Brain itself is the repo root
- `state/sdlc_state.json` when AI Brain itself is the repo root

Those paths are ignored by git so private memory, run status, and evidence logs
do not get published by accident.

`make conversation-feedback` is optional and local. It scans Codex session files
only when they mention the configured project root, strips repeated boilerplate,
redacts common secret patterns, and writes ignored feedback reports under
`state/reports/`. `make maintenance-daily` runs the cadence-aware version so a
deployed project can learn from its own recurring friction without reading every
chat on the computer.

## Repo Initialization

You should not need to manually copy the memory template, replace the tracked
contracts, or hand-edit this Makefile just to start. `make init-repo` discovers
the target repo and writes the local files AI Brain needs.

It looks for common project signals such as `package.json`, `pyproject.toml`,
`Cargo.toml`, `go.mod`, source folders, tests, git branch, and git remote. It
then records detected test, lint, build, typecheck, dev, start, and deploy
commands where it can find them.

Contracts describe AI Brain itself: routing, roles, source catalogs, gates,
memory rules, prompt specs, checks, and release behavior. They are not
populated from the product repo. Product-repo facts live in local memory, local
state, the repo profile, and the current repo work spec. `make target-check`
runs detected repo commands such as test, lint, typecheck, check, and build.
`make target-drift` checks that the repo profile and active work spec still
match the checkout.

The framework supplies the orchestrator harness and autonomous SDLC team. The
adopting team supplies the product.

## License

MIT. Use it, fork it, adapt it, and improve it.
