# Phase 1 — Nest (Memory) — Detailed Component Spec
**Target:** Boksburg Celeron, 1.2GB peak RAM
**Status:** Build-ready
**Decisions applied:** MongoDB retained, Zep self-hosted, Single-writer rule enforced, Startup data required

## 1.1 — Nest Core (Cognee HybridRAG)

**What it is:** Long-term memory with vector + graph + SQLite meta. Single source of truth for all memories.

**Stack changes:**
- Cognee configured with LanceDB (vectors), NetworkX (in-memory graph persisted to SQLite), SQLite meta
- MongoDB NOT used here (reserved for logs)
- Zep is NOT part of Nest; Zep is for short-term session memory only (Phase 2.6)

**Inputs:**
- `NestNode` dataclass:
  ```python
  @dataclass
  class NestNode:
      node_id: str  # uuid4
      text: str
      skill_type: Literal["LIQUID","FUNDAMENTAL","INNATE","ONE_OFF","RUSTY","STALE","CRYSTALLISED"]
      strength: float  # 0.0-1.0
      trauma: float    # 0.0-1.0
      last_access: datetime
      created_at: datetime
      raid_lineage: str | None
      metadata: dict
  ```

**Outputs:**
- `add_to_nest(node) -> None`
- `query_nest(query: str, top_k=8, filter_skill=None) -> list[NestNode]`
- `fetch_node_text(node_id) -> str`
- `delete_from_nest(node_id) -> None`
- SQLite row in `nest/meta.db` table `nest_meta` with indexes on (skill_type, strength, last_access)

**Implementation notes:**
- HybridRAG: vector search (top_k*2) → rerank with graph proximity → return top_k
- **Single-writer rule:** ONLY Archivist writes `strength`. Nest Core may write on add/delete, but strength updates go through `archivist.update_strength()` API. Enforce via SQLite trigger that rejects UPDATE strength WHERE source != 'archivist'.
- Batch inserts: `add_many(nodes: list[NestNode])` uses Cognee `cognify()` once per batch, not per node
- Startup data requirement: on first boot, if `nest_meta` count < 50, call `bootstrap_initial_data()` (see 1.4)

**Acceptance criteria:**
- Add 100 nodes in < 3s, query < 200ms
- Hybrid query returns both semantic and keyword matches
- Strength field immutable to non-Archivist callers (test fails if violated)

## 1.2 — Archivist: Decay Pass

**What it is:** Hourly forgetting curve. ONLY writer for strength.

**Formula (hardcoded):**
```
new_strength = strength * exp(-Δt / τ) + δ * hit
where τ per skill_type:
  LIQUID: 24h, ONE_OFF: 1h, RUSTY: 168h, STALE: 72h
  FUNDAMENTAL/INNATE/CRYSTALLISED: τ = ∞ (skip)
δ = 0.05 per hit
```

**Single-writer enforcement:**
- Archivist holds exclusive WAL lock on `nest_meta` during pass
- All other components read-only; writes attempted raise `PermissionError`
- API: `archivist.get_strength(node_id)` read-only for others

**Outputs:**
- Eviction: delete from Cognee + SQLite when strength ≤ 0.01 and skill_type in [ONE_OFF, STALE, LIQUID]
- Crystallisation: if strength ≥ 0.85 for 7 consecutive days and hits ≥ 20 → promote to CRYSTALLISED, set τ=∞
- RUSTY → GENERAL promotion on first hit (strength += 0.1)

**Acceptance:** Pass on 10k nodes < 10s, no drift, FUNDAMENTAL unchanged

## 1.3 — Archivist: Scheduler

**What it is:** Cron wrapper. Persists next-run times to MongoDB (decision 1: MongoDB retained).

**Jobs:**
- `run_hourly()` → decay pass
- `run_nightly()` → `night_phase()` (only if idle >30min)
- `run_weekly()` → quantization governor

**MongoDB collections:**
- `colony.scheduler_log` documents: {job, started_at, finished_at, status, nodes_processed}

**Persistence:** Next-run times stored in Redis `pr:scheduler:*` with TTL, mirrored to MongoDB for crash recovery

**Acceptance:** Survives restart, missed runs logged, independently triggerable

## 1.4 — Initial Data Bootstrap (NEW - Decision 4)

**What it is:** System needs startup data so we generate/retrieve seed memories on first boot.

**Sources:**
1. **Retrieval:** Load 200 public-domain factual snippets (Wikipedia abstracts for Python, Linux, basic math) → skill_type=FUNDAMENTAL, strength=1.0, trauma=0.0
2. **Generation:** Use Scout (Phi-class) to generate 50 synthetic task traces: "user asked X, answer Y" → skill_type=LIQUID, strength=0.6
3. **Trauma seeds:** 10 synthetic adversarial prompts (from HarmBench subset) marked trauma=0.8, skill_type=ONE_OFF, to test Lilith + Lucid

**Process:**
- Runs once if `nest_meta.count < 50`
- Writes via `add_many()`
- Logs to MongoDB `colony.bootstrap`

**Acceptance:** After bootstrap, Nest contains ≥260 nodes, query "Python" returns FUNDAMENTAL node in top-3
