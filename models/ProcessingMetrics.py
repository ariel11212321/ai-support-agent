from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ProcessingMetrics:
    """Detailed processing metrics"""
    start_time: datetime = field(default_factory=datetime.now)
    classification_time_ms: float = 0.0
    routing_time_ms: float = 0.0
    response_generation_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    retry_count: int = 0
    api_calls_made: int = 0
    tokens_used: int = 0