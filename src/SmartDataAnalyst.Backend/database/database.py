from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.history import HistoryQuery, HistorySession

DATABASE_URL = "sqlite+aiosqlite:///./smartdataanyalyst.db"

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False, # set True for SQL logs
    future=True
)

async def init_db():
    """Create DB tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session