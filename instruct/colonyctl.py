#!/usr/bin/env python3
# colonyctl - CLI for Colony
# Python 3.11+ | Typer + Redis + PyMongo + Websockets
# Install: pip install typer[all] redis pymongo websockets pyyaml rich

import typer
import asyncio
import json
import redis.asyncio as redis
import pymongo
import yaml
import os
import sys
import signal
import uuid
import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.table import Table
from core.council import Council
from core.records import PunkRecords

app = typer.Typer(help="Colony control interface")
console = Console()
CONFIG_PATH = Path.home() / ".config" / "colony" / "config.yaml"

def load_config():
    if not CONFIG_PATH.exists():
        # Fallback for dev
        dev_config = Path("config.yaml")
        if dev_config.exists():
            return yaml.safe_load(dev_config.read_text())
        console.print(f"[red]Config not found: {CONFIG_PATH}[/red]")
        raise typer.Exit(1)
    return yaml.safe_load(CONFIG_PATH.read_text())

def get_redis_async(cfg):
    return redis.from_url(cfg['redis_url'], decode_responses=True)

def get_redis_sync(cfg):
    import redis as redis_sync
    return redis_sync.from_url(cfg['redis_url'], decode_responses=True)

def get_mongo(cfg):
    return pymongo.MongoClient(cfg['mongo_url'])

@app.command()
def status(json_out: bool = typer.Option(False, "--json")):
    """Show colony health: RAM, dictator, active clone, nest size"""
    cfg = load_config()
    r = get_redis_sync(cfg)
    m = get_mongo(cfg)
    
    ram = r.get("pr:york:ram") or "0"
    ram_pct = int(ram) / 1200 * 100
    dictator = r.hgetall("pr:dictator") or {"type": "None"}
    winner = r.get("pr:winner") or "None"
    nest_count = m.colony.nest_meta.count_documents({})
    trauma_count = m.colony.nest_meta.count_documents({"trauma": {"$gt": 0.5}})
    
    if json_out:
        print(json.dumps({
            "ram_mb": int(ram),
            "ram_pct": round(ram_pct, 1),
            "dictator": dictator.get("type"),
            "active_clone": winner,
            "nest_nodes": nest_count,
            "trauma_nodes": trauma_count
        }))
        return
    
    console.print(f"Colony Boksburg | RAM: {ram}MB/1.2GB [{ram_pct:.0f}%] York: {'WARN' if ram_pct > 85 else 'OK'}")
    console.print(f"State: {'ACTIVE' if winner != 'None' else 'IDLE'} | Dictator: {dictator.get('type')} | Antennae: active/30t")
    console.print(f"Clone: {winner} | Nest: {nest_count} nodes | Trauma: {trauma_count}")

@app.command()
def york(watch: bool = typer.Option(False, "--watch", help="Live update every 500ms")):
    """Show York RAM governor status"""
    cfg = load_config()
    r = get_redis_sync(cfg)
    
    def show():
        ram = int(r.get("pr:york:ram") or 0)
        pct = ram / 1200 * 100
        status = "UNLOAD" if pct > 92 else "BLOCK" if pct > 85 else "OK"
        console.print(f"RAM: {ram}MB/1.2GB [{pct:.0f}%] Status: {status} | Block@85% Unload@92%")
        if pct > 85:
            console.print("[red]York threshold exceeded. Exiting.[/red]")
            raise typer.Exit(1)
    
    if not watch:
        show()
        return
    
    try:
        while True:
            show()
            asyncio.run(asyncio.sleep(0.5))
    except KeyboardInterrupt:
        pass

async def run_task(prompt: str, stream: bool, session: Optional[str], timeout: int):
    cfg = load_config()
    r = get_redis_async(cfg)
    event_id = f"cli-{uuid.uuid4().hex[:8]}"
    
    # Initialize Council with RLM
    pr = PunkRecords()
    council = Council(pr)
    
    # Check York RAM first
    ram = int(await r.get("pr:york:ram") or 0)
    if ram / 1200 > 0.85:
        console.print("[red][York] Resource dictator active. Load blocked. Retry later.[/red]")
        return

    # Route task through Council with RLM
    console.print(f"[Council] Routing task via RLM...")
    try:
        winner = await council.route({
            "event_id": event_id,
            "prompt": prompt,
            "source": "cli",
            "session": session or f"sess-{uuid.uuid4().hex[:6]}",
            "recursive": True
        })
        console.print(f"[Council] Task routed to: {winner}")
        
        # Publish to pheromone bus for satellites
        await r.publish("pr:bus:scout", json.dumps({
            "event_id": event_id,
            "prompt": prompt,
            "source": "cli",
            "session": session or f"sess-{uuid.uuid4().hex[:6]}",
            "winner": winner
        }))
    except Exception as e:
        console.print(f"[red][Council] RLM error: {e}[/red]")
        return

    pubsub = r.pubsub()
    await pubsub.subscribe("pr:bus:telemetry")
    
    start_time = time.time()
    full_text = []
    
    try:
        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            data = json.loads(msg["data"])
            if data.get("event_id") != event_id:
                continue
            
            if "scout_info" in data:
                console.print(f"[Scout] {data['scout_info']}")
            if "winner" in data:
                console.print(f"[Shaka] STV winner: {data['winner']}")
            
            if data.get("delta_text"):
                if stream:
                    print(data["delta_text"], end="", flush=True)
                full_text.append(data["delta_text"])
            
            if data.get("status") in ["COMPLETE", "ABORTED_RAM"]:
                if stream:
                    print("\n")
                
                status = data.get("status")
                if status == "ABORTED_RAM":
                    console.print("[red][York] Resource dictator forced unload.[/red]")
                
                duration = data.get("duration_ms", 0) / 1000
                console.print(f"[Done] {duration:.1f}s | Coherence: {data.get('coherence', 0)} | RAM peak: {data.get('ram_peak_mb', 0)}MB")
                break
            
            if time.time() - start_time > timeout:
                console.print(f"[red]Timeout after {timeout}s[/red]")
                break
    finally:
        await pubsub.unsubscribe("pr:bus:telemetry")
        await r.aclose()

@app.command()
def task(
    prompt: str,
    no_stream: bool = typer.Option(False, "--no-stream"),
    json_out: bool = typer.Option(False, "--json"),
    session: Optional[str] = typer.Option(None, "--session"),
    timeout: int = typer.Option(30, "--timeout")
):
    """Submit task to colony. Streams by default."""
    asyncio.run(run_task(prompt, not no_stream, session, timeout))

@app.command()
def nest(query: str, k: int = 8):
    """Query Nest without waking Clones."""
    cfg = load_config()
    import requests
    try:
        res = requests.post(f"{cfg['api_url']}/v1/nest/query", json={"query": query, "k": k})
        res.raise_for_status()
        data = res.json()
        for i, r in enumerate(data.get("results", []), 1):
            console.print(f"{i}. [{r['skill_type']} {r['strength']:.2f}] {r['node_id']}\n   {r['text'][:100]}...")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def dictator(action: str = "check"):
    """check|clear dictator status"""
    cfg = load_config()
    r = get_redis_sync(cfg)
    if action == "check":
        d = r.hgetall("pr:dictator")
        if not d:
            console.print("Dictator: None")
        else:
            console.print(f"Dictator: {d.get('type')} | TTL: {d.get('ttl')} | Priority: {d.get('priority')}")
    elif action == "clear":
        r.publish("pr:bus:emergency", json.dumps({"type": "CLEAR_DICTATOR"}))
        console.print("Sent clear signal to emergency bus.")

@app.command()
def sleep(force: bool = False):
    """Trigger night_phase()"""
    cfg = load_config()
    import requests
    try:
        res = requests.post(f"{cfg['api_url']}/v1/sleep", json={"force": force})
        res.raise_for_status()
        console.print(res.json())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def logs(tail: int = 50, follow: bool = False):
    """View colony logs from MongoDB"""
    cfg = load_config()
    m = get_mongo(cfg)
    logs_col = m.colony.logs
    if follow:
        console.print("[yellow]Tailing logs (Ctrl+C to stop)...[/yellow]")
        try:
            with logs_col.watch() as stream:
                for change in stream:
                    doc = change['fullDocument']
                    console.print(f"[{doc.get('timestamp')}] {doc.get('source')}: {doc.get('message')}")
        except KeyboardInterrupt:
            pass
    else:
        for doc in logs_col.find().sort("timestamp", -1).limit(tail):
            console.print(f"[{doc.get('timestamp')}] {doc.get('source')}: {doc.get('message')}")

@app.command()
def prefetch(session: Optional[str] = None):
    """Debug Antennae prefetch state"""
    cfg = load_config()
    r = get_redis_sync(cfg)
    sess = session or "default"
    data = r.zrange(f"pr:prefetch:{sess}", 0, -1, withscores=True)
    if not data:
        console.print(f"No prefetch data for {sess}")
    else:
        for crystal, score in data:
            console.print(f"{crystal}: {score}")

@app.command()
def top():
    """Launch TUI dashboard (Placeholder)"""
    console.print("[yellow]Textual TUI not implemented in this skeleton. Use 'status' or 'york --watch'.[/yellow]")

if __name__ == "__main__":
    app()
