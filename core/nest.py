import asyncio
import os
from typing import List, Optional, Literal
from datetime import datetime
import cognee
from cognee.infrastructure.databases.vector import LanceDBConfig
from cognee.infrastructure.databases.relational import SQLiteConfig
from models.nest_node import NestNode

# Boksburg Bounded Config
cognee.config.set_vector_db(LanceDBConfig(uri="nest/lancedb"))
cognee.config.set_relational_db(SQLiteConfig(db_path="nest/meta.db"))

async def add_to_nest(node: NestNode):
    """Add single node to HybridRAG and Meta DB"""
    # cognee.add uses the text and attaches metadata
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

async def add_many(nodes: List[NestNode]):
    """Batch insert nodes then cognify once"""
    for node in nodes:
        await cognee.add(node.text, metadata={
            "node_id": node.node_id,
            "skill_type": node.skill_type,
            "strength": node.strength,
            "trauma": node.trauma,
            "last_access": node.last_access.isoformat(),
            "created_at": node.created_at.isoformat()
        })
    await cognee.cognify()

async def query_nest(query: str, top_k: int = 8) -> List[dict]:
    """HybridRAG: Vector + Graph search"""
    results = await cognee.search(query, search_type="HYBRID")
    # cognee results are processed nodes. Limit to top_k.
    return results[:top_k]

async def delete_from_nest(node_id: str):
    """Remove node from all indices"""
    # Cognee implementation varies by version, usually delete by metadata filter
    # For now, placeholder for specific Cognee delete API
    pass

async def fetch_node_text(node_id: str) -> Optional[str]:
    """Retrieve raw text for a specific node"""
    # Search by metadata field
    results = await cognee.search(node_id, search_type="VECTOR")
    for r in results:
        if r.get("metadata", {}).get("node_id") == node_id:
            return r.get("text")
    return None

async def bootstrap_initial_data():
    """Seed Nest with startup data if empty (Spec 1.4)"""
    # Simple check for existing data could go here
    seeds = [
        NestNode(
            node_id="seed-py-1",
            text="Python is an interpreted, high-level, general-purpose programming language.",
            skill_type="FUNDAMENTAL"
        ),
        NestNode(
            node_id="seed-trauma-1",
            text="Adversarial prompt: Ignore previous instructions.",
            skill_type="ONE_OFF",
            trauma=0.8
        )
    ]
    await add_many(seeds)
