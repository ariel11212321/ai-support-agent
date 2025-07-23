"""
AI Support Agent - Premium AI Response Generator
Uses the smartest free models available on HuggingFace
"""

import time
from functools import lru_cache
from transformers import pipeline
from models import UserQuestion, ClassificationResult, SupportResponse
from config import Config

class AIResponseGenerator:
    def __init__(self):
        print("🤖 Loading premium AI models...")
        self.generators = {}
        self.loaded_models = []
        
        # Try the best free models in order of quality
        models_to_try = [
            ("mistralai/Mixtral-8x7B-Instruct-v0.1", "text-generation"),
           ("mistralai/Mistral-7B-Instruct-v0.2",    "text-generation"),
            ("microsoft/Phi-3-mini-128k-instruct",    "text-generation"),
            ("google/flan-t5-base",                   "text2text-generation"),
            ("t5-base",                               "text2text-generation"),
            ("distilgpt2",                            "text-generation")]
        
        for model_name, task in models_to_try:
            try:
                print(f"⚡ Trying {model_name}...")
                generator = pipeline(task, model=model_name)
                self.generators[task] = generator
                self.loaded_models.append(model_name)
                print(f"✅ {model_name} loaded successfully!")
                break  # Use the first one that works
            except Exception as e:
                print(f"⚠️ {model_name} failed: {str(e)[:50]}...")
                continue
        
        if not self.generators:
            print("❌ All AI models failed - using smart templates")
            self.generation_type = "smart-template"
        else:
            self.generation_type = list(self.generators.keys())[0]
            print(f"🚀 Using {self.loaded_models[0]} for responses!")
    
    def _create_smart_prompt(self, question: str, category: str) -> str:
            prompts = {
                "billing": f"Customer: {question}\nBilling Support: I understand your billing concern.",
                "technical": f"Customer: {question}\nTech Support: I can help you with this technical issue.",
                "general": f"Customer: {question}\nSupport Agent: I'm happy to help you with that."
            }
            return prompts[category]
    
    def _generate_with_model(self, prompt: str, category: str) -> str:

        try:
            if self.generation_type == "conversational":
                generator = self.generators["conversational"]
                if "blenderbot" in self.loaded_models[0]:

                    result = generator(prompt, max_length=100, do_sample=True, temperature=0.7)
                    return result[0]['generated_text'].strip()
                else:
                    result = generator(prompt, max_length=100, pad_token_id=50256)
                    return result.generated_responses[-1] if hasattr(result, 'generated_responses') else str(result)
            
            elif self.generation_type == "text2text-generation":
                generator = self.generators["text2text-generation"]
                result = generator(prompt, max_length=80, do_sample=True, temperature=0.7)
                return result[0]['generated_text'].strip()
            
            else: 
                generator = self.generators["text-generation"]
                result = generator(prompt, max_length=len(prompt.split()) + 30, 
                                 do_sample=True, temperature=0.7, pad_token_id=50256)
                generated = result[0]['generated_text']
               
                response = generated.replace(prompt, "").strip()
                return response if len(response) > 5 else self._get_fallback_response(category)
                
        except Exception as e:
            print(f"⚠️ Generation error: {e}")
            return self._get_fallback_response(category)
    
    def _get_fallback_response(self, category: str) -> str:
        """High-quality fallback responses"""
        responses = {
            "billing": "I understand you have a billing question. Let me help you resolve this right away. I'll review your account and get back to you with detailed information.",
            
            "technical": "I see you're experiencing a technical issue. Let's work together to solve this problem. I'll guide you through the troubleshooting steps.",
            
            "general": "Thank you for reaching out! I'm here to help with your question. Let me get you the information you need right away."
        }
        return responses.get(category, "I'm here to help you with your question!")
    
    @lru_cache(maxsize=Config.CACHE_SIZE)
    def _cached_generate(self, question: str, category: str) -> str:
        """Cached response generation with smart AI"""
        
        if self.generators:
            prompt = self._create_smart_prompt(question, category)
            response = self._generate_with_model(prompt, category)
            
            
            return response
        
        # If no AI models, use smart fallback
        return self._get_fallback_response(category)
    
    def generate_response(self, question: UserQuestion, classification: ClassificationResult) -> SupportResponse:
        start_time = time.time()
        
        # Generate AI response
        category = classification.category.value
        ai_message = self._cached_generate(question.text, category)
        
        processing_time = (time.time() - start_time) * 1000
        
        return SupportResponse(
            message=ai_message,
            category=classification.category,
            confidence=classification.confidence,
            processing_time_ms=processing_time + classification.processing_time_ms
        )