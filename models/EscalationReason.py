from enum import Enum

class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    COMPLEX_ISSUE = "complex_issue"
    SENTIMENT_NEGATIVE = "sentiment_negative"
    MANUAL_REQUEST = "manual_request"
    TECHNICAL_LIMITATION = "technical_limitation"