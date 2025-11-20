from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data_analysis, history_router
from database.database import init_db

app = FastAPI(title="SmartDataAnalyst API", version="1.0")


@app.on_event("startup")
async def on_startup():
    await init_db()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(data_analysis.router)
app.include_router(history_router.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "SmartDataAnalyst API is running"}