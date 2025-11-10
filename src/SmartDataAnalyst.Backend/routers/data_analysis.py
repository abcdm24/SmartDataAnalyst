from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import pandas as pd
import os
# from core.agent import analyze_query
from core.agent_v13 import Agent_v13

router = APIRouter(prefix="/api/data", tags=["Data Analysis"])

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

AGENTS = {}

def get_agent_for_file(filename):
    if filename not in AGENTS:
        AGENTS[filename] = Agent_v13()
    return AGENTS[filename]


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
    # agent = Agent_v13()
    agent = get_agent_for_file(filename)
    answer = await agent.analyze_query(df, question)
    return {"answer": answer}


@router.post("/ask-followup")
async def ask_followup(filename: str = Form(...), question: str = Form(...)):
    """
    Continue the conversation with context memory.
    """
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = pd.read_csv(filepath)
    # agent = Agent_v13()
    agent = get_agent_for_file(filename)
    answer = await agent.ask_followup(df, question)
    return {"answer": answer}




