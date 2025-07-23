import time
from functools import lru_cache
from transformers import pipeline
from models import UserQuestion, ClassificationResult, SupportCategory
from config import Config

class QuestionClassifier:
    def __init__(self):
        print("🤖 Loading HuggingFace classification model...")
        self.classifier = pipeline("zero-shot-classification", model=Config.CLASSIFICATION_MODEL)
        print("✅ Classification model loaded!")
    
    @lru_cache(maxsize=Config.CACHE_SIZE)
    def _cached_classify(self, text: str) -> tuple:
        """Cached classification to avoid duplicate API calls"""
        result = self.classifier(text, Config.CLASSIFICATION_LABELS)
        return result['labels'][0], result['scores'][0]
    
    def classify(self, question: UserQuestion, worker_id: int = None) -> ClassificationResult:
        start_time = time.time()
        
        try:
            best_label, score = self._cached_classify(question.text)
            processing_time = (time.time() - start_time) * 1000
            
            return ClassificationResult(
                category=SupportCategory(best_label),
                confidence=score,
                processing_time_ms=processing_time,
                worker_id=worker_id
            )
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return ClassificationResult(
                category=SupportCategory.GENERAL,
                confidence=0.5,
                processing_time_ms=processing_time,
                worker_id=worker_id
            )