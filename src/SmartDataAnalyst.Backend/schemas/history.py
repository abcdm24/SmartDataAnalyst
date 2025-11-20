from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# class HistoryCreate(BaseModel):
#     query: str
#     answer: str
#     status_sequence: List[str] = []
#     source: Optional[str] = "agent"
#     metadata: Optional[dict] = None

# class HistoryRead(BaseModel):
#     id: int
#     timestamp: datetime
#     query: str
#     answer: str
#     status_sequence: List[str]
#     source: str
#     metadata: Optional[dict]

#     class Config:
#         orm_mode = True
        
class HistoryQuery(BaseModel):
    question: str
    answer: str
    timestamp: datetime

    class Config:
        orm_mode = True

class HistorySession(BaseModel):
    id: str
    file_name: str
    upload_date: datetime
    queries: List[HistoryQuery]

    class Config:
        orm_mode = True

class HistoryListItem(BaseModel):
    id: str
    file_name: str
    upload_date: datetime
    query_count: int