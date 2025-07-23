from langgraph.graph import StateGraph, END
from models import GraphState, UserQuestion
from classifier import QuestionClassifier
from handlers import SupportHandler
from typing import TypedDict

class WorkflowState(TypedDict):
    question: UserQuestion
    classification: object
    response: object
    error: str

class SupportWorkflow:
    def __init__(self):
        print("🚀 Initializing AI Support Workflow...")
        self.classifier = QuestionClassifier()
        self.handler = SupportHandler()
        self.workflow = self._build_workflow()
        print("✅ Workflow ready!")
    
    def _build_workflow(self):
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("generate_response", self._response_node)
        
        workflow.add_edge("classify", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.set_entry_point("classify")
        
        return workflow.compile()
    
    def _classify_node(self, state: WorkflowState) -> WorkflowState:
        print("🧠 Classifying question...")
        try:
            classification = self.classifier.classify(state["question"])
            state["classification"] = classification
            print(f"📂 Category: {classification.category.value} ({classification.confidence:.1%})")
        except Exception as e:
            state["error"] = str(e)
            print(f"❌ Classification error: {e}")
        return state
    
    def _response_node(self, state: WorkflowState) -> WorkflowState:
        print("🤖 Generating AI response...")
        if state.get("classification") and not state.get("error"):
            try:
                response = self.handler.handle(state["question"], state["classification"])
                state["response"] = response
                print("✅ Response generated!")
            except Exception as e:
                state["error"] = str(e)
                print(f"❌ Response error: {e}")
        return state
    
    def process(self, question_text: str) -> GraphState:
        question = UserQuestion(text=question_text)
        initial_state = {
            "question": question,
            "classification": None,
            "response": None,
            "error": None
        }
        
        result = self.workflow.invoke(initial_state)
        
        return GraphState(
            question=result["question"],
            classification=result.get("classification"),
            response=result.get("response"),
            error=result.get("error")
        )