from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class UserQuestion:
    text: str
    metadata: Dict[str, Any] = None