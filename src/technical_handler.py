"""
AI Support Agent - Technical Handler
Specialized handler for technical support questions and issues
"""

import re
from typing import List, Tuple, Set

from models import UserQuestion, ClassificationResult, SupportResponse, SupportCategory, Priority
from config import ResponseTemplates, SuggestedActions


class TechnicalHandler:
    """
    Handles technical support questions with specialized responses
    Includes severity assessment and escalation logic
    """
    
    def __init__(self):
        """Initialize technical handler with templates and patterns"""
        self.response_templates = ResponseTemplates.TECHNICAL_TEMPLATES
        self.suggested_actions = SuggestedActions.TECHNICAL_ACTIONS
        
        # Technical issue patterns for detailed analysis
        self.server_patterns = [
            r'server.*down',
            r'server.*not.*responding',
            r'server.*offline',
            r'server.*unavailable',
            r'website.*down'
        ]
        
        self.login_patterns = [
            r'can\'?t.*log',
            r'unable.*log',
            r'login.*fail',
            r'password.*not.*work',
            r'authentication.*error'
        ]
        
        self.performance_patterns = [
            r'slow.*performance',
            r'taking.*long',
            r'timeout',
            r'hanging',
            r'freezing'
        ]
        
        self.api_patterns = [
            r'api.*error',
            r'api.*not.*work',
            r'endpoint.*fail',
            r'request.*fail',
            r'integration.*issue'
        ]
        
        self.configuration_patterns = [
            r'setup.*help',
            r'configuration.*issue',
            r'install.*problem',
            r'deployment.*error',
            r'settings.*wrong'
        ]
        
        self.connection_patterns = [
            r'connection.*fail',
            r'can\'?t.*connect',
            r'network.*issue',
            r'connectivity.*problem',
            r'unreachable'
        ]
        
        # Critical indicators that require immediate escalation
        self.critical_indicators = {
            'production', 'prod', 'live', 'critical', 'emergency',
            'urgent', 'down', 'outage', 'breach', 'security'
        }
        
        # Error code patterns
        self.error_codes = {
            '500': 'Internal Server Error',
            '502': 'Bad Gateway',
            '503': 'Service Unavailable',
            '504': 'Gateway Timeout',
            '404': 'Not Found',
            '403': 'Forbidden',
            '401': 'Unauthorized'
        }
    
    def handle(self, question: UserQuestion, classification: ClassificationResult) -> SupportResponse:
        """
        Process technical question and generate appropriate response
        
        Args:
            question: The user's technical question
            classification: Classification result from the classifier
            
        Returns:
            SupportResponse with technical-specific response and actions
        """
        text_lower = question.text.lower()
        
        # Identify specific technical issue
        issue_type, confidence_boost = self._identify_technical_issue(text_lower)
        
        # Assess severity and criticality
        severity_level = self._assess_severity(text_lower, question.text)
        
        # Generate response
        response_text = self._generate_response(issue_type, text_lower, question.text, severity_level)
        
        # Get suggested actions
        actions = self._get_suggested_actions(issue_type, text_lower, severity_level)
        
        # Determine escalation and priority
        escalation_needed, priority = self._assess_escalation(issue_type, severity_level, text_lower)
        
        # Adjust confidence
        adjusted_confidence = min(0.95, classification.confidence + confidence_boost)
        
        # Create response
        response = SupportResponse(
            category=SupportCategory.TECHNICAL,
            response=response_text,
            suggested_actions=actions,
            escalation_needed=escalation_needed,
            priority=priority,
            confidence=adjusted_confidence,
            processing_time_ms=classification.processing_time_ms
        )
        
        return response
    
    def _identify_technical_issue(self, text: str) -> Tuple[str, float]:
        """Identify specific type of technical issue"""
        # Server/Infrastructure issues
        if any(re.search(pattern, text) for pattern in self.server_patterns):
            return 'server_down', 0.2
        
        # Login/Authentication issues
        if any(re.search(pattern, text) for pattern in self.login_patterns):
            return 'login_problem', 0.15
        
        # Performance issues
        if any(re.search(pattern, text) for pattern in self.performance_patterns):
            return 'performance_issue', 0.1
        
        # API issues
        if any(re.search(pattern, text) for pattern in self.api_patterns):
            return 'api_error', 0.15
        
        # Configuration issues
        if any(re.search(pattern, text) for pattern in self.configuration_patterns):
            return 'configuration_help', 0.1
        
        # Connection issues
        if any(re.search(pattern, text) for pattern in self.connection_patterns):
            return 'connection_problem', 0.1
        
        # Default technical issue
        return 'default', 0.0
    
    def _assess_severity(self, text_lower: str, original_text: str) -> str:
        """Assess the severity level of the technical issue"""
        # Critical severity indicators
        if any(indicator in text_lower for indicator in self.critical_indicators):
            return 'critical'
        
        # High severity indicators
        high_severity = ['not working', 'completely broken', 'cant access', 'error', 'fail']
        if any(indicator in text_lower for indicator in high_severity):
            return 'high'
        
        # Medium severity indicators
        medium_severity = ['slow', 'sometimes', 'intermittent', 'occasional']
        if any(indicator in text_lower for indicator in medium_severity):
            return 'medium'
        
        # Default to low severity
        return 'low'
    
    def _generate_response(self, issue_type: str, text_lower: str, original_text: str, severity: str) -> str:
        """Generate appropriate response text"""
        # Get base response template
        base_response = self.response_templates.get(issue_type, self.response_templates['default'])
        response = base_response
        
        # Add severity-specific context
        if severity == 'critical':
            response += " Given the critical nature of this issue, I'm flagging this for immediate escalation to our infrastructure team."
        elif severity == 'high':
            response += " This appears to be a high-priority issue that needs prompt attention."
        
        # Add error code context if detected
        error_codes = re.findall(r'\b([45]\d{2})\b', original_text)
        if error_codes:
            for code in error_codes:
                if code in self.error_codes:
                    response += f" I notice error code {code} ({self.error_codes[code]}), which helps narrow down the issue."
        
        # Add environment context
        if any(env in text_lower for env in ['production', 'prod', 'live']):
            response += " Since this affects production environment, we'll treat this with high priority."
        elif any(env in text_lower for env in ['staging', 'test', 'dev']):
            response += " I see this is in a non-production environment, which helps with troubleshooting options."
        
        # Add timing context
        if any(time in text_lower for time in ['started', 'began', 'since']):
            response += " Understanding when this started will help identify the root cause."
        
        return response
    
    def _get_suggested_actions(self, issue_type: str, text: str, severity: str) -> List[str]:
        """Get relevant suggested actions for the technical issue"""
        # Get base actions
        base_actions = self.suggested_actions.get(issue_type, self.suggested_actions['default'])
        actions = base_actions.copy()
        
        # Add severity-specific actions
        if severity == 'critical':
            actions.insert(0, "🚨 Contact on-call engineer immediately: +1-800-EMERGENCY")
            actions.insert(1, "Check system status page for known issues")
        
        # Add issue-specific actions
        if issue_type == 'server_down':
            if 'database' in text:
                actions.append("Check database connection status")
            if 'memory' in text or 'ram' in text:
                actions.append("Monitor server memory usage")
        
        elif issue_type == 'api_error':
            actions.extend([
                "Test API endpoints with Postman or curl",
                "Verify API key/token validity",
                "Check API rate limiting status"
            ])
        
        elif issue_type == 'performance_issue':
            actions.extend([
                "Run performance profiling tools",
                "Check resource utilization (CPU, memory, disk)",
                "Review recent code deployments"
            ])
        
        elif issue_type == 'login_problem':
            if 'password' in text:
                actions.insert(1, "Ensure caps lock is off and correct keyboard layout")
            if 'two factor' in text or '2fa' in text:
                actions.append("Check two-factor authentication device/app")
        
        # Add monitoring actions for ongoing issues
        if severity in ['critical', 'high']:
            actions.append("Set up monitoring alerts for this issue")
        
        return actions
    
    def _assess_escalation(self, issue_type: str, severity: str, text: str) -> Tuple[bool, Priority]:
        """Determine if escalation is needed and set priority"""
        escalation_needed = False
        priority = Priority.MEDIUM
        
        # Critical severity always escalates
        if severity == 'critical':
            escalation_needed = True
            priority = Priority.URGENT
        
        # High-impact issues
        elif severity == 'high':
            escalation_needed = True
            priority = Priority.HIGH
        
        # Specific issue types that need escalation
        elif issue_type in ['server_down', 'api_error']:
            escalation_needed = True
            priority = Priority.HIGH
        
        # Production environment issues
        elif any(env in text for env in ['production', 'prod', 'live']):
            escalation_needed = True
            priority = Priority.HIGH
        
        # Security-related issues
        elif any(sec in text for sec in ['security', 'breach', 'hack', 'vulnerability']):
            escalation_needed = True
            priority = Priority.URGENT
        
        # Multiple users affected
        elif any(multi in text for multi in ['everyone', 'all users', 'multiple', 'widespread']):
            escalation_needed = True
            priority = Priority.HIGH
        
        return escalation_needed, priority
    
    def get_technical_insights(self, text: str) -> dict:
        """Extract technical-specific insights from the question"""
        insights = {
            'issue_type': None,
            'severity': 'low',
            'environment': 'unknown',
            'error_codes': [],
            'affected_components': [],
            'timeline_mentioned': False,
            'multiple_users_affected': False
        }
        
        # Identify issue type
        issue_type, _ = self._identify_technical_issue(text.lower())
        insights['issue_type'] = issue_type
        
        # Assess severity
        insights['severity'] = self._assess_severity(text.lower(), text)
        
        # Identify environment
        if any(env in text.lower() for env in ['production', 'prod', 'live']):
            insights['environment'] = 'production'
        elif any(env in text.lower() for env in ['staging', 'stage']):
            insights['environment'] = 'staging'
        elif any(env in text.lower() for env in ['test', 'testing']):
            insights['environment'] = 'testing'
        elif any(env in text.lower() for env in ['dev', 'development']):
            insights['environment'] = 'development'
        
        # Extract error codes
        error_codes = re.findall(r'\b([45]\d{2})\b', text)
        insights['error_codes'] = error_codes
        
        # Identify affected components
        components = ['server', 'database', 'api', 'website', 'app', 'service', 'network']
        insights['affected_components'] = [comp for comp in components if comp in text.lower()]
        
        # Check for timeline mentions
        timeline_words = ['started', 'began', 'since', 'ago', 'yesterday', 'today', 'morning']
        insights['timeline_mentioned'] = any(word in text.lower() for word in timeline_words)
        
        # Check for multiple users affected
        multi_user_words = ['everyone', 'all users', 'multiple', 'widespread', 'team', 'colleagues']
        insights['multiple_users_affected'] = any(word in text.lower() for word in multi_user_words)
        
        return insights
    
    def extract_error_details(self, text: str) -> dict:
        """Extract detailed error information from the text"""
        details = {
            'error_codes': [],
            'stack_traces': False,
            'specific_errors': [],
            'browser_mentioned': None,
            'os_mentioned': None
        }
        
        # Extract HTTP error codes
        http_codes = re.findall(r'\b([45]\d{2})\b', text)
        details['error_codes'].extend(http_codes)
        
        # Check for stack traces
        if any(trace in text.lower() for trace in ['stack trace', 'traceback', 'exception']):
            details['stack_traces'] = True
        
        # Extract specific error messages
        error_patterns = [
            r'error:?\s*(.+?)(?:\n|$)',
            r'exception:?\s*(.+?)(?:\n|$)',
            r'failed:?\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            details['specific_errors'].extend(matches)
        
        # Identify browser
        browsers = ['chrome', 'firefox', 'safari', 'edge', 'opera']
        for browser in browsers:
            if browser in text.lower():
                details['browser_mentioned'] = browser
                break
        
        # Identify operating system
        operating_systems = ['windows', 'mac', 'linux', 'ubuntu', 'ios', 'android']
        for os_name in operating_systems:
            if os_name in text.lower():
                details['os_mentioned'] = os_name
                break
        
        return details