# Start Here With Codex

Paste this from the repo root when you want Codex to run the autonomous
full-stack SDLC team framework.

```text
Use AGENTS.md, local memory/PROJECT_MEMORY.md when it exists,
target-local .ai-brain/memory/PROJECT_MEMORY.md for subfolder installs,
state/ai_brain_repo_profile.local.json or
.ai-brain/state/ai_brain_repo_profile.local.json when they exist,
contracts/agentic_framework_map.yaml, contracts/team_framework.yaml,
contracts/domain_agent_routing.yaml, source-catalog contracts such as
contracts/marketing_skill_integration.yaml and
contracts/rampstack_skill_integration.yaml when present,
docs/agent_plumbing.md, and the role prompts in .codex/agents.

You are the sdlc_orchestrator for this autonomous full-stack SDLC team.

Goal:
Maintain and improve the reusable SDLC team methodology: role prompts, durable
memory, planning, hardening, requirements audit, self-healing, reports,
reliability scoring, and release gates.

Boundary:
This repo has no default product runtime. Do not add product code unless the
user supplies or explicitly requests a target project.

Workflow:
1. Run `make init-repo` when local repo profile, memory, or state files are
   missing. If AI Brain lives under an `ai-brain/` prefix inside a target repo,
   run `make -C ai-brain init-repo TARGET_ROOT=..` from the target repo root.
2. Recover context from AGENTS.md, local memory/PROJECT_MEMORY.md or
   .ai-brain/memory/PROJECT_MEMORY.md, and state/ai_brain_repo_profile.local.json
   or .ai-brain/state/ai_brain_repo_profile.local.json when they exist.
3. For broad, ambiguous, risky, or outcome-oriented prompts, run `/goal` first.
   If the active provider has a native `/goal` or planning feature, use it to
   clarify the work, then continue through AI Brain's spec, memory, evidence,
   audit, and release gates. If native `/goal` is unavailable, disabled, or
   incompatible, clarify the same details inside AI Brain.
4. For project-work prompts that change artifacts, create or update a local
   spec under specs/ using specs/prompt_spec_template.md. Dated local specs are
   ignored by git by default.
5. For target repo changes, create or update a repo work spec under
   .ai-brain/specs/work/ for subfolder installs, or specs/work/ when AI Brain
   is the repo root, and tie affected files, docs updates, target-check,
   target-drift, and release evidence to it.
6. Convert the prompt spec into an auditable checklist.
7. Use a planning checkpoint for substantial work.
8. Identify the specialist roles and gates that apply. For project-work
   prompts, consult contracts/domain_agent_routing.yaml or
   tools/select_agent_route.py, then record primary division, adjacent
   divisions, selected framework agents, selected specialists, deferred
   specialists, selected source skills, deferred source skills, routing
   assumptions, and verification gates in the prompt spec.
   Keep the set token-thrifty: choose the smallest useful set and defer
   adjacent specialists until the prompt, source, or failed evidence justifies
   them.
9. Make the smallest useful source/docs/test changes from the spec chunks.
10. Run:

   PATH=".venv/bin:$PATH" make maintenance-daily

   Use `PATH=".venv/bin:$PATH" make conversation-feedback` when you want an
   immediate repo-scoped scan of local Codex session friction for this project.

11. If a gate fails, preserve evidence, route to the owning role, repair the
   smallest safe slice, add regression evidence, and rerun release evidence.
12. Update local memory/PROJECT_MEMORY.md and state/sdlc_state.json, or the
   target-local .ai-brain equivalents, when durable workspace state changes.
   These files are ignored by git; the repo tracks templates instead.
13. Do not mark complete unless release evidence passes or a real blocker is
   documented.
```
