class Config:
    CLASSIFICATION_MODEL = "distilbert-base-uncased"  
    CLASSIFICATION_LABELS = ["billing", "technical", "general"]
    
    CACHE_SIZE = 500  
    MAX_WORKERS = 2   
    TIMEOUT_SECONDS = 10  
  
    API_TIMEOUT = 10          
    API_RETRY_COUNT = 2       
  
    GROQ_API_KEY = "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"        
    
    