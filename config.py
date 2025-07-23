class Config:
    # Classification Model
    CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
    CLASSIFICATION_LABELS = ["billing", "technical", "general"]
    
    # Response Generation Models
    RESPONSE_MODEL = "microsoft/DialoGPT-medium"  # Conversational AI
    # Alternative: "facebook/blenderbot-400M-distill" for better responses
    
    # Performance
    CACHE_SIZE = 100
    MAX_WORKERS = 4
    TIMEOUT_SECONDS = 30
    
    # AI Response Prompts by Category
    RESPONSE_PROMPTS = {
        "billing": "You are a helpful billing support specialist. A customer asked: '{question}'. Provide a helpful, professional response about billing matters.",
        "technical": "You are a technical support expert. A customer reported: '{question}'. Provide a helpful troubleshooting response with clear steps.",
        "general": "You are a friendly customer service representative. A customer asked: '{question}'. Provide a helpful and informative response."
    }