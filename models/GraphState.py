from dataclasses import dataclass, field
from .UserQuestion import UserQuestion
from typing import Optional, Dict, Any, List
from .SupportResponse import SupportResponse
from .ClassificationResult import ClassificationResult

@dataclass
class GraphState:

    question: UserQuestion
    classification: Optional[ClassificationResult] = None
    response: Optional[SupportResponse] = None
    error: Optional[str] = None
    
    ticket_id: str = ""
    status: str = "new"
    priority: str = "medium"
    requires_escalation: bool = False
    escalation_info: Optional[Dict[str, Any]] = None
    processing_metrics: Optional[Dict[str, Any]] = None
    conversation_context: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_workflow_result(cls, result: Dict[str, Any]) -> 'GraphState':
        

        main_error = result.get("errors", [])
        error_str = main_error[0] if main_error else None
        
        metrics = result.get("processing_metrics")
        metrics_dict = None
        if metrics:
            metrics_dict = {
                "total_time_ms": getattr(metrics, 'total_processing_time_ms', 0),
                "classification_time_ms": getattr(metrics, 'classification_time_ms', 0),
                "response_time_ms": getattr(metrics, 'response_generation_time_ms', 0),
                "api_calls": getattr(metrics, 'api_calls_made', 0)
            }
        
        escalation = result.get("escalation_info")
        escalation_dict = None
        if escalation:
            escalation_dict = {
                "reason": getattr(escalation, 'reason', '').value if hasattr(getattr(escalation, 'reason', ''), 'value') else str(getattr(escalation, 'reason', '')),
                "department": getattr(escalation, 'suggested_department', ''),
                "human_required": getattr(escalation, 'human_agent_required', False)
            }
        
        context = result.get("conversation_context")
        context_dict = None
        if context:
            context_dict = {
                "user_id": getattr(context, 'user_id', None),
                "session_id": getattr(context, 'session_id', ''),
                "sentiment": getattr(context, 'user_sentiment', None),
                "customer_tier": getattr(context, 'customer_tier', 'standard')
            }
        
        return cls(
            question=result["question"],
            classification=result.get("classification"),
            response=result.get("response"),
            error=error_str,
            ticket_id=result.get("ticket_id", ""),
            status=result.get("status", "unknown").value if hasattr(result.get("status", "unknown"), 'value') else str(result.get("status", "unknown")),
            priority=result.get("priority", "medium").value if hasattr(result.get("priority", "medium"), 'value') else str(result.get("priority", "medium")),
            requires_escalation=result.get("requires_escalation", False),
            escalation_info=escalation_dict,
            processing_metrics=metrics_dict,
            conversation_context=context_dict,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            debug_info=result.get("debug_info", {})
        )