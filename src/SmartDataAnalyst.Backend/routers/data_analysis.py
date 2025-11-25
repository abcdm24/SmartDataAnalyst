from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import pandas as pd
import os
import chardet
# from core.agent import analyze_query
from core.agent_v15 import Agent_v15
import asyncio
from datetime import datetime
from services.history_service import HistoryService
from database.database import get_session

history_service = HistoryService()

router = APIRouter(prefix="/api/data", tags=["Data Analysis"])

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

active_connections = {} # {filename: [WebSocket, ...]}
STATUS_HISTORY = {} # {filename: [{status,time}, ...]}

AGENTS = {}
AGENT_STATUSES = {}


async def notify_status(filename: str, status: str):
    """Notify all connected WebSocket clients of staus change"""
    if filename in active_connections:
        for ws in list(active_connections[filename]):
            try:
                await ws.send_json({"status": status})
            except Exception:
                active_connections[filename].remove(ws)


def record_status(filename: str, status: str):
    """Log each status change with timestamp"""
    if filename not in STATUS_HISTORY:
        STATUS_HISTORY[filename] = []
    STATUS_HISTORY[filename].append({
        "status": status,
        "time": datetime.now().isoformat()
    })
    

def get_agent_for_file(filename):
    if filename not in AGENTS:
        agent = Agent_v15(filename)
        AGENTS[filename] = agent

        def handle_status_change(filename, new_status):
            AGENT_STATUSES[filename] = new_status
            print(f"[AgentStatus] {filename} -> {AGENT_STATUSES[filename]}")
        
        agent.on_status_change = handle_status_change
        # AGENT_STATUSES[filename] = agent.get_status()
    return AGENTS[filename]


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    with open(filepath, "rb") as raw:
        result = chardet.detect(raw.read(50000))
        encoding = result["encoding"] or "utf-8"
    
    try:
        df = pd.read_csv(filepath, encoding=encoding)
    except pd.errors.ParserError:
        df = pd.read_csv(filepath, encoding=encoding, sep=";")

    df = df.dropna(how="all", axis=0)    
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    
    # df = pd.read_csv(filepath)
    preview = df.head().to_dict(orient="records")
    print(preview)

    # Save history entry for upload
    async for db in get_session():
        await history_service.add_entry(
            db,
            # event_type="upload",
            file_name=file.filename,
            question="Uploaded file",
            answer=f"File uploaded with {len(df)} rows abd {len(df.columns)} columns"
        )

    return {"filename": file.filename, "columns": list(df.columns), "preview": preview}


@router.post("/query")
async def query_data(filename: str = Form(...), question: str = Form(...)):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = pd.read_csv(filepath)
    # agent = Agent_v13()
    agent = get_agent_for_file(filename)

    if not agent:
        return JSONResponse(status_code=400, content={"error": "Agent not initialized"})
    
    await agent._set_status("processing")
    record_status(filename, "processing")
    await notify_status(filename, "processing")
    await asyncio.sleep(2)

    #def run_query_task():
    try:
        if asyncio.iscoroutinefunction(agent.analyze_query):
            print("coroutine")
            # asyncio.run(agent.analyze_query(df, question))
            answer = await agent.analyze_query(df, question)
        else:
            print("non coroutine")
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_execute(None, agent.analyze_query, df, question)
        
        agent.last_activity_time = asyncio.get_event_loop().time()
        
        # Save history
        async for db in get_session():
            await history_service.add_entry(
                db,
                # event_type="query",
                file_name=filename,
                question=question,
                answer=answer
            )

        return {"answer": answer}        
    
    except Exception as e:
        print(f"[Agent] Background query error: {e}")
    finally:
        await agent._set_status("active")
        record_status(filename, "active")
        await notify_status(filename, "active")
        await asyncio.sleep(2)

    # background_task.add_task(run_query_task)

    # answer = await agent.analyze_query(df, question)
    


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

    # Save History
    async for db in get_session():
        await history_service.add_entry(
            db,
            # event_type="followup",
            filename=filename,
            question=question,
            answer=answer
        )

    return {"answer": answer}


@router.get("/agent-status")
async def get_agent_status(filename: str):
    """
    Returns the current status of the agent for a given file:
    'active' if anything/summarizing, otherwise 'idle'
    """

    agent = get_agent_for_file(filename)

    if not agent:
        return {"status": "not_initialized"}
    
    # agent = AGENTS[filename]
    # return {"status": agent.get_status()}
    # print("Called get_status")

    status = AGENT_STATUSES.get(filename, agent.get_status())
    print(f"Status: {status}")
    return {"status": status}

@router.get("/agent-status-history")
async def get_status_history(filename: str):
    return STATUS_HISTORY.get(filename, [])

@router.websocket("/ws/agent-status")
async def websocket_endpoint(websocket: WebSocket, filename: str):
    await websocket.accept()
    if filename not in active_connections:
        active_connections[filename] = []
    active_connections[filename].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[filename].remove(websocket)