# Colony

Colony - model orchestration for Boksburg Celeron (1.2GB RAM). Decentralized memory (Nest), voting router (Council), evolutionary loop.

## Core Architecture

- **Nest (Memory)**: HybridRAG (Vector + Graph) + exponential forgetting.
- **Council (Routing)**: STV election via Satellites (York, Lilith, Atlas). **RLM recursive dispatch**.
- **York (RAM Governor)**: Dynamic thresholds (85% block, 92% unload) based on loaded model.
- **Scout (Triage)**: Bonsai-1.7B Q4_0 urgency scoring + direct Nest answers. llama.cpp. Always loaded, <50ms.
- **Evolution**: LoRA spawning (Drones) + distillation (Raids) judged by Valkyrie.
- **WorkerLoader**: Loads Bonsai-1.7B via llama.cpp Python bindings. RAM-enforced.
- **NestREPL**: Safe exec/eval sandbox with tool registry (query, fetch, ingest).

## Components

- `instruct/`: OpenAI-compatible FastAPI + CLI (`colonyctl`).
- `core/`: Deep modules - Routing, Memory, Evolution, Scout.
- `core/council.py`: Council with RLM recursion via `rlms` library.
- `core/workers/scout.py`: Scout - llama.cpp inference + Nest lookup.
- `core/workers/loader.py`: WorkerLoader - Bonsai-1.7B with York RAM checks.
- `core/workers/repl.py`: NestREPL - safe code execution for RLM.
- `models/`: Config files + model manifests.
- `scripts/`: Integration tests + E2E verification.

## Status

✅ RLM integration (rlms + llama.cpp)
✅ NestREPL sandbox
✅ Bonsai-1.7B integration (Scout + Workers)
✅ York dynamic thresholds
✅ E2E verification + integration tests

## Getting Started

```bash
# Install deps
pip install -r requirements.txt

# Verify
colonyctl status
colonyctl task "test prompt"
colonyctl york --watch
```

See `SETUP.md` for full install. `UBIQUITOUS_LANGUAGE.md` for glossary.
