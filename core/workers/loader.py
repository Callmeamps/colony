import json
import time
from typing import Optional
from core.records import PunkRecords

class Scout:
    """Spec 4.1: Urgency + Direct Answering"""
    def __init__(self, pr: PunkRecords):
        self.pr = pr

    async def classify(self, prompt: str) -> dict:
        """Score urgency 0-1 and check for direct Nest answer"""
        # In full impl: TinyLlama/Phi inference
        urgency = 0.5 
        return {
            "urgency": urgency,
            "can_answer_direct": False,
            "answer": None
        }

class WorkerLoader:
    """Spec 4.2: RAM-enforced model loading (Bonsai 1-bit)"""
    def __init__(self, pr: PunkRecords):
        self.pr = pr
        self.bonsai_ram_mb = 1180 # 1.15GB + overhead

    async def load_clone(self, clone_id: str):
        # York 85% block logic for 1.2GB system
        # Since Bonsai is 1.15GB, York will likely block if anything else is running.
        # We enforce strict baseline for Bonsai.
        ram = int(await self.pr.r.get("pr:york:ram") or 0)
        
        if (ram + self.bonsai_ram_mb) / 1200 > 0.98:
            await self.pr.r.publish("pr:bus:emergency", json.dumps({
                "type": "Resource", "status": "BLOCKED", "reason": "Bonsai requires near-total RAM"
            }))
            raise Exception("York: Insufficient RAM for Bonsai-8B")

        print(f"[Loader] Loading Bonsai-8B ({clone_id} mode)...")
        await asyncio.sleep(1.2) 
        await self.pr.r.set("pr:current_load", clone_id)

    async def unload_all(self):
        print("[Loader] Unloading all clones...")
        await self.pr.r.delete("pr:current_load")
        # Ensure RAM returns to baseline ~270MB
