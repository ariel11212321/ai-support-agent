from dataclasses import dataclass, field
from .SupportCategory import SupportCategory
from typing import Optional, Dict, Any, List

@dataclass
class ClassificationResult:
    category: SupportCategory
    confidence: float
    processing_time_ms: float = 0.0
    worker_id: Optional[int] = None