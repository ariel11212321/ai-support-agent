"""
AI Support Agent - Billing Handler
Specialized handler for billing-related questions and issues
"""

import re
from typing import List, Tuple

from models import UserQuestion, ClassificationResult, SupportResponse, SupportCategory, Priority
from config import ResponseTemplates, SuggestedActions


class BillingHandler:
    """
    Handles billing-related questions with specialized responses
    Includes escalation logic and action recommendations
    """
    
    def __init__(self):
        """Initialize billing handler with templates and patterns"""
        self.response_templates = ResponseTemplates.BILLING_TEMPLATES
        self.suggested_actions = SuggestedActions.BILLING_ACTIONS
        
        # Billing-specific patterns for detailed analysis
        self.cancellation_patterns = [
            r'cancel.*subscription',
            r'stop.*billing',
            r'unsubscribe',
            r'end.*plan',
            r'terminate.*account'
        ]
        
        self.payment_patterns = [
            r'payment.*fail',
            r'card.*declin',
            r'charge.*error',
            r'transaction.*fail',
            r'billing.*problem'
        ]
        
        self.refund_patterns = [
            r'refund.*request',
            r'money.*back',
            r'return.*payment',
            r'reverse.*charge',
            r'credit.*back'
        ]
        
        self.upgrade_patterns = [
            r'upgrade.*plan',
            r'change.*subscription',
            r'higher.*tier',
            r'more.*features',
            r'premium.*plan'
        ]
        
        self.invoice_patterns = [
            r'invoice.*question',
            r'bill.*inquiry',
            r'receipt.*request',
            r'statement.*issue',
            r'billing.*history'
        ]
    
    def handle(self, question: UserQuestion, classification: ClassificationResult) -> SupportResponse:
        """
        Process billing question and generate appropriate response
        
        Args:
            question: The user's billing question
            classification: Classification result from the classifier
            
        Returns:
            SupportResponse with billing-specific response and actions
        """
        text_lower = question.text.lower()
        
        # Determine specific billing issue type
        issue_type, confidence_boost = self._identify_billing_issue(text_lower)
        
        # Generate response based on issue type
        response_text = self._generate_response(issue_type, text_lower, question.text)
        
        # Get suggested actions
       
        
        # Determine escalation need and priority
        escalation_needed, priority = self._assess_escalation(issue_type, text_lower)
        
        # Adjust confidence based on billing-specific analysis
        adjusted_confidence = min(0.95, classification.confidence + confidence_boost)
        
        # Create and return response
        response = SupportResponse(
            category=SupportCategory.BILLING,
            response=response_text,
            suggested_actions=actions,
            escalation_needed=escalation_needed,
            priority=priority,
            confidence=adjusted_confidence,
            processing_time_ms=classification.processing_time_ms
        )
        
        return response
    
    def _identify_billing_issue(self, text: str) -> Tuple[str, float]:
        """
        Identify specific type of billing issue
        
        Returns:
            Tuple of (issue_type, confidence_boost)
        """
        # Check for cancellation requests
        if any(re.search(pattern, text) for pattern in self.cancellation_patterns):
            return 'cancel_subscription', 0.1
        
        # Check for payment issues
        if any(re.search(pattern, text) for pattern in self.payment_patterns):
            return 'payment_issue', 0.15
        
        # Check for refund requests
        if any(re.search(pattern, text) for pattern in self.refund_patterns):
            return 'refund_request', 0.1
        
        # Check for upgrade requests
        if any(re.search(pattern, text) for pattern in self.upgrade_patterns):
            return 'upgrade_plan', 0.05
        
        # Check for invoice inquiries
        if any(re.search(pattern, text) for pattern in self.invoice_patterns):
            return 'invoice_inquiry', 0.05
        
        # Check for pricing questions
        if any(word in text for word in ['price', 'cost', 'expensive', 'cheap', 'pricing']):
            return 'pricing_question', 0.05
        
        # Default to general billing
        return 'default', 0.0
    
    def _generate_response(self, issue_type: str, text_lower: str, original_text: str) -> str:
        """Generate appropriate response text"""
        # Get base response template
        base_response = self.response_templates.get(issue_type, self.response_templates['default'])
        
        # Add contextual information
        response = base_response
        
        # Add amount-specific context if dollar amounts detected
        amounts = re.findall(r'\$[\d,]+\.?\d*', original_text)
        if amounts:
            response += f" I see you're referring to {', '.join(amounts)}. Let me help you with that specific amount."
        
        # Add urgency acknowledgment if urgent language detected
        urgent_words = ['urgent', 'immediate', 'asap', 'emergency', 'critical']
        if any(word in text_lower for word in urgent_words):
            response += " I understand this is urgent and will prioritize your request accordingly."
        
        # Add specific context for failed payments
        if issue_type == 'payment_issue' and any(word in text_lower for word in ['fail', 'decline', 'error']):
            response += " Payment failures can be due to insufficient funds, expired cards, or bank restrictions."
        
        # Add reassurance for refund requests
        if issue_type == 'refund_request':
            response += " We process refund requests promptly and will keep you updated on the status."
        
        return response
    
    def _get_suggested_actions(self, issue_type: str, text: str) -> List[str]:
        """Get relevant suggested actions for the billing issue"""
        # Get base actions for issue type
        base_actions = self.suggested_actions.get(issue_type, self.suggested_actions['default'])
        actions = base_actions.copy()
        
        # Add specific actions based on context
        if issue_type == 'payment_issue':
            if 'card' in text:
                actions.insert(1, "Update payment method with a different card")
            if 'decline' in text:
                actions.insert(1, "Contact your bank to authorize the transaction")
        
        elif issue_type == 'cancel_subscription':
            if 'immediate' in text or 'now' in text:
                actions.insert(0, "Use live chat for immediate cancellation assistance")
        
        elif issue_type == 'refund_request':
            if any(amount in text for amount in ['$', 'dollar', 'paid']):
                actions.insert(1, "Have your payment confirmation/receipt ready")
        
        elif issue_type == 'upgrade_plan':
            actions.extend([
                "Review feature comparison chart",
                "Calculate potential savings with annual billing"
            ])
        
        return actions
    
    def _assess_escalation(self, issue_type: str, text: str) -> Tuple[bool, Priority]:
        """Determine if escalation is needed and set priority"""
        # High priority issues that need escalation
        high_priority_issues = ['payment_issue', 'refund_request']
        
        # Check for explicit urgency
        urgent_indicators = ['urgent', 'immediate', 'asap', 'emergency', 'critical']
        is_urgent = any(indicator in text for indicator in urgent_indicators)
        
        # Check for payment failures
        payment_failed = any(word in text for word in ['fail', 'decline', 'error', 'problem'])
        
        # Check for large amounts (indicate high-value customers)
        large_amounts = re.findall(r'\$(\d+)', text)
        is_high_value = any(int(amount.replace(',', '')) > 1000 for amount in large_amounts if amount.replace(',', '').isdigit())
        
        # Determine escalation and priority
        escalation_needed = False
        priority = Priority.MEDIUM
        
        if is_urgent or payment_failed:
            escalation_needed = True
            priority = Priority.URGENT
        elif issue_type in high_priority_issues:
            escalation_needed = True
            priority = Priority.HIGH
        elif is_high_value:
            escalation_needed = True
            priority = Priority.HIGH
        elif issue_type == 'cancel_subscription':
            # Cancellations often need human touch for retention
            escalation_needed = True
            priority = Priority.MEDIUM
        
        return escalation_needed, priority
    
    def get_billing_insights(self, text: str) -> dict:
        """
        Extract billing-specific insights from the question
        Useful for analytics and reporting
        """
        insights = {
            'issue_type': None,
            'amount_mentioned': None,
            'urgency_level': 'normal',
            'payment_method_mentioned': False,
            'account_action_requested': False
        }
        
        # Identify issue type
        issue_type, _ = self._identify_billing_issue(text.lower())
        insights['issue_type'] = issue_type
        
        # Extract mentioned amounts
        amounts = re.findall(r'\$[\d,]+\.?\d*', text)
        if amounts:
            insights['amount_mentioned'] = amounts[0]
        
        # Assess urgency
        urgent_words = ['urgent', 'immediate', 'asap', 'emergency', 'critical']
        if any(word in text.lower() for word in urgent_words):
            insights['urgency_level'] = 'high'
        elif any(word in text.lower() for word in ['soon', 'quickly', 'fast']):
            insights['urgency_level'] = 'medium'
        
        # Check for payment method mentions
        payment_methods = ['card', 'credit', 'debit', 'paypal', 'bank', 'visa', 'mastercard']
        if any(method in text.lower() for method in payment_methods):
            insights['payment_method_mentioned'] = True
        
        # Check for account actions
        account_actions = ['cancel', 'upgrade', 'downgrade', 'change', 'update']
        if any(action in text.lower() for action in account_actions):
            insights['account_action_requested'] = True
        
        return insights