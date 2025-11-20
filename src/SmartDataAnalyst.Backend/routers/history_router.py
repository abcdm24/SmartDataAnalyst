# from fastapi import APIROuter, Depends, HTTPExecution
# from typing import List

# from schemas.history import HistoryCreate, HistoryRead
# from services.history_service import HistoryService
# from database import get_session
# from sqlalchemy.ext.asyncio import AsyncSession

# router = APIROuter(prefix="/api/history", tags=["History"])


# def get_service(session: AsyncSession = Depends(get_session)):
#     return HistoryService(session)


# @router.get("/", response_model=List[HistoryRead])
# async def get_all_history(service: HistoryService = Depends(get_service)):
#     return await service.get_all()


# @router.get("/{id}", response_model=HistoryRead)
# async def get_history_item(id: int, service: HistoryService = Depends(get_service)):
#     entry = await service.get_by_id(id)
#     if not entry:
#         raise HTTPExecution(status_cod=404, detail="History item not found")
#     return entry


# @router.delete("/{id}")
# async def delete_history_item(id: int, service: HistoryService = Depends(get_service)):
#     deleted = await service.delete(id)
#     if not deleted:
#         raise HTTPExecution(status_code=404, detail="History item not found")
#     return {"status": "delted","id": id}


# @router.delete("/")
# async def clear_history(service: HistoryService = Depends(get_service)):
#     await service.clear_all()
#     return {"status": "all_deleted"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_session
from services.history_service import HistoryService
from schemas.history import HistorySession, HistoryListItem

router = APIRouter(prefix="/api/history", tags=['History'])

history_service = HistoryService()

@router.get("", response_model=list[HistoryListItem])
async def list_history(db: AsyncSession = Depends(get_session)):
    return await history_service.get_all_history(db)

@router.get("/{session_id}", response_model=HistorySession)
async def get_history_details(session_id: str, db: AsyncSession=Depends(get_session)):
    session = await history_service.get_history_by_id(session_id, db)
    if not session:
        raise HTTPException(404, "History session not found")
    return session

@router.delete("/clear")
async def clear_history(db: AsyncSession = Depends(get_session)):
    await history_service.clear_all_history(db)
    return {"message": "History cleared"}

@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession=Depends(get_session)):
    result = await history_service.delete_session(session_id, db)
    if not result:
        raise HTTPException(404, "History session not found")
    return {"message": "Session deleted"}