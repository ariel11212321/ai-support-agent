from .UserQuestion import UserQuestion
from .ClassificationResult import ClassificationResult
from .SupportResponse import SupportResponse
from .EscalationInfo import EscalationInfo
from .ProcessingMetrics import ProcessingMetrics
from .ConversationContext import ConversationContext
from .Priority import Priority
from .TicketStatus import TicketStatus
from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class WorkflowState(TypedDict):
    # Core workflow data
    ticket_id: str
    question: UserQuestion
    status: TicketStatus
    priority: Priority
    
    # Classification and routing
    classification: Optional[ClassificationResult]
    confidence_threshold: float
    requires_escalation: bool
    escalation_info: Optional[EscalationInfo]
    
    # Response and processing
    response: Optional[SupportResponse]
    alternative_responses: List[SupportResponse]
    processing_metrics: ProcessingMetrics
    
    # Context and user info
    conversation_context: ConversationContext
    user_feedback: Optional[Dict[str, Any]]
    
    # Error handling and debugging
    errors: List[str]
    warnings: List[str]
    debug_info: Dict[str, Any]
    
    # Workflow control
    retry_count: int
    max_retries: int
    should_continue: bool
    next_action: Optional[str]
