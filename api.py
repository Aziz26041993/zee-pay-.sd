
from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(
    title="ZEE PAY API",
    description="ZEE PAY Sudan Digital Wallet API",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "app": "ZEE PAY",
        "message": "Welcome to ZEE PAY API",
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "zee-pay-api",
        "currency": "SDG",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
