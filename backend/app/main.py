from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
import io

from app.anomaly import detect_anomalies
from app.utils import get_usd_to_eur_rate, get_risk_label

app = FastAPI(title="Cloud Cost Anomaly Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CostRecord(BaseModel):
    date: str
    service: str
    cost_usd: float


def build_response(df: pd.DataFrame):
    required_columns = {"date", "service", "cost_usd"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail="Input must contain date, service, and cost_usd fields."
        )

    anomalies = detect_anomalies(df)
    usd_to_eur_rate = get_usd_to_eur_rate()

    for item in anomalies:
        item["actual_cost_eur"] = round(item["actual_cost_usd"] * usd_to_eur_rate, 2)
        item["expected_cost_eur"] = round(item["expected_cost_usd"] * usd_to_eur_rate, 2)
        item["risk_label"] = get_risk_label(item["severity"])

    total_flagged_cost_usd = round(
        sum(item["actual_cost_usd"] for item in anomalies), 2
    ) if anomalies else 0.0

    total_flagged_cost_eur = round(
        sum(item["actual_cost_eur"] for item in anomalies), 2
    ) if anomalies else 0.0

    highest_spike = round(
        max(item["spike_percentage"] for item in anomalies), 2
    ) if anomalies else 0.0

    average_spike = round(
        sum(item["spike_percentage"] for item in anomalies) / len(anomalies), 2
    ) if anomalies else 0.0

    severity_counts = {
        "high": sum(1 for item in anomalies if item["severity"] == "High"),
        "medium": sum(1 for item in anomalies if item["severity"] == "Medium"),
        "low": sum(1 for item in anomalies if item["severity"] == "Low"),
    }

    return {
        "summary": {
            "total_records": int(len(df)),
            "total_anomalies": int(len(anomalies)),
            "total_flagged_cost_usd": total_flagged_cost_usd,
            "total_flagged_cost_eur": total_flagged_cost_eur,
            "highest_spike_percentage": highest_spike,
            "average_anomaly_spike_percentage": average_spike,
            "usd_to_eur_rate": round(usd_to_eur_rate, 4),
            "severity_breakdown": severity_counts
        },
        "anomalies": anomalies
    }


@app.get("/")
def root():
    return {"message": "Cloud Cost Anomaly Detection Backend is running"}


@app.post("/analyse-cost")
async def analyse_cost(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported here.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        return build_response(df)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyse-cost-json")
async def analyse_cost_json(records: List[CostRecord]):
    try:
        df = pd.DataFrame([record.model_dump() for record in records])
        return build_response(df)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))