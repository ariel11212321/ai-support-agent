import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class ConversationContext:

    user_id: Optional[str] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    previous_interactions: List[Dict[str, Any]] = field(default_factory=list)
    user_sentiment: Optional[str] = None
    user_language: str = "en"
    time_zone: Optional[str] = None
    customer_tier: str = "standard"