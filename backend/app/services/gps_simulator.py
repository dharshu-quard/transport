import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket
from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.tables import Bus, Trip, Route, RouteStop, Stop, GpsPing, Incident
from ml.deviation_model import check_route_deviation

logger = logging.getLogger("gps_simulator")

# Active WebSocket passenger / admin connections
active_ws_connections: Set[WebSocket] = set()

async def register_websocket(ws: WebSocket):
    await ws.accept()
    active_ws_connections.add(ws)

def unregister_websocket(ws: WebSocket):
    active_ws_connections.discard(ws)

async def broadcast_tracking_update(payload: dict):
    if not active_ws_connections:
        return
    dead_connections = set()
    message = json.dumps(payload)
    for ws in active_ws_connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead_connections.add(ws)
    for dead in dead_connections:
        active_ws_connections.discard(dead)

# In-memory progress state for active simulated trips
trip_progress_state: Dict[str, dict] = {}

async def run_gps_simulation_tick():
    """
    Simulates a 5-second GPS ping tick for all active in-transit buses.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch active trips
            query = select(Trip).where(Trip.status == "in_transit")
            result = await db.execute(query)
            active_trips = result.scalars().all()

            if not active_trips:
                return

            pings_to_broadcast = []

            for trip in active_trips:
                bus_id = trip.bus_id
                route_id = trip.route_id

                # Fetch route stops
                rs_query = select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.stop_sequence)
                rs_res = await db.execute(rs_query)
                route_stops = rs_res.scalars().all()

                if not route_stops:
                    continue

                stop_ids = [rs.stop_id for rs in route_stops]
                st_query = select(Stop).where(Stop.id.in_(stop_ids))
                st_res = await db.execute(st_query)
                stops_by_id = {s.id: s for s in st_res.scalars().all()}

                waypoints = []
                for rs in route_stops:
                    st = stops_by_id.get(rs.stop_id)
                    if st:
                        waypoints.append((st.latitude, st.longitude, st.name))

                if len(waypoints) < 2:
                    continue

                # Initialize or advance progress
                state = trip_progress_state.get(trip.id, {"leg_idx": 0, "fraction": 0.0, "deviated": False})
                leg_idx = state["leg_idx"]
                fraction = state["fraction"]

                fraction += 0.05 # Advance 5% per 5-second tick
                if fraction >= 1.0:
                    fraction = 0.0
                    leg_idx = (leg_idx + 1) % (len(waypoints) - 1)

                state["leg_idx"] = leg_idx
                state["fraction"] = fraction
                trip_progress_state[trip.id] = state

                start_pt = waypoints[leg_idx]
                end_pt = waypoints[leg_idx + 1]

                cur_lat = start_pt[0] + fraction * (end_pt[0] - start_pt[0])
                cur_lon = start_pt[1] + fraction * (end_pt[1] - start_pt[1])

                # Check if bus is artificially deviated (for testing demo acceptance scenario 8)
                is_deviated = state.get("deviated", False)
                if is_deviated:
                    cur_lat += 0.08 # Shift ~9 km off corridor

                # Run ML route deviation check
                coords_only = [(w[0], w[1]) for w in waypoints]
                dev_res = check_route_deviation(cur_lat, cur_lon, coords_only)

                # Persist ping
                ping = GpsPing(
                    bus_id=bus_id,
                    trip_id=trip.id,
                    latitude=cur_lat,
                    longitude=cur_lon,
                    speed_kmh=round(random.uniform(42.0, 68.0), 1),
                    heading=180.0,
                    timestamp=datetime.utcnow(),
                    is_deviated=dev_res["is_deviated"]
                )
                db.add(ping)

                # If deviated and not already recorded, create incident
                if dev_res["is_deviated"]:
                    inc = Incident(
                        bus_id=bus_id,
                        trip_id=trip.id,
                        incident_type="route_deviation",
                        severity="high",
                        metadata_json={
                            "distance_from_corridor_km": dev_res["min_distance_to_corridor_km"],
                            "anomaly_score": dev_res["anomaly_score"]
                        }
                    )
                    db.add(inc)

                pings_to_broadcast.append({
                    "bus_id": bus_id,
                    "trip_id": trip.id,
                    "latitude": round(cur_lat, 5),
                    "longitude": round(cur_lon, 5),
                    "speed_kmh": ping.speed_kmh,
                    "heading": ping.heading,
                    "current_stage": leg_idx + 1,
                    "next_stop": end_pt[2],
                    "is_deviated": dev_res["is_deviated"],
                    "deviation_info": dev_res,
                    "timestamp": ping.timestamp.isoformat()
                })

            await db.commit()

            if pings_to_broadcast:
                await broadcast_tracking_update({
                    "type": "FLEET_GPS_UPDATE",
                    "pings": pings_to_broadcast,
                    "count": len(pings_to_broadcast)
                })

        except Exception as e:
            logger.error(f"Error in GPS simulation tick: {e}")
            await db.rollback()

def set_bus_deviation_sim(trip_id: str, deviated: bool = True):
    """Sets a simulated deviation flag for testing acceptance checks."""
    if trip_id in trip_progress_state:
        trip_progress_state[trip_id]["deviated"] = deviated
    else:
        trip_progress_state[trip_id] = {"leg_idx": 0, "fraction": 0.2, "deviated": deviated}
