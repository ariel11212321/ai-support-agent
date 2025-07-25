from typing import Optional, List, Tuple
import re

class InputValidator:
    """Comprehensive input validation class for the support system"""
    
    # Configuration constants
    MAX_QUESTION_LENGTH = 5000
    MIN_QUESTION_LENGTH = 3
    MAX_WORKER_ID_LENGTH = 50
    
    # Patterns for validation
    DANGEROUS_PATTERNS = [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',              # JavaScript protocol
        r'on\w+\s*=',               # Event handlers
        r'eval\s*\(',               # eval() calls
        r'exec\s*\(',               # exec() calls
        r'import\s+os',             # OS imports
        r'__import__',              # Dynamic imports
        r'subprocess',              # Subprocess calls
    ]
    
    SUSPICIOUS_SQL_PATTERNS = [
        r'\b(drop|delete|truncate|alter)\s+table\b',
        r'\bunion\s+select\b',
        r';\s*(drop|delete|insert|update)',
        r'--\s*$',  # SQL comments
        r'/\*.*?\*/',  # SQL block comments
    ]
    
    @classmethod
    def validate_question(cls, question: str) -> Tuple[bool, Optional[str]]:
        """
        Validate question input with comprehensive checks
        
        Args:
            question: The question string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(question, str):
            return False, "Question must be a string"
        
        # Check length constraints
        question_stripped = question.strip()
        if len(question_stripped) < cls.MIN_QUESTION_LENGTH:
            return False, f"Question must be at least {cls.MIN_QUESTION_LENGTH} characters long"
        
        if len(question_stripped) > cls.MAX_QUESTION_LENGTH:
            return False, f"Question must be no more than {cls.MAX_QUESTION_LENGTH} characters long"
        
        # Check for dangerous patterns
        question_lower = question.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return False, "Question contains potentially unsafe content"
        
        # Check for SQL injection patterns
        for pattern in cls.SUSPICIOUS_SQL_PATTERNS:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return False, "Question contains suspicious SQL-like patterns"
        
        # Check for excessive whitespace or control characters
        if len(question_stripped) != len(question_stripped.replace('\x00', '')):
            return False, "Question contains null characters"
        
        # Check for reasonable character distribution (not all special characters)
        alphanumeric_count = sum(1 for c in question_stripped if c.isalnum() or c.isspace())
        if alphanumeric_count < len(question_stripped) * 0.5:
            return False, "Question contains too many special characters"
        
        return True, None
    
    @classmethod
    def validate_worker_id(cls, worker_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate worker ID format
        
        Args:
            worker_id: The worker ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(worker_id, str):
            return False, "Worker ID must be a string"
        
        worker_id_stripped = worker_id.strip()
        if len(worker_id_stripped) == 0:
            return False, "Worker ID cannot be empty"
        
        if len(worker_id_stripped) > cls.MAX_WORKER_ID_LENGTH:
            return False, f"Worker ID must be no more than {cls.MAX_WORKER_ID_LENGTH} characters"
        
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', worker_id_stripped):
            return False, "Worker ID can only contain letters, numbers, hyphens, and underscores"
        
        return True, None
    
    @classmethod
    def validate_command_args(cls, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate command line arguments
        
        Args:
            args: List of command line arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(args, list):
            return False, "Arguments must be a list"
        
        # Check for maximum number of arguments
        if len(args) > 10:
            return False, "Too many command line arguments"
        
        # Validate each argument
        for arg in args:
            if not isinstance(arg, str):
                return False, "All arguments must be strings"
            
            if len(arg) > 1000:
                return False, "Individual arguments are too long"
            
            # Check for dangerous patterns in arguments
            if any(re.search(pattern, arg.lower(), re.IGNORECASE) 
                   for pattern in cls.DANGEROUS_PATTERNS):
                return False, "Arguments contain potentially unsafe content"
        
        return True, None
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Sanitize input text by removing/escaping dangerous characters
        
        Args:
            text: The text to sanitize
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove null characters
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove any remaining control characters except newlines and tabs
        text = re.sub(r'[\x01-\x08\x0B-\x1F\x7F]', '', text)
        
        return text
