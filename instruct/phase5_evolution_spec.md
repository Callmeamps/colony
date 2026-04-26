# Phase 5 — Evolution (Trollopes) — Detailed Component Spec
**Decisions applied:** MongoDB retained for logs

## 5.1 — Fertility Drones

**What:** Background experiments spawning new LoRA variants

**Storage:** ArangoDB `drone_log` for experiments, MongoDB `colony.drone_metrics` for time-series metrics (Decision 1)

**Process:** Edison triggers spawn when STV repeatedly selects same Clone with low confidence. Drone trains LoRA on recent failures (data from Nest). Runs offline.

**Acceptance:** Drone output does not affect live routing until Valkyrie approves

## 5.2 — Trollope Raids

**Weekly distillation from large API model**

**Cost cap:** $2/week default (configurable). If cap hit, run partial raid on top-50 failures only.

**Logs:** MongoDB `colony.raid_log`, ArangoDB `raid_log` for graph queries

**Process:** Select 100 prompts where Clone failed (from Zep telemetry). Query external model, distill to new LoRA. Submit to Valkyrie.

## 5.3 — Valkyrie

**Two-headed judge:**
- Head A: novelty + coherence (scores 0-1)
- Head B: robustness (adversarial test set, curated, not generated)

**Promotion rules:** PROMOTE if A≥0.7 and B≥0.65; REJECT if B<0.5; DEFER otherwise

**Authority:** Valkyrie veto cannot be overridden except by Coherence dictator (Pythagoras). Writes verdict to ArangoDB and MongoDB.

**Robustness test set:** Must be curated before Phase 5 (per D5). Store in MinIO `colony-cold-skills/valkyrie-testset`
