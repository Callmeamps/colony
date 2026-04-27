import json
from typing import Optional, Dict

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class PunkRecords:
    """Redis Layer for Council state and routing"""
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.r = redis.from_url(url, decode_responses=True)
        
    async def set_winner(self, clone_id: str):
        """Single-writer: Only Council calls this"""
        await self.r.set("pr:winner", clone_id)
        
    async def get_winner(self) -> Optional[str]:
        return await self.r.get("pr:winner")

    async def cast_ballot(self, satellite: str, ranking: list):
        """Satellites post their preferred Clones"""
        await self.r.set(f"pr:ballot:{satellite}", json.dumps(ranking), ex=10)

    async def get_all_ballots(self) -> Dict[str, list]:
        keys = await self.r.keys("pr:ballot:*")
        ballots = {}
        for k in keys:
            name = k.split(":")[-1]
            val = await self.r.get(k)
            if val:
                ballots[name] = json.loads(val)
        return ballots

class DictatorProtocol:
    # Spec 2.5: Hardcoded priority
    PRIORITY = {
        "Trauma": 0,
        "Resource": 1,
        "Coherence": 2,
        "Deadlock": 3
    }
    
    def __init__(self, pr: PunkRecords):
        self.pr = pr

    async def raise_emergency(self, e_type: str, ttl: int = 3):
        """Handle emergency signals with priority override"""
        current = await self.pr.r.hgetall("pr:dictator")
        new_pri = self.PRIORITY.get(e_type, 99)
        
        if not current or new_pri < int(current.get("priority", 100)):
            await self.pr.r.hset("pr:dictator", mapping={
                "type": e_type,
                "priority": new_pri,
                "ttl": ttl
            })
            return True
        return False

    async def decrement_ttl(self):
        ttl = await self.pr.r.hincrby("pr:dictator", "ttl", -1)
        if ttl <= 0:
            await self.pr.r.delete("pr:dictator")
