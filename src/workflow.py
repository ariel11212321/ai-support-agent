"""
AI Support Agent - LangGraph Workflow
Main workflow orchestration using LangGraph state management
"""

import time
from typing import Dict, Any, Optional
from dataclasses import asdict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models import (
    UserQuestion, ClassificationResult, SupportResponse, 
    SupportCategory, ConversationHistory, WorkerTask
)
from classifier import QuestionClassifier
from billing_handler import BillingHandler
from technical_handler import TechnicalHandler
from general_handler import GeneralHandler


class SupportWorkflow:
    """
    Main support workflow using LangGraph for state management
    Orchestrates the entire question processing pipeline
    """
    
    def __init__(self, enable_checkpoints: bool = False):
        """
        Initialize the workflow with handlers and graph
        
        Args:
            enable_checkpoints: Whether to enable workflow checkpoints for recovery
        """
        # Initialize components
        self.classifier = QuestionClassifier()
        self.handlers = {
            SupportCategory.BILLING: BillingHandler(),
            SupportCategory.TECHNICAL: TechnicalHandler(),
            SupportCategory.GENERAL: GeneralHandler()
        }
        
        # Initialize checkpointer if needed
        self.checkpointer = MemorySaver() if enable_checkpoints else None
        
        # Build the workflow graph
        self.graph = self._build_workflow_graph()
        
        # Performance tracking
        self.workflow_count = 0
        self.total_processing_time = 0.0
        
    def _build_workflow_graph(self) -> StateGraph:
        """Build and compile the LangGraph workflow"""
        # Define the state schema
        workflow = StateGraph(dict)
        
        # Add workflow nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("classify_question", self._classify_question_node)
        workflow.add_node("route_to_handler", self._route_to_handler_node)
        workflow.add_node("handle_billing", self._handle_billing_node)
        workflow.add_node("handle_technical", self._handle_technical_node)
        workflow.add_node("handle_general", self._handle_general_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("validate_input")
        
        # Define workflow edges
        workflow.add_edge("validate_input", "classify_question")
        
        # Conditional routing from classification
        workflow.add_conditional_edges(
            "classify_question",
            self._route_question_decision,
            {
                "route_to_handler": "route_to_handler",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "route_to_handler",
            self._category_decision,
            {
                SupportCategory.BILLING: "handle_billing",
                SupportCategory.TECHNICAL: "handle_technical", 
                SupportCategory.GENERAL: "handle_general",
                "handle_error": "handle_error"
            }
        )
        
        # All handlers go to finalization
        workflow.add_edge("handle_billing", "finalize_response")
        workflow.add_edge("handle_technical", "finalize_response")
        workflow.add_edge("handle_general", "finalize_response")
        
        # Terminal nodes
        workflow.add_edge("finalize_response", END)
        workflow.add_edge("handle_error", END)
        
        # Compile with optional checkpointing
        if self.checkpointer:
            return workflow.compile(checkpointer=self.checkpointer)
        else:
            return workflow.compile()
    
    def process_question(self, question: UserQuestion, worker_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a user question through the complete workflow
        
        Args:
            question: UserQuestion object to process
            worker_id: Optional worker ID for tracking
            
        Returns:
            Dictionary containing the final workflow state
        """
        start_time = time.perf_counter()
        
        try:
            # Prepare initial state
            initial_state = {
                "user_question": asdict(question),
                "worker_id": worker_id,
                "start_time": start_time,
                "classification": None,
                "final_response": None,
                "error": None,
                "workflow_metadata": {
                    "steps_completed": [],
                    "performance_metrics": {}
                }
            }
            
            # Run the workflow
            final_state = self.graph.invoke(initial_state)
            
            # Update performance tracking
            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_performance_tracking(processing_time)
            
            return final_state
            
        except Exception as e:
            # Handle workflow-level errors
            processing_time = (time.perf_counter() - start_time) * 1000
            
            error_state = {
                "user_question": asdict(question),
                "worker_id": worker_id,
                "start_time": start_time,
                "classification": None,
                "final_response": None,
                "error": f"Workflow error: {str(e)}",
                "workflow_metadata": {
                    "steps_completed": ["validate_input"],
                    "performance_metrics": {
                        "processing_time_ms": processing_time,
                        "error_occurred": True
                    }
                }
            }
            
            self._update_performance_tracking(processing_time)
            return error_state
    
    # Workflow Node Implementations
    
    def _validate_input_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input and prepare for processing"""
        try:
            # Add step to metadata
            state["workflow_metadata"]["steps_completed"].append("validate_input")
            
            # Validate question data
            question_data = state.get("user_question")
            if not question_data or not question_data.get("text"):
                return {**state, "error": "Invalid or empty question"}
            
            # Clean and validate question text
            question_text = question_data["text"].strip()
            if len(question_text) < 3:
                return {**state, "error": "Question too short"}
            
            if len(question_text) > 1000:
                return {**state, "error": "Question too long (max 1000 characters)"}
            
            # Update question with cleaned text
            state["user_question"]["text"] = question_text
            
            return state
            
        except Exception as e:
            return {**state, "error": f"Input validation error: {str(e)}"}
    
    def _classify_question_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the user question"""
        try:
            # Add step to metadata
            state["workflow_metadata"]["steps_completed"].append("classify_question")
            
            # Create UserQuestion object from state
            question_data = state["user_question"]
            question = UserQuestion(
                text=question_data["text"],
                user_id=question_data.get("user_id", "anonymous"),
                session_id=question_data.get("session_id")
            )
            
            # Perform classification
            worker_id = state.get("worker_id")
            classification_result = self.classifier.classify(question, worker_id)
            
            # Store classification in state
            state["classification"] = asdict(classification_result)
            
            # Add performance metrics
            state["workflow_metadata"]["performance_metrics"]["classification_time_ms"] = classification_result.processing_time_ms
            
            return state
            
        except Exception as e:
            return {**state, "error": f"Classification error: {str(e)}"}
    
    def _route_to_handler_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route question to appropriate handler based on classification"""
        try:
            # Add step to metadata
            state["workflow_metadata"]["steps_completed"].append("route_to_handler")
            
            # Get classification result
            classification_data = state.get("classification")
            if not classification_data:
                return {**state, "error": "No classification result available"}
            
            # Validate category
            category = classification_data.get("category")
            if category not in [cat.value for cat in SupportCategory]:
                return {**state, "error": f"Invalid category: {category}"}
            
            # Store routing decision
            state["workflow_metadata"]["routing_decision"] = category
            
            return state
            
        except Exception as e:
            return {**state, "error": f"Routing error: {str(e)}"}
    
    def _handle_billing_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle billing questions"""
        return self._handle_category_node(state, "billing", self.handlers[SupportCategory.BILLING])
    
    def _handle_technical_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle technical questions"""
        return self._handle_category_node(state, "technical", self.handlers[SupportCategory.TECHNICAL])
    
    def _handle_general_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general questions"""
        return self._handle_category_node(state, "general", self.handlers[SupportCategory.GENERAL])
    
    def _handle_category_node(self, state: Dict[str, Any], category_name: str, handler) -> Dict[str, Any]:
        """Generic category handler"""
        try:
            # Add step to metadata
            state["workflow_metadata"]["steps_completed"].append(f"handle_{category_name}")
            
            # Reconstruct objects from state
            question_data = state["user_question"]
            question = UserQuestion(
                text=question_data["text"],
                user_id=question_data.get("user_id", "anonymous"),
                session_id=question_data.get("session_id")
            )
            
            classification_data = state["classification"]
            classification = ClassificationResult(
                category=SupportCategory(classification_data["category"]),
                confidence=classification_data["confidence"],
                reasoning=classification_data["reasoning"],
                processing_time_ms=classification_data["processing_time_ms"],
                features_detected=classification_data.get("features_detected", []),
                worker_id=classification_data.get("worker_id")
            )
            
            # Process with handler
            response = handler.handle(question, classification)
            
            # Store response in state
            state["final_response"] = asdict(response)
            
            # Add handler-specific metrics
            state["workflow_metadata"]["performance_metrics"][f"{category_name}_handler_time_ms"] = response.processing_time_ms
            
            return state
            
        except Exception as e:
            return {**state, "error": f"{category_name.title()} handler error: {str(e)}"}
    
    def _finalize_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the response and add metadata"""
        try:
            # Add step to metadata
            state["workflow_metadata"]["steps_completed"].append("finalize_response")
            
            # Calculate total processing time
            start_time = state.get("start_time", time.perf_counter())
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Update performance metrics
            state["workflow_metadata"]["performance_metrics"]["total_processing_time_ms"] = total_time
            state["workflow_metadata"]["performance_metrics"]["workflow_complete"] = True
            
            # Add workflow success flag
            state["workflow_metadata"]["success"] = True
            
            return state
            
        except Exception as e:
            return {**state, "error": f"Finalization error: {str(e)}"}
    
    def _handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow errors"""
        # Add step to metadata
        state["workflow_metadata"]["steps_completed"].append("handle_error")
        
        # Calculate processing time
        start_time = state.get("start_time", time.perf_counter())
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Update performance metrics
        state["workflow_metadata"]["performance_metrics"]["total_processing_time_ms"] = total_time
        state["workflow_metadata"]["performance_metrics"]["error_occurred"] = True
        state["workflow_metadata"]["success"] = False
        
        # Create fallback response if no response exists
        if not state.get("final_response"):
            fallback_response = SupportResponse(
                category=SupportCategory.GENERAL,
                response="I apologize, but I encountered an issue processing your question. Please try again or contact our support team directly.",
                suggested_actions=[
                    "Rephrase your question and try again",
                    "Contact support at support@company.com",
                    "Visit our help center for immediate assistance"
                ],
                escalation_needed=True,
                confidence=0.0,
                processing_time_ms=total_time
            )
            state["final_response"] = asdict(fallback_response)
        
        return state
    
    # Decision Functions for Conditional Edges
    
    def _route_question_decision(self, state: Dict[str, Any]) -> str:
        """Decide whether to route to handler or handle error"""
        if state.get("error"):
            return "handle_error"
        
        classification = state.get("classification")
        if not classification:
            return "handle_error"
        
        return "route_to_handler"
    
    def _category_decision(self, state: Dict[str, Any]) -> str:
        """Decide which category handler to use"""
        if state.get("error"):
            return "handle_error"
        
        classification = state.get("classification")
        if not classification:
            return "handle_error"
        
        category = classification.get("category")
        try:
            return SupportCategory(category)
        except ValueError:
            return "handle_error"
    
    # Performance and Utility Methods
    
    def _update_performance_tracking(self, processing_time: float) -> None:
        """Update workflow performance tracking"""
        self.workflow_count += 1
        self.total_processing_time += processing_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get workflow performance statistics"""
        if self.workflow_count == 0:
            return {
                "total_workflows": 0,
                "average_processing_time_ms": 0.0,
                "classifier_stats": self.classifier.get_performance_stats()
            }
        
        return {
            "total_workflows": self.workflow_count,
            "average_processing_time_ms": self.total_processing_time / self.workflow_count,
            "total_processing_time_ms": self.total_processing_time,
            "classifier_stats": self.classifier.get_performance_stats()
        }
    
    def reset_performance_stats(self) -> None:
        """Reset performance tracking"""
        self.workflow_count = 0
        self.total_processing_time = 0.0
        self.classifier.reset_performance_stats()
    
    def get_workflow_visualization(self) -> str:
        """Get a text representation of the workflow"""
        return """
        🤖 AI Support Agent Workflow
        
        [User Question]
               ↓
        [Validate Input]
               ↓
        [Classify Question] ← QuestionClassifier
               ↓
        [Route to Handler]
               ↓
        ┌─────────────────────────────────────┐
        │         Route by Category           │
        └─────────────────────────────────────┘
               ↓
        ┌──────────┬──────────────┬──────────┐
        │          │              │          │
        ▼          ▼              ▼          ▼
    [Billing]  [Technical]   [General]   [Error]
        │          │              │          │
        └──────────┼──────────────┼──────────┘
                   ▼              
            [Finalize Response]
                   ▼
                [END]
        
        Performance Tracking: ✅
        Error Handling: ✅ 
        State Management: ✅
        Conditional Routing: ✅
        """