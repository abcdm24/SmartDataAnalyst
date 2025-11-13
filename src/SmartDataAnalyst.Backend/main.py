from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data_analysis


app = FastAPI(title="SmartDataAnalyst API", version="1.0")

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


@app.get("/")
def root():
    return {"status": "ok", "message": "SmartDataAnalyst API is running"}