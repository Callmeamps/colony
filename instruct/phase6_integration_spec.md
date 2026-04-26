# Phase 6 — Integration — Detailed Component Spec

## 6.1 — End-to-End Integration Test

**Sequence with decisions:**
1. Bootstrap initial data (Phase 1.4) → verify ≥260 nodes
2. Submit 50 synthetic tasks
3. Verify routing in ArangoDB matches expected types
4. Verify York blocks load when RAM >85% (simulate via memory hog)
5. Trigger night_phase manually → verify Archivist sole writer for strength
6. Trigger Resource emergency → verify York dictator overrides others (priority test)
7. Run Raid mock → verify MongoDB logs created
8. Verify Antennae adapts: idle 50 tokens, active 30, lag 80

**Acceptance:**
- Task cycle <3s avg
- RAM never >1.2GB, returns ≤270MB within 5s
- No orphaned records across Cognee, SQLite, Redis, ArangoDB, MongoDB, Zep, MinIO
- Single-writer violations = 0 (tested via audit log)

## 6.2 — Observability Layer

**Decision 1 MongoDB:** All structured logs to MongoDB `colony.logs`

**Components:**
- JSON logs: every pheromone, dictator election, Valkyrie verdict, RAM threshold breach
- Metrics: RAM, latency, routing, prefetch hit rate, York interventions
- Status view (minimal HTML): shows current state, active Clone, dictator, Nest size by skill_type, last night summary, RAM %, Antennae mode (idle/active/lag)

**Zep integration:** Dashboard pulls recent session memory from self-hosted Zep for "last 5 user interactions"

**Acceptance:** Real-time updates via SSE, log query <1s, all critical events logged with full context
