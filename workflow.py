from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any, Literal, Annotated
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from models import UserQuestion, ClassificationResult, SupportResponse, GraphState
from classifier import QuestionClassifier
from handlers import SupportHandler
from models import WorkflowState, TicketStatus, Priority, EscalationInfo, EscalationReason, ProcessingMetrics, ConversationContext



class SupportWorkflow:
    def __init__(self):
        print("🚀 Initializing Advanced AI Support Workflow...")
        self.classifier = QuestionClassifier()
        self.handler = SupportHandler()
        
        # Configuration
        self.confidence_threshold = 0.75
        self.max_retries = 3
        self.escalation_keywords = [
            "speak to manager", "human agent", "cancel subscription",
            "legal action", "complaint", "terrible", "worst"
        ]
        
        self.workflow = self._build_workflow()
        print("✅ Advanced workflow ready!")
    
    def _build_workflow(self) -> StateGraph:
        """Build complex workflow with multiple paths and decision points"""
        workflow = StateGraph(WorkflowState)
        
        # Add all nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment_node)
        workflow.add_node("classify_question", self._classify_question_node)
        workflow.add_node("check_confidence", self._check_confidence_node)
        workflow.add_node("route_to_specialist", self._route_to_specialist_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("escalate_to_human", self._escalate_to_human_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Define workflow edges with conditional routing
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "validate_input")
        workflow.add_conditional_edges(
            "validate_input",
            self._should_continue_after_validation,
            {
                "continue": "analyze_sentiment",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("analyze_sentiment", "classify_question")
        workflow.add_conditional_edges(
            "classify_question",
            self._should_continue_after_classification,
            {
                "continue": "check_confidence",
                "retry": "classify_question",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "check_confidence",
            self._confidence_routing,
            {
                "high_confidence": "route_to_specialist",
                "low_confidence": "escalate_to_human",
                "needs_human": "escalate_to_human"
            }
        )
        
        workflow.add_edge("route_to_specialist", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self._should_continue_after_response,
            {
                "continue": "quality_check",
                "retry": "generate_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_check_routing,
            {
                "approved": "finalize_response",
                "needs_improvement": "generate_response",
                "escalate": "escalate_to_human"
            }
        )
        
        workflow.add_edge("escalate_to_human", "finalize_response")
        workflow.add_edge("finalize_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _initialize_node(self, state: WorkflowState) -> WorkflowState:
        """Initialize ticket and workflow state"""
        print("🎯 Initializing support ticket...")
        
        state["ticket_id"] = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        state["status"] = TicketStatus.NEW
        state["priority"] = Priority.MEDIUM
        state["confidence_threshold"] = self.confidence_threshold
        state["requires_escalation"] = False
        state["alternative_responses"] = []
        state["errors"] = []
        state["warnings"] = []
        state["debug_info"] = {}
        state["retry_count"] = 0
        state["max_retries"] = self.max_retries
        state["should_continue"] = True
        
        # Initialize metrics
        state["processing_metrics"] = ProcessingMetrics()
        
        # Initialize conversation context
        if "conversation_context" not in state:
            state["conversation_context"] = ConversationContext()
        
        print(f"📋 Ticket {state['ticket_id']} initialized")
        return state
    
    def _validate_input_node(self, state: WorkflowState) -> WorkflowState:
        """Validate and sanitize input with enhanced checks"""
        print("🔍 Validating input...")
        
        question = state["question"]
        
        try:
            # Basic validation
            if not question.text or len(question.text.strip()) < 3:
                state["errors"].append("Question too short")
                state["should_continue"] = False
                return state
            
            # Check for escalation keywords
            text_lower = question.text.lower()
            escalation_detected = any(keyword in text_lower for keyword in self.escalation_keywords)
            
            if escalation_detected:
                state["requires_escalation"] = True
                state["priority"] = Priority.HIGH
                state["escalation_info"] = EscalationInfo(
                    reason=EscalationReason.MANUAL_REQUEST,
                    suggested_department="customer_relations",
                    human_agent_required=True
                )
                state["warnings"].append("Escalation keywords detected")
            
            # Set priority based on urgency indicators
            if any(word in text_lower for word in ["urgent", "emergency", "asap", "immediately"]):
                state["priority"] = Priority.HIGH
            elif any(word in text_lower for word in ["soon", "quick", "fast"]):
                state["priority"] = Priority.MEDIUM
            
            state["status"] = TicketStatus.CLASSIFIED
            print(f"✅ Input validated - Priority: {state['priority'].value}")
            
        except Exception as e:
            state["errors"].append(f"Validation error: {str(e)}")
            state["should_continue"] = False
        
        return state
    
    def _analyze_sentiment_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze user sentiment for better routing"""
        print("😊 Analyzing sentiment...")
        
        try:
            # Simple sentiment analysis (in real implementation, use proper sentiment model)
            text = state["question"].text.lower()
            
            negative_words = ["angry", "frustrated", "terrible", "awful", "hate", "worst", "horrible"]
            positive_words = ["great", "excellent", "love", "amazing", "wonderful", "perfect"]
            
            negative_count = sum(1 for word in negative_words if word in text)
            positive_count = sum(1 for word in positive_words if word in text)
            
            if negative_count > positive_count:
                sentiment = "negative"
                if negative_count >= 2:  # Multiple negative words
                    state["priority"] = Priority.HIGH
                    state["requires_escalation"] = True
                    state["escalation_info"] = EscalationInfo(
                        reason=EscalationReason.SENTIMENT_NEGATIVE,
                        suggested_department="customer_relations",
                        urgency_score=0.8
                    )
            elif positive_count > negative_count:
                sentiment = "positive"
            else:
                sentiment = "neutral"
            
            state["conversation_context"].user_sentiment = sentiment
            state["debug_info"]["sentiment_analysis"] = {
                "sentiment": sentiment,
                "negative_words_found": negative_count,
                "positive_words_found": positive_count
            }
            
            print(f"😊 Sentiment: {sentiment}")
            
        except Exception as e:
            state["warnings"].append(f"Sentiment analysis failed: {str(e)}")
        
        return state
    
    def _classify_question_node(self, state: WorkflowState) -> WorkflowState:
        """Enhanced classification with retry logic"""
        print("🧠 Classifying question...")
        
        try:
            start_time = datetime.now()
            classification = self.classifier.classify(state["question"])
            end_time = datetime.now()
            
            state["classification"] = classification
            state["processing_metrics"].classification_time_ms = (end_time - start_time).total_seconds() * 1000
            state["processing_metrics"].api_calls_made += 1
            
            print(f"📂 Category: {classification.category.value} ({classification.confidence:.1%})")
            
            # Store debug info
            state["debug_info"]["classification"] = {
                "category": classification.category.value,
                "confidence": classification.confidence,
                "processing_time_ms": state["processing_metrics"].classification_time_ms
            }
            
        except Exception as e:
            state["errors"].append(f"Classification error: {str(e)}")
            state["retry_count"] += 1
        
        return state
    
    def _check_confidence_node(self, state: WorkflowState) -> WorkflowState:
        """Check classification confidence and determine routing"""
        print("🎯 Checking confidence...")
        
        classification = state.get("classification")
        if not classification:
            state["requires_escalation"] = True
            return state
        
        confidence = classification.confidence
        threshold = state["confidence_threshold"]
        
        # Adjust threshold based on customer tier
        context = state["conversation_context"]
        if context.customer_tier == "enterprise":
            threshold *= 0.9  # Lower threshold for enterprise customers
        elif context.customer_tier == "premium":
            threshold *= 0.95
        
        if confidence < threshold:
            state["requires_escalation"] = True
            state["escalation_info"] = EscalationInfo(
                reason=EscalationReason.LOW_CONFIDENCE,
                suggested_department=classification.category.value,
                urgency_score=1.0 - confidence
            )
            print(f"⚠️ Low confidence ({confidence:.1%}) - escalating")
        else:
            print(f"✅ High confidence ({confidence:.1%}) - proceeding")
        
        return state
    
    def _route_to_specialist_node(self, state: WorkflowState) -> WorkflowState:
        """Route to appropriate specialist handler"""
        print("🎯 Routing to specialist...")
        
        classification = state["classification"]
        start_time = datetime.now()
        
        # Enhanced routing logic based on category and context
        routing_info = {
            "billing": {
                "handler": "billing_specialist",
                "estimated_time": "2-5 minutes",
                "requires_auth": True
            },
            "technical": {
                "handler": "technical_specialist", 
                "estimated_time": "5-15 minutes",
                "requires_auth": False
            },
            "general": {
                "handler": "general_support",
                "estimated_time": "1-3 minutes", 
                "requires_auth": False
            }
        }
        
        category = classification.category.value
        route_info = routing_info.get(category, routing_info["general"])
        
        state["debug_info"]["routing"] = route_info
        state["processing_metrics"].routing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        state["status"] = TicketStatus.ROUTED
        
        print(f"📍 Routed to: {route_info['handler']}")
        return state
    
    def _generate_response_node(self, state: WorkflowState) -> WorkflowState:
        """Generate response with enhanced context"""
        print("🤖 Generating AI response...")
        
        if not state.get("classification"):
            state["errors"].append("No classification available for response generation")
            return state
        
        try:
            start_time = datetime.now()
            
            # Enhanced context for response generation
            context = state["conversation_context"]
            enhanced_question = UserQuestion(
                text=state["question"].text,
                metadata={
                    "customer_tier": context.customer_tier,
                    "sentiment": context.user_sentiment,
                    "priority": state["priority"].value,
                    "previous_interactions": len(context.previous_interactions)
                }
            )
            
            response = self.handler.handle(enhanced_question, state["classification"])
            
            state["response"] = response
            state["processing_metrics"].response_generation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            state["processing_metrics"].api_calls_made += 1
            state["status"] = TicketStatus.PROCESSING
            
            print("✅ Response generated!")
            
        except Exception as e:
            state["errors"].append(f"Response generation error: {str(e)}")
            state["retry_count"] += 1
        
        return state
    
    def _quality_check_node(self, state: WorkflowState) -> WorkflowState:
        """Perform quality checks on generated response"""
        print("🔍 Performing quality check...")
        
        response = state.get("response")
        if not response:
            return state
        
        quality_score = 1.0
        issues = []
        
        # Check response length
        if len(response.message) < 20:
            quality_score -= 0.3
            issues.append("Response too short")
        elif len(response.message) > 1000:
            quality_score -= 0.2
            issues.append("Response too long")
        
        # Check for generic responses
        generic_phrases = ["I'm here to help", "Thank you for contacting", "Let me assist"]
        if any(phrase in response.message for phrase in generic_phrases):
            quality_score -= 0.1
            issues.append("Generic response detected")
        
        # Check category alignment
        category_keywords = {
            "billing": ["payment", "charge", "invoice", "billing", "account"],
            "technical": ["technical", "error", "bug", "issue", "troubleshoot"],
            "general": ["help", "information", "question", "support"]
        }
        
        category = state["classification"].category.value
        expected_keywords = category_keywords.get(category, [])
        if not any(keyword in response.message.lower() for keyword in expected_keywords):
            quality_score -= 0.2
            issues.append("Response doesn't match category")
        
        state["debug_info"]["quality_check"] = {
            "score": quality_score,
            "issues": issues
        }
        
        # Determine next action based on quality
        if quality_score < 0.6:
            state["warnings"].append(f"Low quality response (score: {quality_score:.2f})")
            if state["retry_count"] < state["max_retries"]:
                state["next_action"] = "retry"
            else:
                state["next_action"] = "escalate"
        else:
            state["next_action"] = "approve"
        
        print(f"📊 Quality score: {quality_score:.2f}")
        return state
    
    def _escalate_to_human_node(self, state: WorkflowState) -> WorkflowState:
        """Handle escalation to human agent"""
        print("🚨 Escalating to human agent...")
        
        escalation_info = state.get("escalation_info")
        if not escalation_info:
            escalation_info = EscalationInfo(
                reason=EscalationReason.TECHNICAL_LIMITATION,
                suggested_department="general_support"
            )
        
        # Create escalation response
        escalation_response = SupportResponse(
            message=f"I understand this requires special attention. I'm connecting you with a human specialist who can better assist you. Your ticket {state['ticket_id']} has been prioritized.",
            category=state["classification"].category if state.get("classification") else None,
            confidence=1.0,
            processing_time_ms=0.0
        )
        
        state["response"] = escalation_response
        state["status"] = TicketStatus.ESCALATED
        state["debug_info"]["escalation"] = {
            "reason": escalation_info.reason.value,
            "department": escalation_info.suggested_department,
            "human_required": escalation_info.human_agent_required
        }
        
        print(f"🎫 Escalated - Reason: {escalation_info.reason.value}")
        return state
    
    def _finalize_response_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize response and update metrics"""
        print("🏁 Finalizing response...")
        
        # Calculate total processing time
        total_time = (datetime.now() - state["processing_metrics"].start_time).total_seconds() * 1000
        state["processing_metrics"].total_processing_time_ms = total_time
        
        # Update conversation context
        context = state["conversation_context"]
        context.previous_interactions.append({
            "ticket_id": state["ticket_id"],
            "category": state["classification"].category.value if state.get("classification") else "unknown",
            "timestamp": datetime.now().isoformat(),
            "status": state["status"].value
        })
        
        state["status"] = TicketStatus.RESOLVED
        print(f"✅ Ticket {state['ticket_id']} finalized - Total time: {total_time:.1f}ms")
        return state
    
    def _handle_error_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and provide fallback response"""
        print("❌ Handling errors...")
        
        error_response = SupportResponse(
            message="I apologize, but I'm experiencing some technical difficulties. A human agent will be with you shortly to assist with your request.",
            category=None,
            confidence=0.0,
            processing_time_ms=0.0
        )
        
        state["response"] = error_response
        state["status"] = TicketStatus.FAILED
        
        print(f"🚫 Ticket {state['ticket_id']} failed with {len(state['errors'])} errors")
        return state
    
    # Conditional routing functions
    def _should_continue_after_validation(self, state: WorkflowState) -> Literal["continue", "error"]:
        return "continue" if state["should_continue"] and not state["errors"] else "error"
    
    def _should_continue_after_classification(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        if state["errors"] and state["retry_count"] >= state["max_retries"]:
            return "error"
        elif state["errors"]:
            return "retry"
        else:
            return "continue"
    
    def _confidence_routing(self, state: WorkflowState) -> Literal["high_confidence", "low_confidence", "needs_human"]:
        if state["requires_escalation"]:
            return "needs_human"
        
        classification = state.get("classification")
        if classification and classification.confidence >= state["confidence_threshold"]:
            return "high_confidence"
        else:
            return "low_confidence"
    
    def _should_continue_after_response(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        if state["errors"] and state["retry_count"] >= state["max_retries"]:
            return "error"
        elif state["errors"]:
            return "retry"
        else:
            return "continue"
    
    def _quality_check_routing(self, state: WorkflowState) -> Literal["approved", "needs_improvement", "escalate"]:
        next_action = state.get("next_action", "approve")
        if next_action == "retry":
            return "needs_improvement"
        elif next_action == "escalate":
            return "escalate"
        else:
            return "approved"
    
    def process(self, question_text: str, user_context: Optional[Any] = None) -> GraphState:
        """Process a question through the complex workflow with proper error handling"""
        from models import UserQuestion  # Import here to avoid circular imports
        
        question = UserQuestion(text=question_text)
        
        # Your existing initial_state setup...
        initial_state = {
            "ticket_id": "",
            "question": question,
            "status": TicketStatus.NEW,
            "priority": Priority.MEDIUM,
            "classification": None,
            "confidence_threshold": self.confidence_threshold,
            "requires_escalation": False,
            "escalation_info": None,
            "response": None,
            "alternative_responses": [],
            "processing_metrics": ProcessingMetrics(),
            "conversation_context": user_context or ConversationContext(),
            "user_feedback": None,
            "errors": [],
            "warnings": [],
            "debug_info": {},
            "retry_count": 0,
            "max_retries": self.max_retries,
            "should_continue": True,
            "next_action": None
        }
        
        try:
            print(f"\n🎫 Processing new support request...")
            result = self.workflow.invoke(initial_state)
            
            print(f"\n📊 Workflow Summary:")
            print(f"   Ticket ID: {result['ticket_id']}")
            print(f"   Status: {result['status'].value}")
            print(f"   Priority: {result['priority'].value}")
            print(f"   Processing Time: {result['processing_metrics'].total_processing_time_ms:.1f}ms")
            print(f"   API Calls: {result['processing_metrics'].api_calls_made}")
            if result['errors']:
                print(f"   Errors: {len(result['errors'])}")
            if result['warnings']:
                print(f"   Warnings: {len(result['warnings'])}")
            
            # Convert complex workflow result to GraphState
            return GraphState.from_workflow_result(result)
            
        except Exception as e:
            print(f"❌ Workflow execution error: {str(e)}")
            
            
            return GraphState(
                question=question,
                classification=None,
                response=None,
                error=f"Workflow error: {str(e)}",
                ticket_id="ERROR",
                status="failed",
                errors=[str(e)]
            )