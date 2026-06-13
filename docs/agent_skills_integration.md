# Agent Skills Integration

This framework maps the lifecycle vocabulary from
`https://github.com/addyosmani/agent-skills` into a reusable autonomous SDLC team
model.

It also maps external source skill catalogs as metadata-only routing lenses:
RampStack's `https://github.com/rampstackco/claude-skills` through
`contracts/rampstack_skill_integration.yaml`, and Corey Haines'
`https://github.com/coreyhaines31/marketingskills` through
`contracts/marketing_skill_integration.yaml`. AI Brain does not copy upstream
skill bodies; it uses source-backed slugs, categories, summaries, trigger
terms, and merge decisions to improve prompt routing while preserving token
discipline.

## Integration Decision

The upstream project is a general workflow taxonomy. This repo turns those ideas
into local role prompts, memory rules, deterministic reports, reliability
scoring, and release gates.

The strongest combined model is:

- use the upstream skill taxonomy as the engineering vocabulary
- use RampStack catalog metadata as optional domain lenses for brand, content,
  SEO, product, growth, design, research, operations, and web delivery work
- use Marketing Skills catalog metadata as optional marketing, CRO, copy, SEO,
  analytics, growth, GTM, and RevOps lenses
- use this repo's role prompts and reports as the execution layer
- keep the framework product-agnostic so adopting teams supply their own code
  and domain checks
- validate the mapping so role and artifact drift is caught

## Source Catalog Overlays

RampStack and Marketing Skills are integrated as catalog overlays, not as
always-loaded role prompts. Each source skill is classified as:

- `merge_existing`: the concept is already covered by AI Brain lifecycle roles.
- `add_catalog_lens`: the concept adds a useful optional domain lens.
- `tool_dependent_lens`: the concept is useful only when an adopting team has
  the needed external data, MCP, credentials, URLs, analytics/ad data, CRM data,
  market data, or web research.

The selector records selected and deferred source skills in prompt specs so an
orchestrator can branch into relevant lenses without burning tokens on full
catalogs. Duplicate slugs across catalogs represent the same concept and should
not activate twice.

## Combined Lifecycle

| Phase | Local owners | Required evidence |
| --- | --- | --- |
| Define | `sdlc_orchestrator`, `delivery_planner`, `product_context_analyst` | provider-native `/goal` input or AI Brain clarification, checklist, assumptions, memory |
| Plan | `delivery_planner`, `interface_contract_architect` | plan, contracts, state |
| Build | `dev_builder`, `dev_test_writer` | code/docs, tests |
| Verify | `quality_explorer`, `adversarial_reviewer`, `evidence_judge`, `self_healer` | reports and regression evidence |
| Review | `implementation_hardener`, `security_reviewer`, `docs_drift_guard`, `pr_reviewer`, `requirements_auditor` | review and audit reports |
| Ship | `release_gate`, `maintenance_heartbeat` | release PASS and combined report |
| Maintain | `maintenance_heartbeat`, `self_healer`, `docs_drift_guard` | memory, state, reliability history |

## Validation

```bash
PATH=".venv/bin:$PATH" make framework-check
```

The validator confirms:

- all upstream core skills are mapped
- every lifecycle phase has a combined rule
- local specialist agent files exist
- referenced local artifacts exist
- upstream provenance and license are recorded
