from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.dashboard_service import generate_dataset_summary

router = APIRouter(prefix="/api/dashboard", tags=['Analysis Dashboard'])

class SummaryRequest(BaseModel):
    file_id: str


@router.post("/summary")
def get_summary(request: SummaryRequest):
    csv_path = f"data/{request.file_id}"
    print(f"csv_path: {csv_path}")
    try:
        data = generate_dataset_summary(csv_path)
        print(f"data: {data}")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    