from pydantic import BaseModel
from typing import Optional, Dict

class MemoryItem(BaseModel):
    memory_id: str
    text: str
    metadata: Dict