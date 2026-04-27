# Phase 4 — Inference — Detailed Component Spec
**Decisions applied:** Scout = Phi/TinyLlama transformer, York hard authority, RAM enforcement

## 4.1 — Scout (Decision 3)

**Model: Bonsai-1.7B Q4_0 (IMPLEMENTED)**
- Architecture: 1.7B params, INT4 GGUF quantization
- Size: ~200MB disk, ~250MB RAM (300MB with overhead)
- Runtime: llama.cpp Python bindings (`llama-cpp-python`)
- Inference: <50ms per classification
- Load: `core/workers/scout.py`, lazy init via `_ensure_model()`

**Functions (IMPLEMENTED):**
- Urgency score 0-1 → writes to Atlas
- Wake decision: if query answerable from Nest top-1 crystal with cosine >0.85, respond directly (no Clone wake)
- Batches Antennae FAISS queries

**Acceptance:** Idle RAM <270MB total (Scout + Redis + OS overhead), urgency scoring via heuristic + model

## 4.2 — Clone Workers (IMPLEMENTED)

**Model: Bonsai-1.7B Q4_0**
- Single model for all workers (Code/Chat/Voice)
- Size: ~300MB RAM with overhead
- Load: `core/workers/loader.py` via llama.cpp Python bindings
- RAM enforcement: York dynamic thresholds (85% block, 92% unload)

**RAM enforcement (Decision 7, IMPLEMENTED):**
- York monitors continuously, reads `pr:model_ram` for dynamic threshold
- Before load: if (RAM + model_ram) / 1200 > 85% → block, trigger Resource dictator
- During generation: if RAM >92% → York force-unloads, emits ABORTED_RAM
- Only one Clone loaded at time; Council enforces via `pr:winner` lock

**Load/unload contract (IMPLEMENTED):**
- Load: `WorkerLoader.load_clone()` → Llama() instance
- Unload: `WorkerLoader.unload_all()` → del llm, gc
- After unload, RAM returns to ~270MB baseline

**Single-writer:** Clones append-only to telemetry (Zep). Cannot write to Nest or routing state.

## 4.3 — Quantization Governor

**Weekly job run by Archivist**

**Demotion schedule unchanged, but respects York thresholds:**
- Never demote if doing so would leave <2 copies of a skill type
- Before requantise, check RAM <75% else defer

**Outputs to MongoDB:** `colony.quantization_log`

**Acceptance:** Dry-run mode, loadable models after requant, FUNDAMENTAL/INNATE never touched
