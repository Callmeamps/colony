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
    """Spec 4.2: RAM-enforced model loading"""
    def __init__(self, pr: PunkRecords):
        self.pr = pr

    async def load_clone(self, clone_id: str):
        ram = int(await self.pr.r.get("pr:york:ram") or 0)
        
        # York 85% block
        if ram / 1200 > 0.85:
            await self.pr.r.publish("pr:bus:emergency", json.dumps({
                "type": "Resource", "status": "BLOCKED"
            }))
            raise Exception("York: RAM > 85%, load blocked")

        print(f"[Loader] Loading {clone_id}...")
        # Simulating INT4 GGUF load
        await asyncio.sleep(1.2) 
        await self.pr.r.set("pr:current_load", clone_id)

    async def unload_all(self):
        print("[Loader] Unloading all clones...")
        await self.pr.r.delete("pr:current_load")
        # Ensure RAM returns to baseline ~270MB
