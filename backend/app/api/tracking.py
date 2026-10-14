from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.tables import Bus, Trip, Route, Stop, RouteStop, GpsPing, Booking, Ticket
from backend.app.services.gps_simulator import register_websocket, unregister_websocket, set_bus_deviation_sim
from ml.arrival_model import predict_arrival_time

router = APIRouter(prefix="/tracking", tags=["Live Tracking & Safety"])

class ValidateBoardedBusRequest(BaseModel):
    ticket_id: str
    boarded_bus_registration: str

class TestDeviationRequest(BaseModel):
    trip_id: str
    deviated: bool = True

@router.websocket("/ws")
async def websocket_tracking_endpoint(websocket: WebSocket):
    await register_websocket(websocket)
    try:
        while True:
            # Keep-alive ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        unregister_websocket(websocket)
    except Exception:
        unregister_websocket(websocket)

@router.get("/live-fleet")
async def get_live_fleet(db: AsyncSession = Depends(get_db)):
    """
    Returns latest GPS positions, speed, route, and status for all buses.
    """
    buses_q = select(Bus, Trip, Route).outerjoin(
        Trip, (Bus.id == Trip.bus_id) & (Trip.status == "in_transit")
    ).outerjoin(
        Route, Trip.route_id == Route.id
    ).where(Bus.is_deleted == False)

    res = await db.execute(buses_q)
    rows = res.all()

    fleet = []
    for bus_obj, trip_obj, route_obj in rows:
        # Get latest ping
        p_q = select(GpsPing).where(GpsPing.bus_id == bus_obj.id).order_by(desc(GpsPing.timestamp)).limit(1)
        p_res = await db.execute(p_q)
        latest_ping = p_res.scalars().first()

        lat = latest_ping.latitude if latest_ping else 13.0674
        lon = latest_ping.longitude if latest_ping else 80.2057

        fleet.append({
            "bus_id": bus_obj.id,
            "registration_number": bus_obj.registration_number,
            "bus_type": bus_obj.bus_type,
            "depot_id": bus_obj.depot_id,
            "status": bus_obj.status,
            "is_in_transit": trip_obj is not None,
            "current_trip_id": trip_obj.id if trip_obj else None,
            "route_name": route_obj.name if route_obj else "Depot Standby",
            "route_number": route_obj.route_number if route_obj else "-",
            "latitude": lat,
            "longitude": lon,
            "speed_kmh": latest_ping.speed_kmh if latest_ping else 0.0,
            "is_deviated": latest_ping.is_deviated if latest_ping else False,
            "last_ping_time": latest_ping.timestamp.isoformat() if latest_ping else None
        })
    return fleet

@router.get("/bus/{bus_id}/eta")
async def get_bus_eta_prediction(
    bus_id: str,
    target_stop_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Computes both distance/speed baseline ETA and ML arrival time prediction.
    """
    bus_res = await db.execute(select(Bus).where(Bus.id == bus_id))
    bus = bus_res.scalars().first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    target_stop_res = await db.execute(select(Stop).where(Stop.id == target_stop_id))
    target_stop = target_stop_res.scalars().first()
    if not target_stop:
        raise HTTPException(status_code=404, detail="Target stop not found")

    # Latest ping
    p_res = await db.execute(select(GpsPing).where(GpsPing.bus_id == bus_id).order_by(desc(GpsPing.timestamp)).limit(1))
    latest_ping = p_res.scalars().first()

    cur_lat = latest_ping.latitude if latest_ping else 13.0674
    cur_lon = latest_ping.longitude if latest_ping else 80.2057
    speed = latest_ping.speed_kmh if (latest_ping and latest_ping.speed_kmh > 10) else 45.0

    # Approximate distance
    from ml.deviation_model import haversine_distance_km
    dist_km = haversine_distance_km(cur_lat, cur_lon, target_stop.latitude, target_stop.longitude)

    # ML prediction vs baseline
    prediction = predict_arrival_time(
        distance_km=max(2.0, dist_km),
        speed_kmh=speed,
        hour_of_day=17,
        traffic_index=1.4
    )

    return {
        "bus_id": bus_id,
        "target_stop_name": target_stop.name,
        "target_stop_ta": target_stop.name_ta,
        "distance_remaining_km": round(dist_km, 1),
        "current_speed_kmh": round(speed, 1),
        **prediction
    }

@router.post("/validate-boarded-bus")
async def validate_boarded_bus(req: ValidateBoardedBusRequest, db: AsyncSession = Depends(get_db)):
    """
    Wrong-bus safety check: validates if boarded bus matches ticket's booked route.
    """
    t_q = select(Ticket, Booking, Trip, Route, Bus).join(
        Booking, Ticket.booking_id == Booking.id
    ).join(
        Trip, Booking.trip_id == Trip.id
    ).join(
        Route, Trip.route_id == Route.id
    ).join(
        Bus, Trip.bus_id == Bus.id
    ).where(Ticket.id == req.ticket_id)

    res = await db.execute(t_q)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket, booking, trip, route, assigned_bus = row
    boarded_reg = req.boarded_bus_registration.strip().upper()
    assigned_reg = assigned_bus.registration_number.strip().upper()

    is_correct_bus = (boarded_reg == assigned_reg)

    if not is_correct_bus:
        return {
            "is_correct_bus": False,
            "warning": True,
            "warning_title": "WRONG BUS DETECTED!",
            "warning_message_en": f"You boarded {boarded_reg}, but your booked ticket is for {assigned_reg} ({route.name}). Please disembark at the next stage!",
            "warning_message_ta": f"எச்சரிக்கை! நீங்கள் தவறான பேருந்தில் ({boarded_reg}) ஏறியுள்ளீர்கள். உங்கள் முன்பதிவு {assigned_reg}-ல் உள்ளது ({route.name})!",
            "assigned_bus": assigned_reg,
            "booked_route": route.name
        }

    return {
        "is_correct_bus": True,
        "warning": False,
        "message": f"Welcome aboard! Boarded valid bus {assigned_reg} for route {route.name}."
    }

@router.get("/missed-bus-alternatives")
async def get_missed_bus_alternatives(current_stop_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    Missed-bus alternative suggestions: finds upcoming scheduled trips from current stop.
    """
    rs_q = select(RouteStop, Route).join(Route, RouteStop.route_id == Route.id).where(RouteStop.stop_id == current_stop_id)
    rs_res = await db.execute(rs_q)
    rows = rs_res.all()

    alternatives = []
    for rs_obj, r_obj in rows[:6]:
        trips_q = select(Trip, Bus).join(Bus, Trip.bus_id == Bus.id).where(
            Trip.route_id == r_obj.id,
            Trip.status.in_(["scheduled", "in_transit"])
        ).limit(2)
        trips_res = await db.execute(trips_q)
        for tr_obj, b_obj in trips_res.all():
            alternatives.append({
                "route_number": r_obj.route_number,
                "route_name": r_obj.name,
                "departure_time": tr_obj.start_time.strftime("%H:%M"),
                "bus_type": b_obj.bus_type,
                "fare_base": r_obj.base_fare,
                "trip_id": tr_obj.id
            })

    return {
        "current_stop_id": current_stop_id,
        "suggestion_count": len(alternatives),
        "alternatives": alternatives
    }

@router.post("/test-deviation")
async def test_bus_deviation(req: TestDeviationRequest):
    """Admin/tester trigger to force a bus corridor deviation for acceptance testing."""
    set_bus_deviation_sim(req.trip_id, req.deviated)
    return {
        "status": "success",
        "trip_id": req.trip_id,
        "deviation_simulated": req.deviated,
        "message": "Trip deviation flag updated for next GPS tick."
    }
