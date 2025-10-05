import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List

# Initialize the FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Define Request Body Model
class TelemetryRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# Load Data
try:
    # Path relative to this file (api/index.py)
    DATA_PATH = Path(__file__).parent.parent / "data" / "telemetry.json"
    df = pd.read_json(DATA_PATH)
except FileNotFoundError:
    df = pd.DataFrame()

# Define API Endpoint
@app.post("/process-telemetry")
def process_telemetry(request: TelemetryRequest):
    if df.empty:
        return {"error": "Telemetry data not found on server."}

    results_list = []
    
    for region in request.regions:
        region_df = df[df['region'] == region]

        if region_df.empty:
            continue

        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_pct'].mean()
        breaches = int((region_df['latency_ms'] > request.threshold_ms).sum())

        region_metrics = {
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches,
        }
        results_list.append(region_metrics)
    
    return {"regions": results_list}
