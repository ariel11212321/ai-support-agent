from enum import Enum

class TicketStatus(str, Enum):
    NEW = "new"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    PROCESSING = "processing"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FAILED = "failed"