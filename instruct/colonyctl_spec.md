# colonyctl — CLI Interface Specification v1
**Target:** Celeron + Boksburg, Python 3.11, Redis 7, MongoDB 6
**Decisions applied:** Single-writer enforced, York hard authority, streaming default, zero model load

## 1. Overview
`colonyctl` is the primary human interface to the colony. It is a thin client that reads Redis/MongoDB and publishes to the pheromone bus. It never loads Scout or Clones directly.

**Install:** `/usr/local/bin/colonyctl`  
**Config:** `~/.config/colony/config.yaml`  
**RAM budget:** <15MB. York kills it if system >85%.

## 2. Config File
```yaml
# ~/.config/colony/config.yaml
redis_url: redis://localhost:6379/0
mongo_url: mongodb://localhost:27017
api_url: http://localhost:7777
default_stream: true
default_session: null
timeout_s: 30
```

## 3. Global Flags
| Flag | Description |
| --- | --- |
| --no-stream | Disable token streaming, buffer full response |
| --json | Machine-readable JSON output |
| --session <id> | Attach to Zep session_id |
| --timeout <s> | Override default 30s Clone timeout |

## 4. Commands

### 4.1 `colonyctl status`
**Purpose:** Instant health check.  
**Reads:** `pr:winner`, `pr:dictator`, `pr:york:ram`, MongoDB `nest_meta` count.  
**Output:**
```
Colony Boksburg | RAM: 612MB/1.2GB [51%] York: OK
State: ACTIVE | Dictator: None | Antennae: active/30t
Clone: Chat Worker | Nest: 1,847 nodes | Trauma: 3 | Crystals: 42
```
**Latency:** <50ms. **RAM:** 0MB.

### 4.2 `colonyctl task "<prompt>"`
**Purpose:** Submit inference task. Routes via Council + RLM. Streaming default.  
**Flow (IMPLEMENTED):**
1. Check York RAM (<85%)
2. Council.route() with RLM recursion (`rlm.RLM()`)
3. RLM decomposes task → sub-tasks → `_route_standard()`
4. Publish to `pr:bus:scout` with winner
5. Stream response via `pr:bus:telemetry`

**Writes:** Publishes `PheromoneSignal` to `pr:bus:scout` with event_id, source='cli'.  
**Reads:** Subscribes to `pr:bus:telemetry` filtered by session_id.  
**Streaming:** Prints `delta_text` chunks as they arrive. Ctrl+C publishes abort signal.  
**--no-stream:** Buffers until `status=COMPLETE`.  
**Output (streaming):**
```
> colonyctl task "write async sleep"
[Council] Routing task via RLM...
[Council] Task routed to: code_worker
[Scout] Urgency: 0.23
[Code Worker] Loading Bonsai-1.7B... 1.2s
[Stream]
async def sleep_ms(ms: int):
    await asyncio.sleep(ms / 1000)

[Done] 2.1s | Coherence: 0.94 | RAM peak: 650MB
```
**Errors:** If York blocks load at >85% RAM, prints `[York] Resource dictator active. Load blocked. Retry later.` and exits 1.

### 4.3 `colonyctl nest query "<q>" [--k 8]`
**Purpose:** Query Nest without waking Clones.  
**Reads:** HTTP GET `localhost:7777/v1/nest/query`.  
**Output:**
```
1. [FUNDAMENTAL 1.00] asyncio.gather
   Run multiple coroutines concurrently...
2. [LIQUID 0.73] asyncio.create_task
   Schedule coroutine execution...
```

### 4.4 `colonyctl dictator [check|clear]`
**check:** Reads `pr:dictator`. Shows type, TTL, scope, priority.  
**clear:** Publishes clear signal. Only succeeds if dictator=None or you are Pythagoras. Respects Decision 5 priority.  

### 4.5 `colonyctl york [--watch]`
**Purpose:** RAM governor status.  
**Reads:** `/proc/meminfo` + `pr:york:ram`.  
**Output:** `RAM: 612MB/1.2GB [51%] Status: OK | Block@85% Unload@92%`  
**--watch:** Updates every 500ms. Auto-exits if >85%.

### 4.6 `colonyctl sleep [--force]`
**Purpose:** Trigger `night_phase()`.  
**Logic:** Checks idle >30min unless --force. York must confirm RAM <70%.  
**Output:** Streams NightReport: `Cycle 1: Dreams... Cycle 2: Nightmares... Done.`

### 4.7 `colonyctl logs [--tail 50|--follow]`
**Purpose:** View MongoDB `colony.logs`.  
**--follow:** Uses MongoDB change streams for live tail.

### 4.8 `colonyctl prefetch [<session_id>]`
**Purpose:** Debug Antennae.  
**Reads:** `pr:prefetch:{session}` ZSET.  
**Output:** Top-8 crystals + strength + mode: `active/30t`.

### 4.9 `colonyctl top`
**Purpose:** Launch Textual TUI dashboard.  
**Exit:** `q`. York at >85% forces exit with warning.

## 5. Single-Writer Enforcement
CLI uses Redis ACL user `colony_cli` with: `+get +publish +subscribe -set -del`.  
Cannot write `pr:winner`, `pr:dictator`, or `nest_meta.strength`. Attempts raise `PermissionError`.  
All mutations go via `pr:bus:scout` or `pr:bus:emergency`.

## 6. Error Codes
| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | York blocked load, RAM >85% |
| 2 | Timeout waiting for Clone |
| 3 | Dictator active, command rejected |
| 4 | Permission denied, single-writer violation |
| 5 | Redis/MongoDB unreachable |

## 7. Example Session
```
$ colonyctl status
Colony Boksburg | RAM: 244MB/1.2GB [20%] York: OK
State: IDLE | Dictator: None | Antennae: idle/50t

$ colonyctl task "fibonacci in python"
[Scout] Urgency: 0.11 → Council routing...
[Shaka] STV winner: Code Worker (0.81)
[Stream]
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

[Done] 1.8s | Coherence: 0.97 | RAM peak: 876MB

$ colonyctl york --watch
RAM: 876MB [73%] OK | Block@85% Unload@92%
RAM: 271MB [23%] OK | Clone unloaded
^C
```

## 8. Security
- No secrets in CLI. Uses localhost only.
- Redis ACL limits damage if binary compromised.
- All commands log to MongoDB `colony.logs` with source='cli'.
