
from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(
    title="ZEE PAY API",
    description="Central backend for ZEE PAY",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "app": "ZEE PAY",
        "message": "Welcome to ZEE PAY API",
        "currency": "SDG",
        "status": "development"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "server": "ZEE PAY",
        "time": datetime.now(timezone.utc).isoformat(),
        "mode": "development"
    }
