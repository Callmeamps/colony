import json
import uuid
import asyncio
from typing import List, Dict, Optional
from core.records import PunkRecords

class Council:
    """
    Deep Module for routing and election management.
    Hides Redis internals and election orchestration.
    """
    def __init__(self, pr: Optional[PunkRecords] = None):
        self.pr = pr or PunkRecords()
        
    async def route(self, task_data: Dict) -> str:
        """
        Deep Interface: route task to the best Clone.
        Hides the full election implementation.
        """
        event_id = task_data.get("event_id") or f"route-{uuid.uuid4().hex[:8]}"
        
        # 1. Trigger satellites (Internal Implementation)
        await self._signal_satellites(event_id, task_data)
        
        # 2. Run Shaka Election (Internal Implementation)
        winner = await self._run_election(event_id)
        
        # 3. Lock winner
        await self.pr.set_winner(winner)
        return winner

    async def _signal_satellites(self, event_id: str, task_data: Dict):
        """Internal: publish to scout bus for satellites to respond"""
        msg = {**task_data, "event_id": event_id}
        await self.pr.r.publish("pr:bus:scout", json.dumps(msg))

    async def _run_election(self, event_id: str) -> str:
        """Internal: collect ballots and run STV"""
        # Short wait for satellites
        await asyncio.sleep(0.1) 
        
        ballots = await self.pr.get_all_ballots()
        if not ballots:
            return "chat_worker" # Default fallback
            
        votes = {}
        for satellite, ranking in ballots.items():
            first_choice = ranking[0]
            votes[first_choice] = votes.get(first_choice, 0) + 1
            
        return max(votes, key=votes.get)
