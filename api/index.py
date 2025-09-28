import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

# Initialize the FastAPI app
app = FastAPI()

# --- Enable CORS ---
# This allows POST requests from any origin, as required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["POST"], # Allows only POST requests
    allow_headers=["*"],
)

# --- Define Request Body Model ---
# This ensures the incoming JSON has the correct structure.
class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

# --- Load Data ---
# Load the telemetry data at startup using a robust relative path.
try:
    # The path is relative to this file's location (api/index.py)
    DATA_PATH = Path(__file__).parent.parent / "data" / "telemetry.json"
    df = pd.read_json(DATA_PATH)
except FileNotFoundError:
    # Handle case where file might not be found
    df = pd.DataFrame()

# --- Define API Endpoint ---
@app.post("/process-telemetry")
def process_telemetry(request: TelemetryRequest):
    """
    Accepts a list of regions and a latency threshold, then returns
    per-region metrics.
    """
    if df.empty:
        return {"error": "Telemetry data not found on server."}

    results = {}
    for region in request.regions:
        # Filter data for the current region
        region_df = df[df['region'] == region]

        if region_df.empty:
            results[region] = {"error": "No data for this region"}
            continue

        # Calculate metrics
        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_percent'].mean()
        
        # Count records where latency is above the given threshold
        breaches = int((region_df['latency_ms'] > request.threshold_ms).sum())

        # Store results for the region
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches,
        }
        
    return results
