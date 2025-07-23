"""
AI Support Agent - General Handler
Specialized handler for general inquiries and informational questions
"""

import re
from typing import List, Tuple

from models import UserQuestion, ClassificationResult, SupportResponse, SupportCategory, Priority
from config import ResponseTemplates, SuggestedActions


class GeneralHandler:
    """
    Handles general inquiry questions with informational responses
    Focuses on providing helpful information and guidance
    """
    
    def __init__(self):
        """Initialize general handler with templates and patterns"""
        self.response_templates = ResponseTemplates.GENERAL_TEMPLATES
        self.suggested_actions = SuggestedActions.GENERAL_ACTIONS
        
        # General inquiry patterns for detailed analysis
        self.how_to_patterns = [
            r'how.*to',
            r'how.*do',
            r'how.*can',
            r'steps.*to',
            r'guide.*for'
        ]
        
        self.feature_patterns = [
            r'what.*is',
            r'explain.*feature',
            r'tell.*about',
            r'feature.*work',
            r'capability'
        ]
        
        self.documentation_patterns = [
            r'documentation',
            r'manual',
            r'guide',
            r'tutorial',
            r'instructions'
        ]
        
        self.contact_patterns = [
            r'contact.*support',
            r'reach.*team',
            r'talk.*someone',
            r'phone.*number',
            r'email.*address'
        ]
        
        self.demo_patterns = [
            r'demo',
            r'trial',
            r'test.*out',
            r'try.*before',
            r'preview'
        ]
        
        self.business_patterns = [
            r'business.*hours',
            r'open.*when',
            r'available.*when',
            r'support.*hours',
            r'office.*hours'
        ]
        
        # Topics that typically require detailed explanations
        self.complex_topics = {
            'machine learning', 'ai', 'artificial intelligence',
            'integration', 'api', 'webhook', 'automation',
            'security', 'privacy', 'compliance', 'gdpr',
            'analytics', 'reporting', 'dashboard'
        }
    
    def handle(self, question: UserQuestion, classification: ClassificationResult) -> SupportResponse:
        """
        Process general question and generate appropriate response
        
        Args:
            question: The user's general question
            classification: Classification result from the classifier
            
        Returns:
            SupportResponse with general informational response and actions
        """
        text_lower = question.text.lower()
        
        # Identify specific type of general inquiry
        inquiry_type, confidence_boost = self._identify_inquiry_type(text_lower)
        
        # Generate response
        response_text = self._generate_response(inquiry_type, text_lower, question.text)
        
        # Get suggested actions
        actions = self._get_suggested_actions(inquiry_type, text_lower)
        
        # Determine if escalation is needed (rare for general inquiries)
        escalation_needed, priority = self._assess_escalation(inquiry_type, text_lower)
        
        # Adjust confidence
        adjusted_confidence = min(0.95, classification.confidence + confidence_boost)
        
        # Create response
        response = SupportResponse(
            category=SupportCategory.GENERAL,
            response=response_text,
            suggested_actions=actions,
            escalation_needed=escalation_needed,
            priority=priority,
            confidence=adjusted_confidence,
            processing_time_ms=classification.processing_time_ms
        )
        
        return response
    
    def _identify_inquiry_type(self, text: str) -> Tuple[str, float]:
        """Identify specific type of general inquiry"""
        # How-to questions
        if any(re.search(pattern, text) for pattern in self.how_to_patterns):
            return 'how_to_question', 0.1
        
        # Feature inquiries
        if any(re.search(pattern, text) for pattern in self.feature_patterns):
            return 'feature_inquiry', 0.1
        
        # Documentation requests
        if any(re.search(pattern, text) for pattern in self.documentation_patterns):
            return 'documentation_request', 0.1
        
        # Contact information requests
        if any(re.search(pattern, text) for pattern in self.contact_patterns):
            return 'contact_info', 0.15
        
        # Demo/trial requests
        if any(re.search(pattern, text) for pattern in self.demo_patterns):
            return 'demo_request', 0.1
        
        # Business hours inquiries
        if any(re.search(pattern, text) for pattern in self.business_patterns):
            return 'contact_info', 0.1
        
        # General information requests
        return 'general_info', 0.0
    
    def _generate_response(self, inquiry_type: str, text_lower: str, original_text: str) -> str:
        """Generate appropriate response text"""
        # Get base response template
        base_response = self.response_templates.get(inquiry_type, self.response_templates['default'])
        response = base_response
        
        # Add personalized context based on detected keywords
        key_terms = self._extract_key_terms(original_text)
        if key_terms:
            response += f" I notice you're interested in {', '.join(key_terms[:3])}. Let me make sure you get the most relevant information."
        
        # Add complexity acknowledgment for technical topics
        complex_topic_mentioned = any(topic in text_lower for topic in self.complex_topics)
        if complex_topic_mentioned and inquiry_type == 'feature_inquiry':
            response += " This is a comprehensive topic, so I'll provide you with detailed resources to get you started."
        
        # Add urgency acknowledgment if present
        if any(urgent in text_lower for urgent in ['urgent', 'quickly', 'asap', 'immediate']):
            response += " I understand you need this information quickly, so I'll prioritize the most important details."
        
        # Add beginner-friendly context
        if any(beginner in text_lower for beginner in ['new', 'beginner', 'start', 'first time']):
            response += " Since you're getting started, I'll include some beginner-friendly resources."
        
        return response
    
    def _get_suggested_actions(self, inquiry_type: str, text: str) -> List[str]:
        """Get relevant suggested actions for the general inquiry"""
        # Get base actions
        base_actions = self.suggested_actions.get(inquiry_type, self.suggested_actions['default'])
        actions = base_actions.copy()
        
        # Add inquiry-specific actions
        if inquiry_type == 'how_to_question':
            if 'setup' in text or 'install' in text:
                actions.insert(1, "Download our setup wizard tool")
            if 'integrate' in text:
                actions.append("Review our integration examples repository")
        
        elif inquiry_type == 'feature_inquiry':
            if any(topic in text for topic in self.complex_topics):
                actions.extend([
                    "Watch our feature deep-dive webinar",
                    "Join our weekly Q&A sessions"
                ])
        
        elif inquiry_type == 'demo_request':
            actions.extend([
                "Schedule a personalized demo with our team",
                "Join our next group demo session",
                "Download our product overview PDF"
            ])
        
        elif inquiry_type == 'contact_info':
            # Add specific contact methods
            actions.extend([
                "📧 Email: support@company.com",
                "📞 Phone: 1-800-SUPPORT (24/7)",
                "💬 Live Chat: Available on our website",
                "🌐 Community Forum: community.company.com"
            ])
        
        # Add learning path for complex topics
        if any(topic in text for topic in self.complex_topics):
            actions.append("Follow our step-by-step learning path")
        
        return actions
    
    def _assess_escalation(self, inquiry_type: str, text: str) -> Tuple[bool, Priority]:
        """Determine if escalation is needed for general inquiries"""
        # Most general inquiries don't need escalation
        escalation_needed = False
        priority = Priority.LOW
        
        # Escalate if requesting to speak with someone
        if any(speak in text for speak in ['speak', 'talk', 'call', 'phone']):
            escalation_needed = True
            priority = Priority.MEDIUM
        
        # Escalate complex technical questions that might need expert help
        if inquiry_type == 'feature_inquiry':
            complex_mentioned = any(topic in text for topic in self.complex_topics)
            if complex_mentioned:
                escalation_needed = True
                priority = Priority.MEDIUM
        
        # Escalate demo requests (sales opportunity)
        if inquiry_type == 'demo_request':
            escalation_needed = True
            priority = Priority.MEDIUM
        
        return escalation_needed, priority
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from the question text for personalization"""
        # Simple keyword extraction
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filter out common words
        common_words = {
            'this', 'that', 'with', 'have', 'will', 'they', 'from', 
            'been', 'were', 'said', 'each', 'which', 'their', 'time',
            'what', 'how', 'when', 'where', 'why', 'help', 'need',
            'want', 'know', 'like', 'work', 'make', 'get', 'use'
        }
        
        # Keep meaningful terms
        key_terms = [word for word in words if word not in common_words and len(word) > 3]
        
        # Return unique terms, limited to avoid overwhelming response
        return list(dict.fromkeys(key_terms))[:5]
    
    def get_general_insights(self, text: str) -> dict:
        """Extract general inquiry insights for analytics"""
        insights = {
            'inquiry_type': None,
            'complexity_level': 'basic',
            'user_experience_level': 'unknown',
            'specific_product_mentioned': False,
            'competitor_mentioned': False,
            'urgency_level': 'normal'
        }
        
        # Identify inquiry type
        inquiry_type, _ = self._identify_inquiry_type(text.lower())
        insights['inquiry_type'] = inquiry_type
        
        # Assess complexity
        if any(topic in text.lower() for topic in self.complex_topics):
            insights['complexity_level'] = 'advanced'
        elif any(word in text.lower() for word in ['integration', 'api', 'custom', 'enterprise']):
            insights['complexity_level'] = 'intermediate'
        
        # Assess user experience level
        if any(beginner in text.lower() for beginner in ['new', 'beginner', 'first time', 'getting started']):
            insights['user_experience_level'] = 'beginner'
        elif any(advanced in text.lower() for advanced in ['advanced', 'expert', 'experienced']):
            insights['user_experience_level'] = 'advanced'
        
        # Check for product mentions
        products = ['dashboard', 'api', 'mobile app', 'web app', 'integration', 'analytics']
        if any(product in text.lower() for product in products):
            insights['specific_product_mentioned'] = True
        
        # Check for competitor mentions (for competitive analysis)
        competitors = ['competitor', 'alternative', 'vs', 'compared to', 'better than']
        if any(comp in text.lower() for comp in competitors):
            insights['competitor_mentioned'] = True
        
        # Assess urgency
        if any(urgent in text.lower() for urgent in ['urgent', 'asap', 'immediately']):
            insights['urgency_level'] = 'high'
        elif any(soon in text.lower() for soon in ['soon', 'quickly', 'fast']):
            insights['urgency_level'] = 'medium'
        
        return insights
    
    def suggest_related_topics(self, text: str) -> List[str]:
        """Suggest related topics that might interest the user"""
        related_topics = []
        
        # Topic clustering based on common inquiry themes
        topic_clusters = {
            'getting_started': [
                'Basic setup and configuration',
                'First steps tutorial',
                'Account setup guide'
            ],
            'integration': [
                'API documentation',
                'Webhook setup guide',
                'Third-party integrations'
            ],
            'features': [
                'Feature comparison chart',
                'Advanced features overview',
                'Best practices guide'
            ],
            'support': [
                'Community forum',
                'Video tutorials',
                'FAQ section'
            ]
        }
        
        # Determine relevant cluster based on question content
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['start', 'begin', 'new', 'setup']):
            related_topics.extend(topic_clusters['getting_started'])
        
        if any(word in text_lower for word in ['integrate', 'api', 'connect']):
            related_topics.extend(topic_clusters['integration'])
        
        if any(word in text_lower for word in ['feature', 'capability', 'function']):
            related_topics.extend(topic_clusters['features'])
        
        if any(word in text_lower for word in ['help', 'support', 'learn']):
            related_topics.extend(topic_clusters['support'])
        
        # Remove duplicates and limit results
        return list(dict.fromkeys(related_topics))[:5]