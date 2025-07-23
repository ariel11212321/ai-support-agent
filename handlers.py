from models import UserQuestion, ClassificationResult, SupportResponse
from response_generator import AIResponseGenerator

class SupportHandler:
    def __init__(self):
        self.response_generator = AIResponseGenerator()
    
    def handle(self, question: UserQuestion, classification: ClassificationResult) -> SupportResponse:
        # Generate AI response instead of static template
        return self.response_generator.generate_response(question, classification)