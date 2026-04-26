# Phase 3 — Sleep — Detailed Component Spec

## 3.1 — night_phase() Orchestrator

**Integration with decisions:**
- Runs only if York confirms RAM <70% and all Clones unloaded (Decision 7)
- Archivist is sole writer for strength updates during night
- Scheduler triggers via MongoDB log

**4 cycles:**
1. **Dreams:** reinforce high-strength LIQUID nodes (strength +=0.02)
2. **Nightmares:** adversarial test on top-20 crystals using Lilith prompts
3. **Cleanup:** run decay pass (Archivist)
4. **Lucid:** if trauma nodes uncleared OR coherence deadlock → generate synthetic resolution via Scout, write to Nest as GENERAL

**Pre-sleep flush:** `pre_sleep_flush()` verifies Clone unload via York, waits for RAM ≤270MB, then starts

**Acceptance:** Full run <4h on 10k nodes, NightReport written to Nest, post-sleep signal on `pr:bus:emergency`
