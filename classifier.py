import time
import os
import re
import requests
from functools import lru_cache
from models import UserQuestion, ClassificationResult, SupportCategory
from config import Config



class QuestionClassifier:
    def __init__(self):
        print("⚡ Initializing Groq-based classification system...")
        
        # Groq configuration
        self.api_key = os.getenv("GROQ_API_KEY") or getattr(Config, 'GROQ_API_KEY', '')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"  # Fast and accurate
        
        # Classification categories
        self.categories = {
            "technical": "technical support login and app issues",
            "billing": "billing payment and subscription questions", 
            "general": "general information and account help"
        }
        
        # Quick keyword patterns for obvious cases (faster than API)
        self.keyword_patterns = {
            SupportCategory.TECHNICAL: [
                r'\b(login|log.?in|sign.?in|password|username|authenticate)\b',
                r'\b(button|click|press|tap)\b.*\b(not work|doesn\'t work|broken|fail)\b',
                r'\b(error|bug|crash|freeze|loading|stuck|hang)\b',
                r'\b(app|website|site|page)\b.*\b(not work|broken|slow)\b',
                r'\b(can\'t|cannot|unable to)\b.*\b(login|access|open|load)\b',
                r'\b(technical|server|connection|network|browser)\b',
                r'\b(upload|download|export|sync)\b.*\b(not work|fail|error)\b'
            ],
            SupportCategory.BILLING: [
                r'\b(billing|bill|invoice|payment|charge|charged|subscription)\b',
                r'\b(refund|money|cost|price|pricing|fee|plan)\b',
                r'\b(credit card|paypal|transaction|upgrade|cancel)\b',
                r'\b(double charge|wrong charge|overcharge)\b'
            ]
        }
        
        # Test API connectivity
        if self._test_groq_connection():
            print("🚀 Groq classification ready!")
        else:
            print("⚠️ Groq API not available, using keyword fallback")
            self.api_key = None
        
        print("✅ Classification system loaded!")
    
    def _test_groq_connection(self) -> bool:
        """Test Groq API connectivity"""
        if not self.api_key:
            return False
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _classify_with_keywords(self, text: str) -> tuple:
        """Fast keyword-based classification for obvious cases"""
        text_lower = text.lower()
        
        # Count matches for each category
        scores = {}
        for category, patterns in self.keyword_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, text_lower, re.IGNORECASE))
            if score > 0:
                scores[category] = score
        
        if scores:
            # Return category with highest score
            best_category = max(scores.keys(), key=lambda k: scores[k])
            # Simple confidence based on match count (max out at 0.95)
            confidence = min(0.95, 0.7 + (scores[best_category] * 0.1))
            return best_category.value, confidence
        
        return None, 0.0
    
    def _classify_with_groq(self, text: str) -> tuple:
        """Classify using Groq API"""
        if not self.api_key:
            return None, 0.0
        
        try:
            # Create a focused classification prompt
            prompt = f"""Classify this customer support question into exactly one category:

Categories:
1. technical - login issues, app problems, bugs, errors, technical difficulties
2. billing - payments, subscriptions, charges, refunds, pricing, invoices  
3. general - account questions, information requests, general help

Question: "{text}"

Respond with ONLY the category name (technical, billing, or general) and a confidence score from 0.1 to 1.0.
Format: category,confidence
Example: technical,0.85"""

            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a precise classification system. Always respond in the exact format requested."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 20,
                    "temperature": 0.1  # Low temperature for consistent classification
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip().lower()
                
                # Parse the response (format: category,confidence)
                if ',' in content:
                    parts = content.split(',')
                    category = parts[0].strip()
                    try:
                        confidence = float(parts[1].strip())
                        confidence = max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0
                    except (ValueError, IndexError):
                        confidence = 0.8  # Default confidence
                    
                    # Validate category
                    if category in ['technical', 'billing', 'general']:
                        return category, confidence
                
                # Fallback parsing - just look for category keywords
                if 'technical' in content:
                    return 'technical', 0.7
                elif 'billing' in content:
                    return 'billing', 0.7
                elif 'general' in content:
                    return 'general', 0.7
                    
        except Exception as e:
            print(f"⚠️ Groq classification error: {str(e)[:50]}...")
        
        return None, 0.0
    
    @lru_cache(maxsize=Config.CACHE_SIZE)
    def _cached_classify(self, text: str) -> tuple:
        """Cached classification with hybrid approach"""
        # Try keywords first (fastest)
        keyword_result = self._classify_with_keywords(text)
        if keyword_result[0] and keyword_result[1] >= 0.8:
            return keyword_result
        
        # Use Groq for unclear cases
        groq_result = self._classify_with_groq(text)
        if groq_result[0]:
            return groq_result
        
        # Use keyword result if Groq fails
        if keyword_result[0]:
            return keyword_result
        
        # Final fallback
        return 'general', 0.5
    
    def classify(self, question: UserQuestion, worker_id: int = None) -> ClassificationResult:
        start_time = time.time()
        
        try:
            category_str, confidence = self._cached_classify(question.text)
            processing_time = (time.time() - start_time) * 1000
            
            # Convert string to enum
            category_mapping = {
                'technical': SupportCategory.TECHNICAL,
                'billing': SupportCategory.BILLING,
                'general': SupportCategory.GENERAL
            }
            
            category = category_mapping.get(category_str, SupportCategory.GENERAL)
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                processing_time_ms=processing_time,
                worker_id=worker_id
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            print(f"⚠️ Classification error: {str(e)}")
            
            return ClassificationResult(
                category=SupportCategory.GENERAL,
                confidence=0.5,
                processing_time_ms=processing_time,
                worker_id=worker_id
            )
    
    def clear_cache(self):
        """Clear the classification cache"""
        self._cached_classify.cache_clear()
        print("🧹 Classification cache cleared")
    
    def get_cache_info(self):
        """Get cache statistics"""
        return self._cached_classify.cache_info()