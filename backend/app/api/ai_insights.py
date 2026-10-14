import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.core.database import get_db
from backend.app.core.rbac import get_current_user, require_role
from backend.app.models.tables import Bus, Route, Incident, Pass, Complaint
from ml.demand_model import predict_demand
from ml.arrival_model import predict_arrival_time
from ml.maintenance_model import calculate_maintenance_risk
from ml.allocation_model import generate_allocation_recommendations
from ml.pass_fraud_model import detect_pass_fraud_velocity
from ml.complaint_classifier import classify_complaint_text
from ml.drowsiness_detector import DrowsinessDetector

router = APIRouter(prefix="/ai", tags=["AI Insights & ML Services"])

class DrowsinessEventRequest(BaseModel):
    driver_id: Optional[str] = "driver-1"
    bus_id: str
    ear_value: float
    closure_duration_seconds: float
    trigger_alarm: bool = True

shared_drowsiness_detector = DrowsinessDetector(ear_threshold=0.22, sustained_secs=2.0)

@router.get("/insights-overview")
async def get_ai_insights_overview(
    db: AsyncSession = Depends(get_db)
):
    """
    Consolidated payload powering the admin dashboard 'AI Insights' screen.
    """
    # 1. Demand Predictions for top routes
    routes = (await db.execute(select(Route).limit(6))).scalars().all()
    demand_summary = []
    for idx, r in enumerate(routes):
        p_peak = predict_demand(route_index=idx, hour_of_day=8, day_of_week=2)
        p_off = predict_demand(route_index=idx, hour_of_day=14, day_of_week=2)
        demand_summary.append({
            "route_id": r.id,
            "route_number": r.route_number,
            "route_name": r.name,
            "predicted_peak_demand_pax": p_peak,
            "predicted_offpeak_demand_pax": p_off,
            "recommended_capacity": int(p_peak * 1.1)
        })

    # 2. Arrival Model Benchmark Sample
    arrival_sample = predict_arrival_time(distance_km=45.0, speed_kmh=42.0, hour_of_day=18, traffic_index=1.6)

    # 3. Fleet Maintenance Risk Matrix
    buses = (await db.execute(select(Bus).limit(10))).scalars().all()
    fleet_health = []
    for b in buses:
        risk = calculate_maintenance_risk(
            mileage_km=b.mileage_km,
            days_since_service=28,
            past_breakdowns=1 if b.status == "maintenance" else 0,
            failed_inspections=0
        )
        fleet_health.append({
            "bus_id": b.id,
            "registration": b.registration_number,
            "bus_type": b.bus_type,
            "mileage_km": b.mileage_km,
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "recommendations": risk["recommended_actions"]
        })

    # 4. Allocation Suggestions
    dummy_demands = [
        {"route_id": r["route_id"], "route_number": r["route_number"], "route_name": r["route_name"], "predicted_demand": r["predicted_peak_demand_pax"], "scheduled_seats": 40, "base_fare": 140.0}
        for r in demand_summary[:4]
    ]
    standby_buses = [
        {"id": b.id, "registration_number": b.registration_number, "bus_type": b.bus_type}
        for b in buses if b.status in ["active", "standby"]
    ][:3]
    allocation_recs = generate_allocation_recommendations(dummy_demands, standby_buses)

    # 5. Pass Fraud Detections (Recent velocity anomalies)
    fraud_sample = detect_pass_fraud_velocity(
        pass_id="TN-PASS-DEMO-CLONE",
        current_lat=9.9252, # Madurai
        current_lon=78.1198,
        current_time=datetime.utcnow(),
        last_scan={"latitude": 13.0674, "longitude": 80.2057, "timestamp": datetime.utcnow().isoformat()} # Chennai scanned at same time
    )

    # 6. Evaluation metrics reports from /ml/reports
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "reports")
    reports_meta = {}
    for r_file in os.listdir(reports_dir):
        if r_file.endswith(".json"):
            try:
                with open(os.path.join(reports_dir, r_file), "r", encoding="utf-8") as f:
                    reports_meta[r_file.replace(".json", "")] = json.load(f)
            except Exception:
                pass

    return {
        "demand_forecasts": demand_summary,
        "arrival_time_comparison": arrival_sample,
        "predictive_maintenance_fleet": fleet_health,
        "allocation_recommendations": allocation_recs,
        "velocity_fraud_detection_sample": fraud_sample,
        "ml_reports": reports_meta
    }

@router.post("/process-drowsiness-frame")
async def process_drowsiness_eye_aspect_ratio(
    ear_value: float = Query(...),
    driver_id: Optional[str] = "demo-driver",
    bus_id: Optional[str] = "TN-01-N-1001",
    db: AsyncSession = Depends(get_db)
):
    """
    Processes real-time eye aspect ratio measurement from webcam demo page.
    Triggers safety alarm after sustained eye closure.
    Zero raw video stored (Privacy Guaranteed).
    """
    res = shared_drowsiness_detector.process_ear_sample(
        ear_value=ear_value,
        driver_id=driver_id,
        bus_id=bus_id
    )

    if res["trigger_alarm"]:
        # Record safety incident in database
        bus_obj = (await db.execute(select(Bus).where(Bus.registration_number == bus_id))).scalars().first()
        bus_pk = bus_obj.id if bus_obj else "bus-1"

        inc = Incident(
            bus_id=bus_pk,
            incident_type="drowsiness_alert",
            severity="high",
            metadata_json={
                "ear_value": ear_value,
                "closure_duration": res["closure_duration_seconds"],
                "status": "ASSISTIVE_ALARM_ACTIVATED"
            }
        )
        db.add(inc)
        await db.commit()

    return res

@router.post("/drowsiness-event")
async def log_drowsiness_event(
    req: DrowsinessEventRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Logs assistive drowsiness alert event from driver device.
    """
    bus_obj = (await db.execute(select(Bus).where(Bus.registration_number == req.bus_id))).scalars().first()
    bus_pk = bus_obj.id if bus_obj else "bus-1"

    inc = Incident(
        bus_id=bus_pk,
        driver_id=req.driver_id,
        incident_type="drowsiness_alert",
        severity="high",
        metadata_json={
            "ear_value": req.ear_value,
            "duration": req.closure_duration_seconds,
            "trigger_alarm": req.trigger_alarm
        }
    )
    db.add(inc)
    await db.commit()
    return {"status": "recorded", "incident_id": inc.id}
