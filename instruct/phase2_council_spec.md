# Phase 2 — Council (Sonial) — Detailed Component Spec
**Decisions applied:** Zep self-hosted, Emergency priority hardcoded, Antennae adaptive, Single-writer rule, York hard authority

## 2.1 — Punk Records: Redis Layer

**Implementation:**
- Redis 7, namespaces `pr:*`
- Keys: `pr:ballot:{satellite}`, `pr:adv_scores`, `pr:atlas:urgency`, `pr:winner`, `pr:dictator`, `pr:prefetch:{session}`, `pr:bus:*`

**Single-writer rule:** Council is ONLY writer for routing state (`pr:winner`, `pr:dictator`, `pr:ballot:*`). Clones may READ only. Enforce via Redis ACL: council user = write, clone user = read.

## 2.2 — Punk Records: ArangoDB Layer

**Collections:** satellites, routing_decisions, stv_rounds, dictator_log, clone_performance
**Graph:** `punk_records_graph` with edges `VOTED_FOR`, `TRIGGERED`

**Single-writer:** Council writes routing_decisions and stv_rounds. Archivist writes clone_performance (synced from Zep). No other writers.

## 2.3 — Satellites

**York — RAM Governor (Decision 7):**
- Reads `/proc/meminfo` or psutil every 500ms
- Thresholds: >85% → publish `pr:bus:emergency` type=Resource, block new loads; >92% → force unload current Clone, set dictator
- York = hard authority: its Resource dictator cannot be overridden by other satellites
- Output ballot ranks Labourers by RAM cost (Voice < Chat < Code)

**Lilith — Adversarial:**
- 20M classifier (placeholder: keyword + regex if no dataset). Input: task + Nest trauma flags. Output adv_score

**Atlas — Urgency:** rule-based, <5ms

**Edison — Spawn logic:** queries ArangoDB drone_log

**Pythagoras — Coherence:** cosine similarity between task embedding and top Nest crystal

## 2.4 — Shaka STV Orchestrator

**Flow:** collect ballots (timeout 80ms) → run STV → check emergency consensus → publish winner

**Performance:** <100ms end-to-end

## 2.5 — Dictator Protocol (Decision 5)

**Hardcoded priority:** Trauma > Resource > Coherence > Deadlock
- Implemented as constant `EMERGENCY_PRIORITY = {"Trauma":0,"Resource":1,"Coherence":2,"Deadlock":3}`
- If simultaneous signals, lowest number wins. No ties. Code asserts priority, cannot be configured at runtime.

**Emergency types:**
- Trauma: Lilith adv_score >0.9 OR Nest trauma >0.7 → dictator=Lilith, TTL=5 turns, scope=labourer_selection+lucid
- Resource: York >85% → dictator=York, TTL=3 turns, scope=unload+freeze_drones (Decision 7: >92% triggers immediate unload)
- Coherence: Pythagoras incoherent 3× → dictator=Pythagoras, TTL=4 turns
- Deadlock: STV no winner 3× → dictator=Edison, TTL=2 turns

**TTL:** decrements per turn, stored in Redis with turn counter, not wall-clock

## 2.6 — Clone Telemetry Loop (Zep self-hosted)

**Decision 2:** Use self-hosted Zep, not cloud. Deploy via Docker `zepai/zep:latest` on localhost:8123, SQLite backend, no quota.

**Flow:**
- Clone emits `OutboundTelemetry` → written to Zep session memory AND published to `pr:bus:telemetry`
- Zep stores per-session short-term memory (last 50 turns)
- Archivist hourly sync: reads Zep summaries → writes to ArangoDB `clone_performance`
- **Single-writer:** Clones = append-only telemetry. They may not update or delete Zep entries. Enforce via Zep API wrapper that exposes only `append()`.

**Acceptance:** Zep persists across restarts, sync <1s, no Clone can modify past telemetry

## 2.7 — Antennae Prefetch (Decision 6: adaptive)

**Original 10-token fixed → replaced with adaptive:**
- idle → 50 tokens (user typing slowly or reading)
- active → 30 tokens (normal generation)
- lag → 80+ tokens (if previous prefetch >70ms or RAM >80%)

**State detection:**
- idle: no token generated in last 2s
- active: generation < 40ms/token
- lag: generation >70ms/token OR York reports RAM >80%

**Implementation:** background asyncio task, queries Nest top-8, writes to Redis ZSET `pr:prefetch:{session}` TTL 30s. Never blocks generation. Batch up to 3 sessions into single FAISS call.

**Acceptance:** Prefetch <50ms, adaptive switching verified in test harness

## 2.8 — RLM Integration (IMPLEMENTED)

**Recursive Language Model dispatch via `rlms` library:**
- Council uses `rlm.RLM(model="bonsai-1.7b")` for recursive routing
- Flow: task → RLM decomposes → sub-tasks → `_route_standard()` per sub-task
- NestREPL sandbox provides safe `exec()`/`eval()` for RLM-generated code
- Tools available: `query()`, `fetch()`, `ingest()` (wired to Nest)

**Implementation files:**
- `core/council.py` - RLM dispatch in `_route_recursive()`
- `core/workers/repl.py` - NestREPL sandbox
- `instruct/colonyctl.py` - CLI hooks into Council

**Acceptance:** RLM routes tasks, REPL executes safely, sub-calls stream via `pr:bus:telemetry`
