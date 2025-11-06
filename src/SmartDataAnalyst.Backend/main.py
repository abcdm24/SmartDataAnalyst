from fastapi import FastAPI
from routers import data_analysis


app = FastAPI(title="SmartDataAnalyst API", version="1.0")


app.include_router(data_analysis.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "SmartDataAnalyst API is running"}