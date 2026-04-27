# Phase 6 — Integration — Detailed Component Spec

## 6.1 — End-to-End Integration Test (IMPLEMENTED)

**Script:** `scripts/integration_test.py`

**Sequence with decisions:**
1. Bootstrap initial data (Phase 1.4) → verify ≥260 nodes
2. Test York RAM Enforcement → verify block at 85%
3. Test Council + RLM Routing → verify recursive dispatch via `rlm.RLM()`
4. Test WorkerLoader (Bonsai-1.7B) → verify llama.cpp loading + unload
5. Test Nest Query → verify HybridRAG search
6. Test Event Streaming → verify `pr:bus:scout` publish
7. Verify York Monitor Values → check `pr:model_ram` dynamic threshold
8. Test RLM Recursion → verify sub-task decomposition
9. Test NestREPL Tool Calls → verify `query()`, `fetch()` in sandbox

**Additional Tests (IMPLEMENTED):**
- `test_rlm_recursion()` - RLM recursive routing with sub-calls
- `test_nest_tool_calls()` - NestREPL sandbox with query/fetch tools

**Acceptance:**
- Task cycle <3s avg
- RAM never >1.2GB, returns ≤270MB within 5s
- No orphaned records across Cognee, SQLite, Redis, MongoDB, Zep
- Single-writer violations = 0 (tested via audit log)
- RLM routes tasks correctly, REPL executes safely

## 6.2 — Observability Layer

**Decision 1 MongoDB:** All structured logs to MongoDB `colony.logs`

**Components:**
- JSON logs: every pheromone, dictator election, Valkyrie verdict, RAM threshold breach
- Metrics: RAM, latency, routing, prefetch hit rate, York interventions
- Status view (minimal HTML): shows current state, active Clone, dictator, Nest size by skill_type, last night summary, RAM %, Antennae mode (idle/active/lag)

**Zep integration:** Dashboard pulls recent session memory from self-hosted Zep for "last 5 user interactions"

**Acceptance:** Real-time updates via SSE, log query <1s, all critical events logged with full context
