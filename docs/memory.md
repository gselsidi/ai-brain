# Durable Project Memory

`memory/PROJECT_MEMORY.md` is the lightweight local memory system for this
repo.

The public repo tracks `memory/PROJECT_MEMORY.template.md`. Copy that template
to `memory/PROJECT_MEMORY.md` in a working checkout when you want durable local
context. The real memory file is ignored by git so workspace-specific notes,
run summaries, and adoption details do not get published.

Codex should read it after `AGENTS.md` at the start of project-work prompts
when it exists. The goal is to survive context compaction without depending on
hidden chat history.

## What Belongs There

- current framework state
- stable commands
- important files
- role and gate decisions
- durable prompt-spec workflow decisions
- durable limitations and adoption boundaries
- latest verified evidence

## What Does Not Belong There

- secrets or credentials
- large logs
- full prompt specs; store those under `specs/`
- speculative scratch notes
- private personal data

Generated reports should stay under `state/reports/`.
