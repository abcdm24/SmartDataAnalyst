import os
# from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data_analysis, history_router, dashboard_router
from database.database import init_db
from dotenv import load_dotenv

load_dotenv() # loads .env file

app = FastAPI(title="SmartDataAnalyst API", version="1.0")

# app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.on_event("startup")
async def on_startup():
    await init_db()

frontend_origin= os.getenv("FRONTEND_ORIGIN","http://localhost:5173")

origins = [
    frontend_origin,
    "http://localhost:5173",
    "https://kind-stone-0dcb77a00.3.azurestaticapps.net"
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
app.include_router(dashboard_router.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "SmartDataAnalyst API is running"}