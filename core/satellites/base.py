from abc import ABC, abstractmethod
from typing import List, Dict

class Satellite(ABC):
    """
    Formal Seam for Satellite modules.
    All satellites must implement vote() to participate in Shaka elections.
    """
    
    @abstractmethod
    async def vote(self, task_data: Dict) -> List[str]:
        """
        Produce a Ballot (ranked list of Clones).
        task_data contains context required for decision making.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the satellite."""
        pass
