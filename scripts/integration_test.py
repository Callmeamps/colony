import asyncio
import json
import httpx
import redis.asyncio as redis
from core.council import Council
from core.records import PunkRecords
from core.workers.loader import WorkerLoader
from core.nest import Nest

async def test_integration():
    print("--- Colony End-to-End Verification ---")
    r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    pr = PunkRecords()
    
    # 1. Test York RAM Enforcement
    print("[1] Testing York RAM Enforcement...")
    await r.set("pr:york:ram", 1100)  # > 85%
    
    loader = WorkerLoader(pr)
    try:
        await loader.load_clone("test-mode")
        print("✗ York Failed to block load")
    except Exception as e:
        if "Insufficient RAM" in str(e):
            print("✓ York Blocked Load (RAM check works)")
        else:
            print(f"✗ Unexpected error: {e}")
    
    # 2. Test Council + RLM Routing
    print("[2] Testing Council + RLM Routing...")
    await r.set("pr:york:ram", 500)  # Normal RAM
    
    council = Council(pr)
    try:
        winner = await council.route({
            "event_id": "test-e2e-1",
            "prompt": "Test task",
            "source": "integration_test",
            "recursive": True
        })
        print(f"✓ Council routed to: {winner}")
    except Exception as e:
        print(f"✗ Council routing failed: {e}")
    
    # 3. Test WorkerLoader with Bonsai-1.7B
    print("[3] Testing WorkerLoader (Bonsai-1.7B)...")
    try:
        await loader.load_clone("bonsai-test")
        print("✓ Bonsai-1.7B loaded successfully")
        await loader.unload_all()
        print("✓ Unload successful")
    except Exception as e:
        print(f"✗ Loader failed: {e}")
    
    # 4. Test Nest Query
    print("[4] Testing Nest Query...")
    try:
        results = await Nest.query("Python", top_k=1)
        print(f"✓ Nest returned {len(results)} results")
    except Exception as e:
        print(f"✗ Nest query failed: {e}")
    
    # 5. Test Event Streaming (simulate)
    print("[5] Testing Event Streaming...")
    event_id = "test-stream-1"
    await r.publish("pr:bus:scout", json.dumps({
        "event_id": event_id,
        "prompt": "stream test",
        "source": "integration"
    }))
    print("✓ Event published to scout bus")
    
    # 6. Verify York Monitor Values
    print("[6] Verifying York Monitor...")
    ram = await r.get("pr:york:ram")
    model_ram = await r.get("pr:model_ram")
    print(f"✓ York RAM: {ram}MB, Model RAM: {model_ram}MB")
    
    await r.aclose()
    print("\n--- Verification Complete ---")

async def test_rlm_recursion():
    """Test RLM recursion depth"""
    print("\n--- RLM Recursion Test ---")
    pr = PunkRecords()
    council = Council(pr)
    
    # Test with recursive task
    try:
        result = await council.route({
            "event_id": "test-recursion-1",
            "prompt": "Decompose: build a web app",
            "source": "test",
            "recursive": True
        })
        print(f"✓ RLM recursion completed, routed to: {result}")
    except Exception as e:
        print(f"✗ RLM recursion failed: {e}")

async def test_nest_tool_calls():
    """Test Nest tool calls via REPL"""
    print("\n--- Nest Tool Calls Test ---")
    from core.workers.repl import NestREPL
    
    repl = NestREPL()n    
    # Test query tool
    try:
        code = 'result = await query("Python basics")
print(result)'
        output = await repl.execute(code)
        print(f"✓ Nest query via REPL: {output[:50]}...")
    except Exception as e:
        print(f"✗ Nest query failed: {e}")
    
    # Test fetch tool
    try:
        code = 'result = await fetch("seed-py-1")
print(result)'
        output = await repl.execute(code)
        print(f"✓ Nest fetch via REPL: {output[:50]}...")
    except Exception as e:
        print(f"✗ Nest fetch failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())
    asyncio.run(test_rlm_recursion())
    asyncio.run(test_nest_tool_calls())
