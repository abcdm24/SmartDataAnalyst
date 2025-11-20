# from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, ForeignKey
# from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
#from database import Base
import uuid
from typing import List, Optional

# class History(SQLModel, table=True):
#     __tablename__ = "history"

#     id: Optional[int] = Field(default=None, primary_key=True)
#     timestamp: datetime = Field(default_factory=datetime.utcnow)
#     query: str
#     answer: str
#     status_sequence: List[str] = Field(
#         sa_column=Column(JSON),
#         default_factory=list
#     )
#     source: Optional[str] = Field(default="agent")
#     metadata: Optional[dict] = Field(
#         default=None,
#         sa_column=Column(JSON)
#     )



class HistorySession(SQLModel, table=True):
    __tablename__ = "history_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    file_name:str = Field(nullable=False) # = Field(String, nullable=False)
    upload_date: datetime = Field(default_factory=datetime.utcnow)

    #queries = Relationship("HistoryQuery", back_populates="session", cascade="all, delete-orphan")
     
    queries: List["HistoryQuery"] = Relationship(back_populates="session")


class HistoryQuery(SQLModel, table=True):
    __tablename__ = "history_queries"

    id:str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(foreign_key="history_sessions.id")
    question: str = Field(nullable=False)
    answer: str = Field(nullable=False) 
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[HistorySession] = Relationship(back_populates="queries")
