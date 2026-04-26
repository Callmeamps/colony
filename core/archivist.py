import math
import asyncio
from datetime import datetime, timedelta
from typing import List
from models.nest_node import NestNode
from core.nest import add_many # In reality, we'd use a direct DB connection for performance

# Hardcoded Decays from Spec 1.2
TAU = {
    "LIQUID": 24.0,   # hours
    "ONE_OFF": 1.0,
    "RUSTY": 168.0,
    "STALE": 72.0,
}

class Archivist:
    def __init__(self, db_path: str = "nest/meta.db"):
        self.db_path = db_path

    async def run_decay_pass(self):
        """Hourly forgetting curve. Single-writer logic."""
        # Note: In a real implementation, we would query the SQLite nest_meta table directly.
        # This skeleton demonstrates the logic.
        
        now = datetime.utcnow()
        # Mock: nodes = await self.get_decayable_nodes()
        nodes: List[Any] = [] 
        
        for node in nodes:
            if node.skill_type in ["FUNDAMENTAL", "INNATE", "CRYSTALLISED"]:
                continue
                
            delta_t = (now - node.last_access).total_seconds() / 3600.0
            tau = TAU.get(node.skill_type, 24.0)
            
            # New Strength = strength * exp(-Δt / τ)
            new_strength = node.strength * math.exp(-delta_t / tau)
            
            # Eviction check
            if new_strength <= 0.01:
                # await delete_from_nest(node.node_id)
                continue
            
            # Promotion check: CRYSTALLISED promotion logic
            # if hits >= 20 and strength >= 0.85 for 7 days...
            
            # Update node.strength = new_strength
            # await self.update_strength(node.node_id, new_strength)

    async def update_strength(self, node_id: str, delta: float):
        """Only entry point for strength modification (δ * hit)"""
        # Enforce single-writer by checking caller or via specific API
        pass

async def nightly_cleanup():
    """Triggered by Scheduler"""
    archivist = Archivist()
    await archivist.run_decay_pass()
    # verify York RAM < 70% before proceeding with night_phase()
