# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import time
import os

app = FastAPI()

# Allow any frontend to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["https://yourwebsite.com"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track metrics file
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
metrics_file = os.path.join(log_folder, "apm_metrics.log")

def log_metric(data):
    data["logged_at"] = datetime.utcnow().isoformat()
    with open(metrics_file, "a") as file:
        file.write(json.dumps(data) + "\n")

# Middleware to track all API requests
@app.middleware("http")
async def track_api_performance(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        # Log unhandled exceptions as errors
        error_metric = {
            "type": "exception",
            "error": str(e),
            "path": request.url.path,
            "client_ip": request.client.host
        }
        log_metric(error_metric)
        raise e

    process_time = (time.time() - start_time) * 1000  # ms
    metric = {
        "type": "request",
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": round(process_time, 2),
        "client_ip": request.client.host,
    }
    log_metric(metric)
    return response

# ➡️ For Throughput: Custom event tracker
@app.post("/apm/track_event/")
async def track_event(event: dict):
    event["type"] = "custom_event"
    event["timestamp"] = datetime.utcnow().isoformat()
    log_metric(event)
    return {"status": "success", "message": "Event tracked"}

# ➡️ For Availability monitoring
@app.get("/health")
async def health_check():
    return {"status": "UP", "time": datetime.utcnow().isoformat()}
