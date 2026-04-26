import asyncio
import json
import httpx
import redis.asyncio as redis

async def test_integration():
    print("--- Colony Integration Test ---")
    r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    # 1. York RAM Enforcement
    print("[1] Testing York RAM Enforcement...")
    await r.set("pr:york:ram", 1100) # > 85%
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:7777/v1/chat/completions", json={
                "model": "colony-auto",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False
            })
            if res.status_code == 503:
                print("✓ York Blocked Load (503)")
            else:
                print(f"✗ York Failed to block (Status: {res.status_code})")
        except Exception as e:
            print(f"✗ Request failed: {e}")

    # 2. Nest Query
    print("[2] Testing Nest Query...")
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:7777/v1/nest/query", json={"query": "Python", "k": 1})
        if res.status_code == 200 and "results" in res.json():
            print("✓ Nest Query Returned Results")
        else:
            print("✗ Nest Query Failed")

    # 3. Sleep Trigger
    print("[3] Testing Sleep Trigger...")
    await r.set("pr:york:ram", 500) # < 70%
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:7777/v1/sleep", json={"force": False})
        if res.json().get("status") == "scheduled":
            print("✓ Sleep Scheduled")
        else:
            print("✗ Sleep Rejected")

    await r.aclose()
    print("--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_integration())
