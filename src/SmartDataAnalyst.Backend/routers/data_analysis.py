from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import pandas as pd
import os
from core.agent import analyze_query

router = APIRouter(prefix="/api/data", tags=["Data Analysis"])

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    df = pd.read_csv(filepath)
    preview = df.head().to_dict(orient="records")
    return {"filename": file.filename, "columns": list(df.columns), "preview": preview}


@router.post("/query")
async def query_data(filename: str = Form(...), question: str = Form(...)):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = pd.read_csv(filepath)
    answer = analyze_query(df, question)
    return {"answer": answer}