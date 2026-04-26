import asyncio
import json
import psutil
from core.records import PunkRecords, DictatorProtocol

class York:
    """RAM Governor Satellite (Spec 2.3)"""
    def __init__(self, pr: PunkRecords, dp: DictatorProtocol):
        self.pr = pr
        self.dp = dp
        self.total_ram = 1200 # Boksburg 1.2GB target
        
    async def monitor(self):
        """Main loop: check RAM every 500ms"""
        while True:
            # In real Boksburg, we'd read /proc/meminfo or similar
            mem = psutil.virtual_memory()
            used_mb = mem.used / (1024 * 1024)
            pct = (used_mb / self.total_ram) * 100
            
            # Write to Redis for others to read
            await self.pr.r.set("pr:york:ram", int(used_mb))
            
            if pct > 92:
                # Immediate unload signal
                await self.pr.r.publish("pr:bus:emergency", json.dumps({
                    "type": "Resource",
                    "action": "UNLOAD",
                    "severity": "CRITICAL"
                }))
                await self.dp.raise_emergency("Resource", ttl=3)
            elif pct > 85:
                # Block new loads
                await self.dp.raise_emergency("Resource", ttl=1)
                
            await asyncio.sleep(0.5)

    async def get_ballot(self):
        """York ranks Clones by RAM cost (Spec 2.3)"""
        # Voice (300MB) < Chat (300MB) < Code (650MB)
        return ["voice_worker", "chat_worker", "code_worker"]
