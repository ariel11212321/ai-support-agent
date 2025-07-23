"""
AI Support Agent - Configuration Settings
Centralized configuration for the entire application
"""

import os
from pathlib import Path
from typing import Dict, Set, List


class Config:
    """Main configuration class for the AI Support Agent"""
    
    # Application Info
    APP_NAME = "AI Support Agent"
    APP_VERSION = "2.0.0"
    APP_DESCRIPTION = "Enterprise-grade AI support classification system"
    
    # Performance Settings
    MAX_WORKERS = 4
    WORKER_TIMEOUT_SECONDS = 30
    MAX_QUEUE_SIZE = 100
    
    # Classification Settings
    MIN_CONFIDENCE_THRESHOLD = 0.3
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    DEFAULT_CONFIDENCE = 0.5
    
    # Cache Settings
    CACHE_MAX_SIZE = 1000
    CACHE_TTL_SECONDS = 3600  # 1 hour
    ENABLE_CACHE = True
    
    # File Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Data Files
    CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
    ANALYTICS_FILE = DATA_DIR / "analytics.json"
    CACHE_FILE = DATA_DIR / "cache.json"
    LOG_FILE = LOGS_DIR / "agent.log"
    
    # CLI Settings
    CLI_PROMPT = "Support Agent 🤖 › "
    CLI_WELCOME_MESSAGE = f"🤖 {APP_NAME} v{APP_VERSION}"
    CLI_HELP_TEXT = """
Available commands:
  help     - Show this help message
  stats    - Show current statistics
  clear    - Clear screen
  quit     - Exit the application
  
Just type your question to get support!
"""
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)


class Keywords:
    """Keyword definitions for classification"""
    
    BILLING_KEYWORDS: Set[str] = {
        'billing', 'payment', 'invoice', 'charge', 'subscription', 'refund',
        'cancel', 'upgrade', 'downgrade', 'plan', 'pricing', 'cost', 'fee',
        'account', 'balance', 'credit', 'card', 'receipt', 'transaction',
        'money', 'dollar', 'price', 'expensive', 'cheap', 'free', 'trial'
    }
    
    TECHNICAL_KEYWORDS: Set[str] = {
        'server', 'down', 'error', 'bug', 'crash', 'slow', 'performance',
        'login', 'password', 'api', 'integration', 'configuration', 'setup',
        'install', 'update', 'troubleshoot', 'connection', 'timeout',
        'database', 'ssl', 'certificate', 'backup', 'restore', 'deploy',
        'code', 'website', 'app', 'application', 'system', 'network'
    }
    
    GENERAL_KEYWORDS: Set[str] = {
        'how', 'what', 'when', 'where', 'why', 'feature', 'documentation',
        'tutorial', 'guide', 'help', 'support', 'contact', 'hours',
        'available', 'information', 'about', 'demo', 'trial', 'learn',
        'explain', 'understand', 'know', 'tell', 'show', 'example'
    }
    
    URGENCY_KEYWORDS: Set[str] = {
        'urgent', 'emergency', 'critical', 'immediate', 'asap', 'now',
        'quickly', 'fast', 'priority', 'important', 'serious', 'down',
        'broken', 'not working', 'failed', 'production', 'live'
    }


class Patterns:
    """Regex patterns for advanced classification"""
    
    # Financial patterns
    MONEY_PATTERN = r'\$[\d,]+\.?\d*'
    CURRENCY_PATTERN = r'(\$|€|£|¥)\s*\d+'
    
    # Technical patterns
    ERROR_CODE_PATTERN = r'error.*\d+|status.*\d+|code.*\d+'
    HTTP_STATUS_PATTERN = r'[45]\d{2}'  # 4xx, 5xx errors
    IP_ADDRESS_PATTERN = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Time patterns
    TIME_PATTERN = r'\d{1,2}:\d{2}(?::\d{2})?'
    DATE_PATTERN = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    
    # Connection issues
    CONNECTION_PATTERN = r'can\'?t.*connect|unable.*connect|connection.*fail'
    LOGIN_PATTERN = r'can\'?t.*log|unable.*log|login.*fail'


class ResponseTemplates:
    """Template responses for each category"""
    
    BILLING_TEMPLATES: Dict[str, str] = {
        'cancel_subscription': "To cancel your subscription, please visit your account settings or contact our billing team directly.",
        'payment_issue': "For payment issues, please check your payment method and ensure your card details are up to date.",
        'refund_request': "For refund requests, please provide your order number and reason for the refund request.",
        'upgrade_plan': "You can upgrade your plan anytime from your account dashboard. Need help choosing the right plan?",
        'invoice_inquiry': "You can find all your invoices in the billing section of your account dashboard.",
        'pricing_question': "For pricing information, please visit our plans page or contact our sales team.",
        'default': "I'm here to help with your billing question. Let me connect you with our billing specialist."
    }
    
    TECHNICAL_TEMPLATES: Dict[str, str] = {
        'server_down': "I understand your server is experiencing issues. Let's troubleshoot this together.",
        'login_problem': "Login problems can be frustrating. Let's get you back into your account quickly.",
        'performance_issue': "Performance issues can have various causes. Let's identify and resolve the bottleneck.",
        'api_error': "API errors need immediate attention. Let me help you diagnose the issue.",
        'configuration_help': "Configuration issues are common. I'll guide you through the setup process.",
        'connection_problem': "Connection issues can be network-related. Let's check your connectivity.",
        'default': "I'm here to help resolve your technical issue. Let's start with some basic troubleshooting."
    }
    
    GENERAL_TEMPLATES: Dict[str, str] = {
        'how_to_question': "I'd be happy to guide you through this process step by step.",
        'feature_inquiry': "I can explain how this feature works and help you get started.",
        'documentation_request': "Let me provide you with the relevant documentation and resources.",
        'contact_info': "Here are the best ways to reach our support team.",
        'demo_request': "I can help you get started with a demo or trial.",
        'general_info': "Let me provide you with the information you're looking for.",
        'default': "Thank you for your question. I'm here to help with any information you need."
    }


class SuggestedActions:
    """Predefined suggested actions for each category"""
    
    BILLING_ACTIONS: Dict[str, List[str]] = {
        'cancel_subscription': [
            "Visit Account Settings > Subscription",
            "Contact billing team at billing@company.com",
            "Call 1-800-BILLING for immediate assistance"
        ],
        'payment_issue': [
            "Check payment method in account settings",
            "Verify card details and expiration date",
            "Contact your bank if payment is declined"
        ],
        'refund_request': [
            "Locate your order/transaction number",
            "Submit refund request through support portal",
            "Allow 3-5 business days for processing"
        ],
        'default': [
            "Contact billing support at billing@company.com",
            "Call our billing helpline: 1-800-BILLING",
            "Visit our billing FAQ section"
        ]
    }
    
    TECHNICAL_ACTIONS: Dict[str, List[str]] = {
        'server_down': [
            "Check server status at status.company.com",
            "Verify network connectivity",
            "Review server logs for error messages",
            "Contact infrastructure team if issue persists"
        ],
        'login_problem': [
            "Try resetting your password",
            "Clear browser cache and cookies",
            "Check if account is locked",
            "Use password recovery option"
        ],
        'api_error': [
            "Check API documentation for correct usage",
            "Verify authentication tokens",
            "Review request format and parameters",
            "Check API rate limits and quotas"
        ],
        'default': [
            "Describe the exact error message",
            "Note when the issue started",
            "Try basic troubleshooting steps",
            "Contact technical support with details"
        ]
    }
    
    GENERAL_ACTIONS: Dict[str, List[str]] = {
        'how_to_question': [
            "Check our documentation at docs.company.com",
            "Watch video tutorials on our YouTube channel",
            "Join our community forum for discussions",
            "Contact support for personalized guidance"
        ],
        'feature_inquiry': [
            "Explore the feature in our demo environment",
            "Read the feature documentation",
            "Watch feature-specific tutorials",
            "Contact sales for detailed discussions"
        ],
        'default': [
            "Browse our help center",
            "Contact our support team",
            "Check our community forum",
            "Visit our website for more information"
        ]
    }


class Colors:
    """Color definitions for Rich CLI output"""
    
    # Category colors
    BILLING_COLOR = "yellow"
    TECHNICAL_COLOR = "red"
    GENERAL_COLOR = "blue"
    
    # Status colors
    SUCCESS_COLOR = "green"
    WARNING_COLOR = "orange"
    ERROR_COLOR = "red"
    INFO_COLOR = "cyan"
    
    # UI colors
    PROMPT_COLOR = "bright_blue"
    HEADER_COLOR = "bright_green"
    ACCENT_COLOR = "magenta"


class Scoring:
    """Scoring weights for classification"""
    
    # Base scores per keyword match
    KEYWORD_BASE_SCORE = 2.0
    PATTERN_MATCH_SCORE = 3.0
    URGENCY_BOOST = 2.0
    
    # Category weights
    BILLING_WEIGHT = 1.0
    TECHNICAL_WEIGHT = 1.2  # Technical issues slightly prioritized
    GENERAL_WEIGHT = 0.8    # General questions slightly deprioritized
    
    # Confidence calculation
    CONFIDENCE_SMOOTHING = 0.1
    MIN_FEATURES_FOR_HIGH_CONFIDENCE = 3