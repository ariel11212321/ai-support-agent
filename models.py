from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class SupportCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"

@dataclass
class UserQuestion:
    text: str
    metadata: Dict[str, Any] = None

@dataclass
class ClassificationResult:
    category: SupportCategory
    confidence: float
    processing_time_ms: float = 0.0
    worker_id: Optional[int] = None

@dataclass
class SupportResponse:
    message: str
    category: SupportCategory
    confidence: float
    processing_time_ms: float

@dataclass
class GraphState:
    question: UserQuestion
    classification: Optional[ClassificationResult] = None
    response: Optional[SupportResponse] = None
    error: Optional[str] = None