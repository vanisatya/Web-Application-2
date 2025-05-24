from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json
import time
import os

app = FastAPI()

# Allow any frontend to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory and file to log metrics
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
metrics_file = os.path.join(log_folder, "apm_metrics.log")

def log_metric(data):
    data["logged_at"] = datetime.utcnow().isoformat()
    with open(metrics_file, "a") as file:
        file.write(json.dumps(data) + "\n")

# ➡️ Middleware: Track all HTTP requests
@app.middleware("http")
async def track_api_performance(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
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

# ➡️ Serve static files like CSS, JS, images
app.mount("/static", StaticFiles(directory="static"), name="static")

# ➡️ Routes for static HTML pages
@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    return FileResponse("static/index.html")

@app.get("/generic.html", response_class=HTMLResponse)
async def serve_certifications():
    return FileResponse("static/generic.html")

@app.get("/elements.html", response_class=HTMLResponse)
async def serve_skills():
    return FileResponse("static/elements.html")

@app.get("/contact.html", response_class=HTMLResponse)
async def serve_contact():
    return FileResponse("static/contact.html")

# ➡️ Custom event tracker (for throughput)
@app.post("/apm/track_event/")
async def track_event(event: dict):
    event["type"] = "custom_event"
    event["timestamp"] = datetime.utcnow().isoformat()
    log_metric(event)
    return {"status": "success", "message": "Event tracked"}

# ➡️ Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "UP", "time": datetime.utcnow().isoformat()}
