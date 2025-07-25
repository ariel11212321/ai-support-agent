import time
import requests
import json
import os
from functools import lru_cache
from typing import Optional, Dict, Any
from models import UserQuestion, ClassificationResult, SupportResponse
from config import Config


class AIResponseGenerator:
    def __init__(self):
        print("⚡ Initializing Groq AI response system...")
        
        # Groq configuration
        self.api_key = getattr(Config, 'GROQ_API_KEY', '')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"  # Fast and free model
        
        # Request configuration
        self.timeout = 10
        self.max_tokens = 150
        self.temperature = 0.7
        
        # Test API availability
        if self._test_groq_connection():
            print("🚀 Groq API connection verified!")
        else:
            print("⚠️ Groq API not available, using fallback responses")
            self.api_key = None
    
    def _test_groq_connection(self) -> bool:
        """Test Groq API connectivity"""
        if not self.api_key:
            print("❌ No Groq API key found")
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
            
            if response.status_code == 200:
                print("✅ Groq API test successful")
                return True
            else:
                print(f"❌ Groq API test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Groq API test error: {str(e)[:50]}...")
            return False
    
    def _create_enhanced_prompt(self, question: str, category: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create specialized prompts for different support categories"""
        
        # Extract metadata for context
        customer_tier = "standard"
        sentiment = "neutral"
        priority = "medium"
        
        if metadata:
            customer_tier = metadata.get("customer_tier", "standard")
            sentiment = metadata.get("sentiment", "neutral")
            priority = metadata.get("priority", "medium")
        
        # Base system prompts for each category
        system_prompts = {
            "billing": """You are a professional billing support specialist. You help customers with payment issues, account billing, invoices, and subscription questions. Always be empathetic, clear, and solution-focused. Provide specific next steps when possible.""",
            
            "technical": """You are an expert technical support engineer. You help customers troubleshoot software issues, bugs, and technical problems. Provide clear, step-by-step guidance and ask relevant follow-up questions to diagnose issues effectively.""",
            
            "general": """You are a helpful customer service representative. You assist customers with general inquiries, account questions, and product information. Be friendly, informative, and always aim to fully address the customer's needs."""
        }
        
        # Adjust tone based on customer tier and sentiment
        tone_adjustments = {
            "enterprise": " Use a professional, executive-level communication style.",
            "premium": " Provide detailed, priority service with additional context.",
            "standard": " Maintain a friendly, helpful tone."
        }
        
        sentiment_adjustments = {
            "negative": " The customer seems frustrated, so be especially empathetic and focus on immediate resolution.",
            "positive": " The customer has a positive attitude, maintain their satisfaction.",
            "neutral": " Maintain a professional, helpful demeanor."
        }
        
        priority_adjustments = {
            "urgent": " This is an urgent request requiring immediate attention.",
            "high": " This is a high-priority request.",
            "medium": " Handle this with standard priority.",
            "low": " This is a routine inquiry."
        }
        
        # Build enhanced system prompt
        system_prompt = system_prompts.get(category, system_prompts["general"])
        system_prompt += tone_adjustments.get(customer_tier, tone_adjustments["standard"])
        system_prompt += sentiment_adjustments.get(sentiment, sentiment_adjustments["neutral"])
        system_prompt += priority_adjustments.get(priority, priority_adjustments["medium"])
        
        # Add specific instructions
        system_prompt += "\n\nGuidelines:\n"
        system_prompt += "- Keep responses concise but comprehensive (50-120 words)\n"
        system_prompt += "- Always acknowledge the customer's concern\n"
        system_prompt += "- Provide actionable next steps when applicable\n"
        system_prompt += "- Use a warm, professional tone\n"
        system_prompt += "- Avoid technical jargon unless specifically relevant\n"
        
        return system_prompt
    
    def _call_groq_api(self, question: str, category: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Make API call to Groq with enhanced prompting"""
        if not self.api_key:
            return ""
        
        try:
            system_prompt = self._create_enhanced_prompt(question, category, metadata)
            
            # Prepare the request
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make the API call
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Basic quality checks
                if len(content) < 20:
                    print("⚠️ Groq response too short, using fallback")
                    return ""
                
                return content
            
            elif response.status_code == 429:
                print("⚠️ Groq rate limit hit")
                return ""
            
            else:
                print(f"⚠️ Groq API error: {response.status_code} - {response.text[:100]}")
                return ""
                
        except requests.exceptions.Timeout:
            print("⚠️ Groq API timeout")
            return ""
        
        except Exception as e:
            print(f"⚠️ Groq API error: {str(e)[:50]}...")
            return ""
    
    def _get_fallback_response(self, category: str, question: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Enhanced fallback responses when Groq API is unavailable"""
        
        # Extract customer context
        customer_tier = metadata.get("customer_tier", "standard") if metadata else "standard"
        sentiment = metadata.get("sentiment", "neutral") if metadata else "neutral"
        
        # Tier-specific greetings
        greetings = {
            "enterprise": "Thank you for contacting our enterprise support team.",
            "premium": "Thank you for contacting our premium support.",
            "standard": "Thank you for contacting our support team."
        }
        
        # Sentiment-aware responses
        empathy = {
            "negative": "I understand your frustration, and I'm here to help resolve this issue for you.",
            "positive": "I appreciate you reaching out, and I'm happy to assist you.",
            "neutral": "I'm here to help you with your inquiry."
        }
        
        # Category-specific responses
        responses = {
            "billing": {
                "action": "I'll help you resolve this billing matter right away. Let me review your account and get this sorted out for you.",
                "next_steps": "I'll need to access your account details to provide the most accurate information and resolution."
            },
            "technical": {
                "action": "I can help you troubleshoot this technical issue. Let me guide you through some steps to identify and resolve the problem.",
                "next_steps": "I'll work with you step-by-step to diagnose the issue and find an effective solution."
            },
            "general": {
                "action": "I'm here to help answer your question and provide you with the information you need.",
                "next_steps": "I'll make sure you get comprehensive assistance with your inquiry."
            }
        }
        
        # Build response
        greeting = greetings.get(customer_tier, greetings["standard"])
        empathy_msg = empathy.get(sentiment, empathy["neutral"])
        category_response = responses.get(category, responses["general"])
        
        response = f"{greeting} {empathy_msg} {category_response['action']} {category_response['next_steps']}"
        
        return response
    
    @lru_cache(maxsize=500)
    def _cached_generate(self, question: str, category: str, metadata_str: str = "") -> str:
        """Generate response with caching (metadata converted to string for hashing)"""
        metadata = json.loads(metadata_str) if metadata_str else None
        
        # Try Groq API first
        response = self._call_groq_api(question, category, metadata)
        
        # Fallback if API fails or returns poor response
        if not response or len(response) < 20:
            return self._get_fallback_response(category, question, metadata)
        
        return response
    
    def generate_response(self, question: UserQuestion, classification: ClassificationResult) -> SupportResponse:
        """Generate a support response using Groq API"""
        start_time = time.time()
        
        # Extract metadata for enhanced prompting
        metadata = question.metadata or {}
        metadata_str = json.dumps(metadata, sort_keys=True) if metadata else ""
        
        # Generate response
        category = classification.category.value
        ai_message = self._cached_generate(question.text, category, metadata_str)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        total_time = processing_time + (classification.processing_time_ms or 0)
        
        return SupportResponse(
            message=ai_message,
            category=classification.category,
            confidence=classification.confidence,
            processing_time_ms=total_time
        )
    
    def clear_cache(self):
        """Clear the response cache"""
        self._cached_generate.cache_clear()
        print("🧹 Response cache cleared")
    
    def get_cache_info(self):
        """Get cache statistics"""
        return self._cached_generate.cache_info()
