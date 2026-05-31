# Agent Skills Integration

This framework maps the lifecycle vocabulary from
`https://github.com/addyosmani/agent-skills` into a reusable autonomous SDLC team
model.

## Integration Decision

The upstream project is a general workflow taxonomy. This repo turns those ideas
into local role prompts, memory rules, deterministic reports, reliability
scoring, and release gates.

The strongest combined model is:

- use the upstream skill taxonomy as the engineering vocabulary
- use this repo's role prompts and reports as the execution layer
- keep the framework product-agnostic so adopting teams supply their own code
  and domain checks
- validate the mapping so role and artifact drift is caught

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
