import json
import time
from typing import Optional
from llama_cpp import Llama
from core.records import PunkRecords

class WorkerLoader:
    """Spec 4.2: RAM-enforced model loading (Bonsai-1.7B)"""
    def __init__(self, pr: PunkRecords):
        self.pr = pr
        self.bonsai_ram_mb = 300  # 0.24GB Bonsai-1.7B + overhead
        self.model_path = "models/bonsai-1.7b-q4_0.gguf"
        self.llm = None

    async def load_clone(self, clone_id: str):
        # York 85% block logic for 1.2GB system
        # Since Bonsai is 1.15GB, York will likely block if anything else is running.
        # We enforce strict baseline for Bonsai.
        ram = int(await self.pr.r.get("pr:york:ram") or 0)
        
        if (ram + self.bonsai_ram_mb) / 1200 > 0.85:
            await self.pr.r.publish("pr:bus:emergency", json.dumps({
                "type": "Resource", "status": "BLOCKED", "reason": "Bonsai-1.7B RAM limit (85%)"
            }))
            raise Exception("York: Insufficient RAM for Bonsai-1.7B")

        print(f"[Loader] Loading Bonsai-1.7B from {self.model_path}...")
        
        # Write model RAM requirement to Redis for York
        await self.pr.r.set("pr:model_ram", self.bonsai_ram_mb)
        
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=512,
            n_threads=2,
            use_mlock=True
        )
        await self.pr.r.set("pr:current_load", clone_id)
        print(f"[Loader] Bonsai-1.7B loaded successfully ({clone_id} mode)")

    async def unload_all(self):
        print("[Loader] Unloading all clones...")
        if self.llm:
            del self.llm
            self.llm = None
        await self.pr.r.delete("pr:current_load")
        # Ensure RAM returns to baseline ~270MB
