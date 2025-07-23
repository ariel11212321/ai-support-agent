from transformers import pipeline
from typing import Tuple
from models import UserQuestion, ClassificationResult, SupportCategory
from config import Config

class QuestionClassifier:
    def __init__(self):
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.labels = ["billing", "technical", "general"]

    def classify(self, question: UserQuestion, worker_id: int = None) -> ClassificationResult:
        try:
            result = self.classifier(question.text, self.labels)
            best_label = result['labels'][0]
            score = result['scores'][0]
            reasoning = f"Zero-shot classification using HuggingFace (score: {score:.2f})"
            return ClassificationResult(
                category=SupportCategory(best_label),
                confidence=score,
                reasoning=reasoning,
                processing_time_ms=0.0,
                features_detected=[],
                worker_id=worker_id
            )
        except Exception as e:
            return ClassificationResult(
                category=SupportCategory.GENERAL,
                confidence=Config.DEFAULT_CONFIDENCE,
                reasoning=f"Classification error: {str(e)}",
                processing_time_ms=0.0,
                features_detected=[],
                worker_id=worker_id
            )