import json
import uuid
import asyncio
from typing import List, Dict, Optional
from rlms import RLM
from core.records import PunkRecords
from core.workers.repl import NestREPL

class Council:
    """
    Deep Module for routing and election management.
    Now supports Recursive Language Model (RLM) dispatch.
    """
    def __init__(self, pr: Optional[PunkRecords] = None):
        self.pr = pr or PunkRecords()
        self.repl = NestREPL()
        self.rlm = RLM(model="bonsai-1.7b", context_window=512)
        
    async def route(self, task_data: Dict) -> str:
        """
        Deep Interface: route task to the best Clone.
        Uses RLM loop if 'recursive' flag is set.
        """
        recursive = task_data.get("recursive", True)
        
        if recursive:
            return await self._route_recursive(task_data)
        
        return await self._route_standard(task_data)

    async def _route_recursive(self, task_data: Dict) -> str:
        """
        RLM Implementation: The Council becomes the orchestrator.
        """
        print(f"[Council] Starting RLM dispatch for {task_data.get('event_id')}")
        
        # Use RLM to decompose task and determine routing
        prompt = f"Decompose task: {json.dumps(task_data)}"
        response = await self.rlm.generate(prompt, max_tokens=256)
        
        # Parse RLM response for sub-tasks
        try:
            sub_tasks = json.loads(response)
            results = []
            for sub in sub_tasks.get("subtasks", []):
                result = await self._route_standard(sub)
                results.append(result)
            winner = results[0] if results else "chat_worker"
        except Exception as e:
            print(f"[Council] RLM parse error: {e}, falling back")
            winner = await self._route_standard(task_data)
        
        await self.pr.set_winner(winner)
        return winner

    async def _route_standard(self, task_data: Dict) -> str:
        event_id = task_data.get("event_id") or f"route-{uuid.uuid4().hex[:8]}"
        await self._signal_satellites(event_id, task_data)
        winner = await self._run_election(event_id)
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
