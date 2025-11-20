# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from typing import List, Optional

# from models.history import History
# from schemas.history import HistoryCreate

# class HistoryService:
#     """Handlers insert, fetch, delete for history."""

#     def __init__(self, session: AsyncSession):
#         self.session = session
    

#     async def add_history(self, data:HistoryCreate) -> History:
#         entry = History(
#             query=data.query,
#             answer=data.answer,
#             status_sequence=data.status_sequnece,
#             source=data.source,
#             metadata=data.metadata   
#         )
#         self.session.add(entry)
#         await self.session.commit()
#         await self.session.refresh(entry)
#         return entry
    
    
#     async def get_all(self) -> List[History]:
#         result = await self.session.execute(select(History))
#         return result.scalars.all()
    

#     async def get_by_id(self, id: int) -> Optional[History]:
#         result = await self.session.execute(select(History).where(History.id == id))
#         return result.scalars().first()
    

#     async def delete(self, id: int)->bool:
#         entry = await self.get_by_id(id)
#         if not entry:
#             return False
#         await self.session.delete(entry)
#         await self.session.commit()
#         return True
    
    
#     async def clear_all(self):
#         await self.session.execute("DELETE FROM history")
#         await self.session.commit()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from models.history import HistorySession, HistoryQuery

from models.history import HistorySession, HistoryQuery
import uuid
from datetime import datetime, timezone


class HistoryService:
    
    def __init__(self):
        pass


    async def add_entry(self, db: AsyncSession, file_name: str, question: str, answer: str):
        """
        Add a new history record:
        - If session for file does not exist, create it.
        - Add query entry.
        """

        # 1 Get or create session
        result = await db.execute(select(HistorySession).where(HistorySession.file_name== file_name))

        session_obj = result.unique().scalars().first()

        if not session_obj:
            session_obj = HistorySession(
                id=str(uuid.uuid4()),
                file_name=file_name,
                upload_date=datetime.utcnow()
            )
            db.add(session_obj)
            await db.flush()

        # 2 Add query record
        query_entry = HistoryQuery(
            id=str(uuid.uuid4()),
            session_id=session_obj.id,
            question=question,
            answer=answer,
            timestamp=datetime.now(timezone.utc)
        )

        db.add(query_entry)

        # 3 Commit to database
        await db.commit()
        return True

    async def get_all_history(self, db:AsyncSession):
        result = await db.execute(
            select(HistorySession)
            .options(joinedload(HistorySession.queries))
            .order_by(HistorySession.upload_date.desc())
        )

        sessions = result.unique().scalars().all()

        return[
            {
                "id": s.id,
                "file_name": s.file_name,
                "upload_date": s.upload_date,
                "query_count": len(s.queries)
            }
            for s in sessions
        ]

    async def get_history_by_id(self, session_id: str, db: AsyncSession):
        result = await db.execute(
            select(HistorySession)
            .where(HistorySession.id == session_id)
            .options(joinedload(HistorySession.queries))
        )

        return result.unique().scalars().first()


    async def clear_all_history(self, db: AsyncSession):
        await db.execute("DELETE FROM history_queries")
        await db.execute("DELETE FROM history_sessions")
        await db.commit()


    async def delete_session(self, session_id: str, db: AsyncSession):
        session = await self.get_history_by_id(session_id, db)
        if not session:
            return False
        
        await db.delete(session)
        await db.commit()
        return True
    