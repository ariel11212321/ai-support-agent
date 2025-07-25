from dataclasses import dataclass
from .EscalationReason import EscalationReason
from typing import Optional

@dataclass
class EscalationInfo:
    """Information about escalation"""
    reason: EscalationReason
    suggested_department: str
    human_agent_required: bool = False
    urgency_score: float = 0.0
    estimated_resolution_time: Optional[str] = None