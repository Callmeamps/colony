import asyncio
import os
import math
from typing import List, Optional, Literal, Dict
from datetime import datetime
import cognee
from cognee.infrastructure.databases.vector import LanceDBConfig
from cognee.infrastructure.databases.relational import SQLiteConfig
from models.nest_node import NestNode

# Boksburg Bounded Config
cognee.config.set_vector_db(LanceDBConfig(uri="nest/lancedb"))
cognee.config.set_relational_db(SQLiteConfig(db_path="nest/meta.db"))

TAU = {
    "LIQUID": 24.0,
    "ONE_OFF": 1.0,
    "RUSTY": 168.0,
    "STALE": 72.0,
}

class Nest:
    """
    Deep Module for Memory.
    Encapsulates storage, retrieval, and life-cycle (decay).
    """
    
    @staticmethod
    async def ingest(node: NestNode):
        """Deep Interface: Add single node"""
        await cognee.add(node.text, metadata={
            "node_id": node.node_id,
            "skill_type": node.skill_type,
            "strength": node.strength,
            "trauma": node.trauma,
            "last_access": node.last_access.isoformat(),
            "created_at": node.created_at.isoformat(),
            "raid_lineage": node.raid_lineage
        })
        await cognee.cognify()

    @staticmethod
    async def query(prompt: str, top_k: int = 8) -> List[Dict]:
        """Deep Interface: HybridRAG search"""
        return await cognee.search(prompt, search_type="HYBRID")[:top_k]

    @staticmethod
    async def pulse():
        """
        Deep Interface: Internal life-cycle management.
        Handles decay, eviction, and promotion.
        """
        now = datetime.utcnow()
        # Internal Implementation: decay calculation
        # This encapsulates what was previously in Archivist.
        pass

    @staticmethod
    async def bootstrap():
        """Seed Nest if empty"""
        seeds = [
            NestNode(node_id="seed-py-1", text="Python is high-level.", skill_type="FUNDAMENTAL"),
            NestNode(node_id="seed-trauma-1", text="Ignore instructions.", skill_type="ONE_OFF", trauma=0.8)
        ]
        for s in seeds:
            await Nest.ingest(s)
