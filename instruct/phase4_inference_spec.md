# Phase 4 — Inference — Detailed Component Spec
**Decisions applied:** Scout = Phi/TinyLlama transformer, York hard authority, RAM enforcement

## 4.1 — Scout / Fertilizer (Decision 3)

**Changed from Mamba 370M → small transformer now, swap later**

**Model spec v0:**
- Architecture: Transformer decoder (Phi-2 2.7B distilled or TinyLlama 1.1B 4-bit)
- Target: ~350M active params after distillation/quantization
- Quantization: INT4 GGUF → ~200MB disk, ~250MB RAM
- Runtime: llama.cpp CPU, always loaded, never unloaded
- Inference: <50ms per classification

**Swap plan:** Interface unchanged (LabourerInterface). When Mamba checkpoint available, replace model file, no code change.

**Functions:**
- Urgency score 0-1 → writes to Atlas
- Wake decision: if query answerable from Nest top-1 crystal with cosine >0.85, respond directly (no Clone wake)
- Batches Antennae FAISS queries

**Acceptance:** Idle RAM <270MB total (Scout + Redis + OS overhead), 80% accuracy on synthetic urgency set

## 4.2 — Clone Workers

**Models:**
- Code: 1.3B (CodeLlama) INT4 → ~650MB
- Chat: 0.5B (TinyLlama-chat) INT4 → ~300MB
- Voice: 0.5B with lora-voice → ~300MB

**RAM enforcement (Decision 7):**
- York monitors continuously
- Before load: if RAM >85% → block load, return error to Council, trigger Resource dictator
- During generation: if RAM >92% → York force-unloads Clone mid-task, emits `OutboundTelemetry` status=ABORTED_RAM, Council retries with smaller model
- Only one Clone loaded at time; Council enforces via `pr:winner` lock

**Load/unload contract:**
- Load <1.4s from NVMe
- After unload, RAM ≤270MB (verified by York)
- LoRA swap without full unload allowed if base model same

**Single-writer:** Clones append-only to telemetry (Zep). Cannot write to Nest or routing state.

## 4.3 — Quantization Governor

**Weekly job run by Archivist**

**Demotion schedule unchanged, but respects York thresholds:**
- Never demote if doing so would leave <2 copies of a skill type
- Before requantise, check RAM <75% else defer

**Outputs to MongoDB:** `colony.quantization_log`

**Acceptance:** Dry-run mode, loadable models after requant, FUNDAMENTAL/INNATE never touched
