from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, Any

@dataclass
class NestNode:
    node_id: str
    text: str
    skill_type: Literal["LIQUID", "FUNDAMENTAL", "INNATE", "ONE_OFF", "RUSTY", "STALE", "CRYSTALLISED"]
    strength: float = 1.0
    trauma: float = 0.0
    last_access: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    raid_lineage: Optional[str] = None
    metadata: dict = field(default_factory=dict)
