"""
AI Support Agent - Data Models
Clean data structures using Python dataclasses
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class SupportCategory(str, Enum):
    """Support categories for question classification"""
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


class Priority(str, Enum):
    """Priority levels for support tickets"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class UserQuestion:
    """Represents a user's support question"""
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and clean question text"""
        self.text = self.text.strip()
        if not self.text:
            raise ValueError("Question text cannot be empty")


@dataclass
class ClassificationResult:
    """Results from question classification"""
    category: SupportCategory
    confidence: float
    reasoning: str
    processing_time_ms: float = 0.0
    features_detected: List[str] = field(default_factory=list)
    worker_id: Optional[int] = None
    
    def __post_init__(self):
        """Validate confidence score"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class SupportResponse:
    """Complete support response with actions and metadata"""
    category: SupportCategory
    response: str
    suggested_actions: List[str] = field(default_factory=list)
    escalation_needed: bool = False
    priority: Priority = Priority.MEDIUM
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_action(self, action: str) -> None:
        """Add a suggested action to the response"""
        if action not in self.suggested_actions:
            self.suggested_actions.append(action)
    
    def set_urgent(self) -> None:
        """Mark response as urgent requiring escalation"""
        self.escalation_needed = True
        self.priority = Priority.URGENT


@dataclass
class ConversationHistory:
    """Tracks conversation between user and agent"""
    session_id: str
    questions: List[UserQuestion] = field(default_factory=list)
    responses: List[SupportResponse] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_exchange(self, question: UserQuestion, response: SupportResponse) -> None:
        """Add a question-response pair to conversation"""
        self.questions.append(question)
        self.responses.append(response)
        self.updated_at = datetime.now()
    
    @property
    def total_exchanges(self) -> int:
        """Get total number of question-response exchanges"""
        return min(len(self.questions), len(self.responses))


@dataclass
class AnalyticsData:
    """Analytics and performance metrics"""
    total_questions: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0
    average_processing_time: float = 0.0
    accuracy_rate: float = 0.0
    cache_hit_rate: float = 0.0
    worker_utilization: Dict[int, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def update_metrics(self, classification: ClassificationResult, response: SupportResponse) -> None:
        """Update analytics with new classification and response data"""
        self.total_questions += 1
        
        # Update category counts
        category = classification.category.value
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        
        # Update confidence (running average)
        new_confidence = classification.confidence
        self.average_confidence = (
            (self.average_confidence * (self.total_questions - 1) + new_confidence) 
            / self.total_questions
        )
        
        # Update processing time (running average)
        new_time = classification.processing_time_ms
        self.average_processing_time = (
            (self.average_processing_time * (self.total_questions - 1) + new_time) 
            / self.total_questions
        )
        
        # Update worker utilization
        if classification.worker_id:
            worker_count = self.worker_utilization.get(classification.worker_id, 0)
            self.worker_utilization[classification.worker_id] = worker_count + 1
    
    def get_top_category(self) -> Optional[str]:
        """Get the most common category"""
        if not self.category_counts:
            return None
        return max(self.category_counts, key=self.category_counts.get)


@dataclass
class SystemMetrics:
    """System performance and health metrics"""
    active_workers: int = 0
    queue_size: int = 0
    cache_size: int = 0
    memory_usage_mb: float = 0.0
    uptime_seconds: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_timestamp(self) -> None:
        """Update the last updated timestamp"""
        self.last_updated = datetime.now()


@dataclass
class CacheEntry:
    """Cache entry for storing question-response pairs"""
    question_hash: str
    question_text: str
    response: SupportResponse
    hit_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def access(self) -> None:
        """Mark cache entry as accessed"""
        self.hit_count += 1
        self.last_accessed = datetime.now()


@dataclass
class WorkerTask:
    """Task for worker thread processing"""
    task_id: str
    question: UserQuestion
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[int] = None
    result: Optional[SupportResponse] = None
    error: Optional[str] = None
    
    def start_processing(self, worker_id: int) -> None:
        """Mark task as started by worker"""
        self.started_at = datetime.now()
        self.worker_id = worker_id
    
    def complete_processing(self, result: SupportResponse) -> None:
        """Mark task as completed with result"""
        self.completed_at = datetime.now()
        self.result = result
    
    def fail_processing(self, error: str) -> None:
        """Mark task as failed with error"""
        self.completed_at = datetime.now()
        self.error = error
    
    @property
    def processing_time_ms(self) -> float:
        """Get processing time in milliseconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return 0.0
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed (success or failure)"""
        return self.completed_at is not None