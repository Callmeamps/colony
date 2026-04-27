# Colony API — OpenAI-Compatible Interface Spec v1
**Base URL:** `http://localhost:7777/v1`  
**Compatibility target:** OpenAI Chat Completions API v1  
**Decisions applied:** Single-writer enforced, York hard authority, streaming default, Zep session support

## 1. Philosophy
The API is a *protocol adapter*, not a model server. It translates OpenAI-standard requests into pheromone signals, lets the Council route to a Clone, and streams telemetry back as OpenAI-format SSE. 

**Key constraints:**
- **No direct model load.** API never instantiates Scout/Clones. It publishes to `pr:bus:scout`.
- **Single-writer.** API is read-only. All writes go via pheromone bus. API key `colony_api` has Redis ACL `+get +publish +subscribe -set`.
- **York enforcement.** If `pr:york:ram` >85%, `/v1/chat/completions` returns 503 with `error.code: "resource_exhausted"`.
- **Streaming default.** `stream: false` must be explicitly set to disable.

## 2. Authentication
None for localhost. If exposed, use header: `Authorization: Bearer colony-local`. No quota enforcement.

## 3. Endpoints

### 3.1 POST /v1/chat/completions — Primary
**OpenAI compatible.** Submit a task. Colony routes via Scout → Council → Clone.

**Request Body (OpenAI standard + Colony extensions):**
```json
{
  "model": "colony-code",  // maps to clone: colony-code|colony-chat|colony-voice|colony-auto
  "messages": [
    {"role": "system", "content": "You are a code assistant"},
    {"role": "user", "content": "write async sleep"}
  ],
  "stream": true,  // default true for Colony, unlike OpenAI
  "temperature": 0.7,
  "max_tokens": 512,
  "user": "session_abc123",  // maps to Zep session_id
  "metadata": {  // Colony-specific, optional
    "force_clone": null,  // bypass STV: "code_worker"|"chat_worker"|"voice_worker"
    "dictator_override": false  // allow dictator to hijack, default false
  }
}
```

**Model mapping:**
| model | Clone | Notes |
| --- | --- | --- |
| colony-auto | STV via Shaka | Default. Runs full Council vote |
| colony-code | Code Worker (Clone) 1.3B | Bypasses STV |
| colony-chat | Chat Worker (Clone) 0.5B | Bypasses STV |
| colony-voice | Voice Worker (Clone) 0.5B | Bypasses STV |
| colony-scout | Scout (Bonsai-1.7B) | Direct mode. Lightweight |

**Response — Streaming (SSE):**
```
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"id":"chatcmpl-7f3a","object":"chat.completion.chunk","created":1712345678,"model":"colony-code","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-7f3a","object":"chat.completion.chunk","created":1712345678,"model":"colony-code","choices":[{"index":0,"delta":{"content":"async"},"finish_reason":null}]}

data: {"id":"chatcmpl-7f3a","object":"chat.completion.chunk","created":1712345678,"model":"colony-code","choices":[{"index":0,"delta":{"content":" def"},"finish_reason":null}]}

data: {"id":"chatcmpl-7f3a","object":"chat.completion.chunk","created":1712345678,"model":"colony-code","choices":[{"index":0,"delta":{},"finish_reason":"stop","colony_metadata":{"coherence":0.94,"ram_peak_mb":891,"crystals_used":3,"dictator":null,"clone":"code_worker","duration_ms":2100}}]}

data: [DONE]
```

**Response — Non-streaming:**
```json
{
  "id": "chatcmpl-7f3a",
  "object": "chat.completion",
  "created": 1712345678,
  "model": "colony-code",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "async def sleep_ms(ms: int):\n    await asyncio.sleep(ms / 1000)"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 18,
    "total_tokens": 30
  },
  "colony_metadata": {
    "coherence": 0.94,
    "ram_peak_mb": 891,
    "crystals_used": 3,
    "dictator": null,
    "clone": "code_worker",
    "duration_ms": 2100,
    "stv_rounds": 1
  }
}
```

**Error Codes:**
| HTTP | error.code | Meaning |
| --- | --- | --- |
| 503 | resource_exhausted | York: RAM >85%, load blocked |
| 409 | dictator_active | Dictator override, request rejected unless metadata.dictator_override=true |
| 408 | timeout | Clone took >timeout_s, York may have force-unloaded |
| 403 | permission_denied | Single-writer violation attempt |

### 3.2 GET /v1/models
**OpenAI compatible.** List available clones.
```json
{
  "object": "list",
  "data": [
    {"id": "colony-auto", "object": "model", "owned_by": "colony", "permission": []},
    {"id": "colony-code", "object": "model", "owned_by": "colony"},
    {"id": "colony-chat", "object": "model", "owned_by": "colony"},
    {"id": "colony-voice", "object": "model", "owned_by": "colony"},
    {"id": "colony-scout", "object": "model", "owned_by": "colony"}
  ]
}
```

### 3.3 GET /v1/status
**Colony-specific.** Not in OpenAI spec. Returns same data as `colonyctl status`.
```json
{
  "ram_mb": 612,
  "ram_pct": 51.0,
  "york_status": "OK",
  "state": "ACTIVE",
  "dictator": null,
  "active_clone": "chat_worker",
  "antennae_mode": "active/30t",
  "nest_nodes": 1847,
  "trauma_nodes": 3,
  "crystals": 42
}
```

### 3.4 POST /v1/nest/query
**Colony-specific.** HybridRAG search without waking Clones.
**Request:** `{"query": "asyncio", "k": 8}`  
**Response:** `{"results": [{"node_id": "1a3f", "skill_type": "FUNDAMENTAL", "strength": 1.0, "text": "asyncio.gather..."}]}`

### 3.5 POST /v1/sleep
**Colony-specific.** Trigger `night_phase()`.  
**Request:** `{"force": false}`  
**Response:** `{"status": "scheduled", "idle_check_passed": true}`  
NightReport streams via websocket `/v1/ws/telemetry` if connected.

### 3.6 WS /v1/ws/telemetry
**Colony-specific.** WebSocket stream of `pr:bus:telemetry` + `pr:bus:emergency`.  
**Messages:** JSON `OutboundTelemetry` objects. Use for Godot live updates.

## 4. Streaming Implementation
1. Client POSTs to `/v1/chat/completions` with `stream: true`.
2. API generates `event_id`, publishes `PheromoneSignal` to `pr:bus:scout` with `prompt`, `temperature`, `max_tokens`, `session=user`.
3. API subscribes to `pr:bus:telemetry` filtered by `event_id`.
4. For each `OutboundTelemetry.delta_text` from Clone, API emits SSE `data:` line with `choices[0].delta.content`.
5. On `OutboundTelemetry.status=COMPLETE`, API emits final chunk with `finish_reason: "stop"` + `colony_metadata`, then `data: [DONE]`.
6. If `status=ABORTED_RAM`, emit `finish_reason: "length"` and `error` in `colony_metadata`.
7. Client disconnect = publish abort to `pr:bus:emergency`.

## 5. Zep Session Mapping
OpenAI `user` field → Zep `session_id`. If omitted, API generates `sess_<uuid>`.  
All `messages` are appended to Zep session memory. Colony reads last 10 turns for context.  
Clones are append-only to Zep; cannot delete history.

## 6. York Enforcement
Before publishing to `pr:bus:scout`, API checks `pr:york:ram`. If >85%: return 503 immediately.  
If RAM crosses 92% mid-stream: Clone force-unloaded, stream ends with `finish_reason: "length"` and `colony_metadata.dictator: "Resource"`.

## 7. Single-Writer Compliance
API Redis user has ACL: `+get +publish +subscribe +xread -set -del -hset`.  
Cannot write `pr:winner`, `pr:dictator`, `nest_meta.strength`. All mutations via pheromone bus only.

## 8. OpenAPI 3.1 Snippet
```yaml
openapi: 3.1.0
info:
  title: Colony API
  version: 1.0.0
  description: OpenAI-compatible interface to Colony
paths:
  /v1/chat/completions:
    post:
      operationId: createChatCompletion
      requestBody:
        content:
          application/json:
            schema:
              allOf:
                - $ref: '#/components/schemas/CreateChatCompletionRequest'
                - type: object
                  properties:
                    metadata:
                      type: object
                      properties:
                        force_clone:
                          type: string
                          enum: [code_worker, chat_worker, voice_worker]
                        dictator_override:
                          type: boolean
      responses:
        '200':
          description: SSE stream or JSON
          content:
            text/event-stream:
              schema:
                type: string
            application/json:
              schema:
                $ref: '#/components/schemas/CreateChatCompletionResponse'
components:
  schemas:
    CreateChatCompletionRequest:
      type: object
      required: [model, messages]
      properties:
        model:
          type: string
          enum: [colony-auto, colony-code, colony-chat, colony-voice, colony-scout]
        messages:
          type: array
          items:
            type: object
            properties:
              role: {type: string, enum: [system, user, assistant]}
              content: {type: string}
        stream: {type: boolean, default: true}
        temperature: {type: number}
        max_tokens: {type: integer}
        user: {type: string}
    CreateChatCompletionResponse:
      type: object
      properties:
        id: {type: string}
        object: {type: string, enum: [chat.completion]}
        created: {type: integer}
        model: {type: string}
        choices:
          type: array
          items:
            type: object
            properties:
              index: {type: integer}
              message:
                type: object
                properties:
                  role: {type: string}
                  content: {type: string}
              finish_reason: {type: string}
        colony_metadata:
          type: object
          properties:
            coherence: {type: number}
            ram_peak_mb: {type: integer}
            crystals_used: {type: integer}
            dictator: {type: [string, 'null']}
            clone: {type: string}
            duration_ms: {type: integer}
```

## 9. Example cURL
```bash
curl -N http://localhost:7777/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "colony-scout",
    "messages": [{"role": "user", "content": "scout ahead"}],
    "stream": true,
    "user": "my-session"
  }'
```

## 10. Godot Integration
Point your HTTPRequest node at `localhost:7777/v1/chat/completions`.  
Parse SSE: split on `\n\n`, ignore `[DONE]`, append `delta.content` to Label.  
Use `/v1/ws/telemetry` WebSocket for dictator alerts and RAM warnings.
