# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->


## Build & Test

```bash
# Install dependencies
pip install -r requirements.txt

# Run integration tests
python scripts/integration_test.py

# Run E2E verification
python scripts/integration_test.py

# Lint (if available)
# flake8 core/ instruct/
```

## Architecture Overview

Colony - Boksburg Celeron (1.2GB RAM) model orchestration.

**Core modules (deep modules, small interface):**
- `core/nest.py` - HybridRAG memory (vector + graph + decay)
- `core/council.py` - STV routing + RLM recursive dispatch
- `core/workers/scout.py` - Bonsai-1.7B urgency scoring (llama.cpp)
- `core/workers/loader.py` - Worker model loading (York RAM-enforced)
- `core/workers/repl.py` - NestREPL sandbox (safe exec/eval)
- `core/satellites/york.py` - RAM governor (dynamic thresholds)

**Interface:** `colonyctl` CLI + FastAPI (`instruct/colony_api_main.py`)

## Conventions & Patterns

- **Deep modules**: Small public interface, deep implementation (see `core/council.py`)
- **Beads (bd)**: All task tracking via `bd` CLI, never TODO lists
- **Caveman docs**: Terse, no fluff, technical terms exact
- **TDD**: Red-green-refactor, one test at a time
- **Surgical edits**: Touch only what's needed, match existing style
