# Durable Project Memory

`memory/PROJECT_MEMORY.md` is the lightweight local memory system. For target
repos that install AI Brain under `ai-brain/`, the sticky local memory file
still lives at the target repo root, outside the replaceable `ai-brain/`
framework folder.

The public repo tracks `memory/PROJECT_MEMORY.template.md` as a safe example.
Do not copy it by hand during normal adoption. Run `make init-repo`; the
initializer inspects the checkout and creates or updates the ignored local
memory file with a generated repo-profile section. For subfolder installs, run
`make -C ai-brain init-repo TARGET_ROOT=..`; that writes target-local memory,
state, specs, and reports to target-root `memory/`, `state/`, `specs/`, and
`state/reports/` so `ai-brain/` can be replaced without losing project
context. The same init command also migrates old non-conflicting local data
from nested `ai-brain/memory/`, `ai-brain/state/`, and `ai-brain/specs/` into
those target-root folders. Legacy hidden data homes or stale data-root
overrides from older builds are treated as legacy and normalized to
`TARGET_ROOT`.

The real memory file is ignored by git so workspace-specific notes, run
summaries, detected commands, and adoption details do not get published. The
initializer also updates target `.gitignore` for generated local AI Brain
artifacts during subfolder installs.

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

Generated reports should stay under `state/reports/` at the repo root.

`make init-repo` preserves any text outside its generated marker block, so you
can keep durable human notes in this file while still letting AI Brain refresh
the detected repo profile.
