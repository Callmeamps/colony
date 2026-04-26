# main.py - Colony API FastAPI skeleton
# pip install fastapi uvicorn[standard] redis pymongo sse-starlette pyyaml
# Run: uvicorn main:app --host 127.0.0.1 --port 7777

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
import asyncio
import json
import time
import uuid
import pymongo
from core.records import PunkRecords, DictatorProtocol
from core.council import Council
from core.sleep import SleepCycle
from core.nest import Nest
from core.workers.loader import WorkerLoader, Scout

app = FastAPI(title="Colony API", version="1.0.0")

# Setup Core components
pr = PunkRecords()
dp = DictatorProtocol(pr)
council = Council(pr)
sleep_cycle = SleepCycle(pr, None) # Archivist removed, logic now in Nest
loader = WorkerLoader(pr)
scout = Scout(pr)
mongo = pymongo.MongoClient("mongodb://localhost:27017")

# Models matching OpenAI spec + extensions
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ColonyMetadata(BaseModel):
    force_clone: Optional[Literal["code_worker", "chat_worker", "voice_worker"]] = None
    dictator_override: bool = False

class ChatCompletionRequest(BaseModel):
    model: Literal["colony-auto", "colony-code", "colony-chat", "colony-voice"]
    messages: List[Message]
    stream: bool = True  # Colony default
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    user: Optional[str] = None  # Zep session_id
    metadata: Optional[ColonyMetadata] = None

class ColonyMetadataResponse(BaseModel):
    coherence: float
    ram_peak_mb: int
    crystals_used: int
    dictator: Optional[str]
    clone: str
    duration_ms: int

class SleepRequest(BaseModel):
    force: bool = False

class NestQueryRequest(BaseModel):
    query: str
    k: int = 8

async def check_york():
    ram = int(await pr.r.get("pr:york:ram") or 0)
    if ram / 1200 > 0.85:
        raise HTTPException(503, detail={"error": {"code": "resource_exhausted", "message": "York: RAM >85%, load blocked"}})

async def stream_generator(event_id: str, model: str):
    pubsub = pr.r.pubsub()
    await pubsub.subscribe("pr:bus:telemetry")
    created = int(time.time())
    yield {"data": json.dumps({"id": event_id, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]})}
    async for msg in pubsub.listen():
        if msg["type"] != "message": continue
        data = json.loads(msg["data"])
        if data.get("event_id") != event_id: continue
        if data.get("delta_text"):
            yield {"data": json.dumps({"id": event_id, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [{"index": 0, "delta": {"content": data["delta_text"]}, "finish_reason": None}]})}
        if data.get("status") in ["COMPLETE", "ABORTED_RAM"]:
            yield {"data": json.dumps({"id": event_id, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop" if data["status"] == "COMPLETE" else "length", "colony_metadata": data}]})}
            yield {"data": "[DONE]"}
            break
    await pubsub.unsubscribe("pr:bus:telemetry")

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    await check_york()
    event_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    prompt = "\n".join([f"{m.role}: {m.content}" for m in req.messages])
    
    # Run Scout Urgency Check
    scout_data = await scout.classify(prompt)
    
    # Use Deep Council Interface
    asyncio.create_task(council.route({
        "event_id": event_id,
        "prompt": prompt,
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "session": req.user,
        "force_clone": req.metadata.force_clone if req.metadata else None,
        "source": "api",
        "urgency": scout_data["urgency"]
    }))
    
    if req.stream: return EventSourceResponse(stream_generator(event_id, req.model))
    
    full_content = []
    meta = None
    async for chunk in stream_generator(event_id, req.model):
        if chunk == {"data": "[DONE]"}: break
        d = json.loads(chunk["data"])
        delta = d["choices"][0].get("delta", {})
        if "content" in delta: full_content.append(delta["content"])
        if d["choices"][0].get("finish_reason"): meta = d["choices"][0].get("colony_metadata")
    return {"id": event_id, "object": "chat.completion", "created": int(time.time()), "model": req.model, "choices": [{"index": 0, "message": {"role": "assistant", "content": "".join(full_content)}, "finish_reason": "stop"}], "colony_metadata": meta}

@app.post("/v1/nest/query")
async def nest_query(req: NestQueryRequest):
    res = await Nest.query(req.query, req.k)
    return {"results": res}

@app.post("/v1/sleep")
async def sleep(req: SleepRequest):
    asyncio.create_task(sleep_cycle.run_night_phase(req.force))
    return {"status": "scheduled", "idle_check_passed": True}

@app.websocket("/v1/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    pubsub = pr.r.pubsub()
    await pubsub.subscribe("pr:bus:telemetry", "pr:bus:emergency")
    try:
        async for msg in pubsub.listen():
            if msg["type"] == "message": await websocket.send_text(msg["data"])
    except WebSocketDisconnect: pass
    finally: await pubsub.unsubscribe("pr:bus:telemetry", "pr:bus:emergency")

@app.on_event("startup")
async def startup():
    await Nest.bootstrap()

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "colony-auto", "object": "model", "owned_by": "colony"},
            {"id": "colony-code", "object": "model", "owned_by": "colony"},
            {"id": "colony-chat", "object": "model", "owned_by": "colony"},
            {"id": "colony-voice", "object": "model", "owned_by": "colony"}
        ]
    }

@app.get("/v1/status")
async def status():
    ram = int(await r.get("pr:york:ram") or 0)
    return {
        "ram_mb": ram,
        "ram_pct": round(ram / 1200 * 100, 1),
        "york_status": "UNLOAD" if ram > 1104 else "BLOCK" if ram > 1020 else "OK",
        "state": "ACTIVE" if await r.get("pr:winner") else "IDLE",
        "dictator": (await r.hget("pr:dictator", "type")) or None,
        "active_clone": await r.get("pr:winner"),
    }
