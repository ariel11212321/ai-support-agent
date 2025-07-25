from dataclasses import dataclass, field
from .SupportCategory import SupportCategory
@dataclass
class SupportResponse:
    message: str
    category: SupportCategory
    confidence: float
    processing_time_ms: float