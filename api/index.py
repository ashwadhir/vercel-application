import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse # Import JSONResponse
from pydantic import BaseModel
from pathlib import Path

# Initialize the FastAPI app
app = FastAPI()

# We are adding headers manually now, so the middleware is not needed.
# You can remove or comment out the app.add_middleware block.

# --- Define Request Body Model ---
class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

# --- Load Data ---
try:
    DATA_PATH = Path(__file__).parent.parent / "data" / "telemetry.json"
    df = pd.read_json(DATA_PATH)
except FileNotFoundError:
    df = pd.DataFrame()

# --- Define API Endpoint ---
@app.post("/process-telemetry")
def process_telemetry(request: TelemetryRequest):
    if df.empty:
        return JSONResponse(
            status_code=404,
            content={"error": "Telemetry data not found on server."}
        )

    results = {}
    for region in request.regions:
        region_df = df[df['region'] == region]

        if region_df.empty:
            results[region] = {"error": "No data for this region"}
            continue

        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_pct'].mean()
        breaches = int((region_df['latency_ms'] > request.threshold_ms).sum())

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches,
        }
    
    # --- FIX: Manually create headers and attach them to the response ---
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    
    return JSONResponse(content=results, headers=headers)
