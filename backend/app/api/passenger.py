import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from backend.app.core.database import get_db
from backend.app.core.rbac import get_current_user
from backend.app.models.tables import (
    User, Stop, Route, RouteStop, Trip, Booking, Ticket, Payment, Refund, ConfigRule, Bus
)
from backend.app.services.fare_service import calculate_fare
from backend.app.services.payment_mock import payment_gateway
from backend.app.services.qr_service import generate_qr_ticket_payload

router = APIRouter(prefix="/passenger", tags=["Passenger Core"])

class FareEstimateRequest(BaseModel):
    route_id: str
    from_stop_id: str
    to_stop_id: str
    bus_type: Optional[str] = "Ordinary"

class CreateBookingRequest(BaseModel):
    trip_id: str
    from_stop_id: str
    to_stop_id: str
    passenger_name: str
    seat_number: Optional[int] = None
    passenger_age: Optional[int] = 28
    passenger_gender: Optional[str] = "M"
    payment_method: str = "upi"

class CancelBookingRequest(BaseModel):
    reason: Optional[str] = "Passenger schedule change"

@router.get("/stops")
async def list_stops(search: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Stop).where(Stop.is_deleted == False)
    if search:
        query = query.where(or_(Stop.name.ilike(f"%{search}%"), Stop.name_ta.ilike(f"%{search}%")))
    res = await db.execute(query.order_by(Stop.name))
    stops = res.scalars().all()
    return [{"id": s.id, "name": s.name, "name_ta": s.name_ta, "latitude": s.latitude, "longitude": s.longitude, "is_major": s.is_major} for s in stops]

@router.get("/routes/search")
async def search_routes_and_trips(
    from_stop_id: str = Query(...),
    to_stop_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Searches valid routes connecting from_stop_id and to_stop_id,
    with downstream stage check, calculated fares, and available trips.
    """
    # Find routes containing both stops in correct order
    rs1_q = select(RouteStop).where(RouteStop.stop_id == from_stop_id)
    rs1_res = await db.execute(rs1_q)
    from_stops = {rs.route_id: rs for rs in rs1_res.scalars().all()}

    rs2_q = select(RouteStop).where(RouteStop.stop_id == to_stop_id)
    rs2_res = await db.execute(rs2_q)
    to_stops = {rs.route_id: rs for rs in rs2_res.scalars().all()}

    matching_route_ids = []
    for r_id, rs_from in from_stops.items():
        if r_id in to_stops:
            rs_to = to_stops[r_id]
            if rs_to.stop_sequence > rs_from.stop_sequence: # Downstream direction
                matching_route_ids.append((r_id, rs_from, rs_to))

    results = []
    for r_id, rs_from, rs_to in matching_route_ids:
        r_q = select(Route).where(Route.id == r_id, Route.is_active == True)
        r_res = await db.execute(r_q)
        route_obj = r_res.scalars().first()
        if not route_obj:
            continue

        # Get total stages on route
        cnt_q = select(RouteStop).where(RouteStop.route_id == r_id)
        cnt_res = await db.execute(cnt_q)
        all_stops = cnt_res.scalars().all()
        total_stages = len(all_stops)

        # Base fare calculation
        base_f, tax_f, total_fare = calculate_fare(
            from_stop_seq=rs_from.stop_sequence,
            to_stop_seq=rs_to.stop_sequence,
            total_stages=total_stages,
            base_route_fare=route_obj.base_fare,
            bus_type="Ordinary"
        )

        # Available trips for this route today
        trips_q = select(Trip, Bus).join(Bus, Trip.bus_id == Bus.id).where(
            Trip.route_id == r_id,
            Trip.status.in_(["scheduled", "in_transit"]),
            Trip.is_deleted == False
        ).limit(5)
        trips_res = await db.execute(trips_q)
        trips_data = []
        for trip_obj, bus_obj in trips_res.all():
            # Calculate booked seats
            bk_q = select(Ticket).join(Booking, Ticket.booking_id == Booking.id).where(
                Booking.trip_id == trip_obj.id,
                Ticket.status.in_(["valid", "boarded"])
            )
            bk_res = await db.execute(bk_q)
            booked_count = len(bk_res.scalars().all())

            trips_data.append({
                "trip_id": trip_obj.id,
                "bus_registration": bus_obj.registration_number,
                "bus_type": bus_obj.bus_type,
                "total_seats": bus_obj.total_seats,
                "available_seats": max(0, bus_obj.total_seats - booked_count),
                "departure_time": trip_obj.start_time.strftime("%H:%M"),
                "status": trip_obj.status
            })

        results.append({
            "route_id": route_obj.id,
            "route_number": route_obj.route_number,
            "route_name": route_obj.name,
            "from_stage": rs_from.stage_number,
            "to_stage": rs_to.stage_number,
            "distance_km": round(rs_to.distance_from_origin_km - rs_from.distance_from_origin_km, 1),
            "estimated_mins": max(15, rs_to.travel_time_mins - rs_from.travel_time_mins),
            "fare_inr": total_fare,
            "trips": trips_data
        })

    return results

@router.get("/trips/{trip_id}/seat-map")
async def get_trip_seat_map(trip_id: str, db: AsyncSession = Depends(get_db)):
    t_q = select(Trip, Bus).join(Bus, Trip.bus_id == Bus.id).where(Trip.id == trip_id)
    t_res = await db.execute(t_q)
    row = t_res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip_obj, bus_obj = row

    # Fetch already booked seat numbers
    b_q = select(Ticket.seat_number).join(Booking, Ticket.booking_id == Booking.id).where(
        Booking.trip_id == trip_id,
        Ticket.status.in_(["valid", "boarded"])
    )
    b_res = await db.execute(b_q)
    occupied_seats = set(b_res.scalars().all())

    seats = []
    for s_num in range(1, bus_obj.total_seats + 1):
        seats.append({
            "seat_number": s_num,
            "is_available": s_num not in occupied_seats,
            "seat_type": "window" if s_num % 4 in [1, 0] else "aisle"
        })

    return {
        "trip_id": trip_id,
        "bus_registration": bus_obj.registration_number,
        "bus_type": bus_obj.bus_type,
        "total_seats": bus_obj.total_seats,
        "occupied_count": len(occupied_seats),
        "available_count": bus_obj.total_seats - len(occupied_seats),
        "seats": seats
    }

@router.post("/fare/estimate")
async def estimate_fare(req: FareEstimateRequest, db: AsyncSession = Depends(get_db)):
    r_q = select(Route).where(Route.id == req.route_id)
    r_res = await db.execute(r_q)
    route_obj = r_res.scalars().first()
    if not route_obj:
        raise HTTPException(status_code=404, detail="Route not found")

    rs1_q = select(RouteStop).where(RouteStop.route_id == req.route_id, RouteStop.stop_id == req.from_stop_id)
    rs1_res = await db.execute(rs1_q)
    rs1 = rs1_res.scalars().first()

    rs2_q = select(RouteStop).where(RouteStop.route_id == req.route_id, RouteStop.stop_id == req.to_stop_id)
    rs2_res = await db.execute(rs2_q)
    rs2 = rs2_res.scalars().first()

    if not rs1 or not rs2:
        raise HTTPException(status_code=400, detail="Invalid stop selection for route")

    cnt_q = select(RouteStop).where(RouteStop.route_id == req.route_id)
    cnt_res = await db.execute(cnt_q)
    total_stages = len(cnt_res.scalars().all())

    base_f, tax_f, total_fare = calculate_fare(
        from_stop_seq=rs1.stop_sequence,
        to_stop_seq=rs2.stop_sequence,
        total_stages=total_stages,
        base_route_fare=route_obj.base_fare,
        bus_type=req.bus_type or "Ordinary"
    )

    return {
        "route_id": req.route_id,
        "base_amount": base_f,
        "tax_amount": tax_f,
        "total_fare": total_fare,
        "distance_km": round(abs(rs2.distance_from_origin_km - rs1.distance_from_origin_km), 1)
    }

@router.post("/bookings")
async def create_booking(
    req: CreateBookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check trip
    t_q = select(Trip, Route, Bus).join(Route, Trip.route_id == Route.id).join(Bus, Trip.bus_id == Bus.id).where(Trip.id == req.trip_id)
    t_res = await db.execute(t_q)
    trip_row = t_res.first()
    if not trip_row:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip_obj, route_obj, bus_obj = trip_row

    # Calculate fare
    rs1_q = select(RouteStop).where(RouteStop.route_id == route_obj.id, RouteStop.stop_id == req.from_stop_id)
    rs2_q = select(RouteStop).where(RouteStop.route_id == route_obj.id, RouteStop.stop_id == req.to_stop_id)
    rs1 = (await db.execute(rs1_q)).scalars().first()
    rs2 = (await db.execute(rs2_q)).scalars().first()

    if not rs1 or not rs2:
        raise HTTPException(status_code=400, detail="Stops not found on this route")

    cnt_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_obj.id))
    total_stages = len(cnt_res.scalars().all())

    _, _, total_fare = calculate_fare(
        from_stop_seq=rs1.stop_sequence,
        to_stop_seq=rs2.stop_sequence,
        total_stages=total_stages,
        base_route_fare=route_obj.base_fare,
        bus_type=bus_obj.bus_type
    )

    # Seat allocation: pick specified or lowest available
    b_q = select(Ticket.seat_number).join(Booking, Ticket.booking_id == Booking.id).where(
        Booking.trip_id == req.trip_id,
        Ticket.status.in_(["valid", "boarded"])
    )
    occupied_seats = set((await db.execute(b_q)).scalars().all())

    allocated_seat = req.seat_number
    if allocated_seat:
        if allocated_seat in occupied_seats:
            raise HTTPException(status_code=400, detail=f"Seat {allocated_seat} is already occupied.")
    else:
        for s in range(1, bus_obj.total_seats + 1):
            if s not in occupied_seats:
                allocated_seat = s
                break
        if not allocated_seat:
            raise HTTPException(status_code=400, detail="Bus is completely booked. No seats remaining.")

    booking_ref = f"TNK-{uuid.uuid4().hex[:8].upper()}"

    # Create Booking
    booking = Booking(
        user_id=current_user.id,
        trip_id=req.trip_id,
        from_stop_id=req.from_stop_id,
        to_stop_id=req.to_stop_id,
        booking_reference=booking_ref,
        total_fare=total_fare,
        status="confirmed",
        booking_channel="app",
        payment_status="paid"
    )
    db.add(booking)
    await db.flush()

    # Process Mock Payment
    charge = payment_gateway.process_charge(total_fare, req.payment_method, current_user.id)
    payment = Payment(
        booking_id=booking.id,
        transaction_ref=charge["transaction_ref"],
        payment_method=req.payment_method,
        amount=total_fare,
        status="success",
        gateway_response=charge
    )
    db.add(payment)
    await db.flush()

    # Generate Signed Offline Tamper-Proof HMAC QR Ticket
    ticket_id = str(uuid.uuid4())
    qr_payload, qr_sig = generate_qr_ticket_payload(
        ticket_id=ticket_id,
        booking_ref=booking_ref,
        trip_id=req.trip_id,
        passenger_name=req.passenger_name or current_user.full_name,
        seat_number=allocated_seat,
        fare=total_fare
    )

    ticket = Ticket(
        id=ticket_id,
        booking_id=booking.id,
        seat_number=allocated_seat,
        passenger_name=req.passenger_name or current_user.full_name,
        passenger_age=req.passenger_age,
        passenger_gender=req.passenger_gender,
        qr_code_data=qr_payload,
        qr_signature=qr_sig,
        status="valid"
    )
    db.add(ticket)
    await db.commit()

    return {
        "booking_id": booking.id,
        "booking_reference": booking_ref,
        "ticket_id": ticket.id,
        "seat_number": allocated_seat,
        "total_fare": total_fare,
        "qr_code_data": qr_payload,
        "qr_signature": qr_sig,
        "status": "confirmed",
        "route_name": route_obj.name,
        "bus_registration": bus_obj.registration_number
    }

@router.get("/bookings/history")
async def get_booking_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Booking, Trip, Route, Stop, Ticket).join(
        Trip, Booking.trip_id == Trip.id
    ).join(
        Route, Trip.route_id == Route.id
    ).join(
        Stop, Booking.from_stop_id == Stop.id
    ).join(
        Ticket, Booking.id == Ticket.booking_id
    ).where(
        Booking.user_id == current_user.id
    ).order_by(Booking.created_at.desc())

    res = await db.execute(query)
    rows = res.all()

    items = []
    for b_obj, tr_obj, r_obj, st_obj, t_obj in rows:
        items.append({
            "booking_id": b_obj.id,
            "booking_reference": b_obj.booking_reference,
            "ticket_id": t_obj.id,
            "seat_number": t_obj.seat_number,
            "total_fare": b_obj.total_fare,
            "status": b_obj.status,
            "payment_status": b_obj.payment_status,
            "route_name": r_obj.name,
            "from_stop": st_obj.name,
            "qr_code_data": t_obj.qr_code_data,
            "booking_date": b_obj.created_at.isoformat()
        })
    return items

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    req: CancelBookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    b_q = select(Booking, Payment, Trip).join(Payment, Booking.id == Payment.booking_id).join(Trip, Booking.trip_id == Trip.id).where(
        Booking.id == booking_id,
        Booking.user_id == current_user.id
    )
    res = await db.execute(b_q)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found or not owned by user.")
    booking, payment, trip = row

    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled.")

    # Read configurable refund rules table
    rule_q = select(ConfigRule).where(ConfigRule.key == "refund_policy")
    rule_res = await db.execute(rule_q)
    rule_obj = rule_res.scalars().first()
    policy = rule_obj.value if rule_obj else {
        "cancellation_window_hours_full": 24,
        "partial_refund_percentage": 75,
        "late_cancellation_percentage": 50,
        "no_refund_within_hours": 1
    }

    # Calculate time to trip departure
    hours_left = max(0.0, (trip.start_time - datetime.utcnow()).total_seconds() / 3600.0)

    refund_pct = 0
    if hours_left >= policy.get("cancellation_window_hours_full", 24):
        refund_pct = 100
    elif hours_left >= 6:
        refund_pct = policy.get("partial_refund_percentage", 75)
    elif hours_left >= policy.get("no_refund_within_hours", 1):
        refund_pct = policy.get("late_cancellation_percentage", 50)
    else:
        refund_pct = 0 # No refund within 1 hour

    refund_amount = round((booking.total_fare * refund_pct) / 100.0, 2)
    penalty_amount = round(booking.total_fare - refund_amount, 2)

    # Process mock refund
    payment_gateway.process_refund(payment.transaction_ref, refund_amount)

    refund = Refund(
        booking_id=booking.id,
        payment_id=payment.id,
        refund_amount=refund_amount,
        penalty_amount=penalty_amount,
        reason=req.reason,
        status="processed"
    )
    db.add(refund)

    # Update booking and ticket status
    booking.status = "cancelled"
    booking.payment_status = "refunded" if refund_amount > 0 else "retained"

    # Cancel associated tickets
    tickets_res = await db.execute(select(Ticket).where(Ticket.booking_id == booking.id))
    for t in tickets_res.scalars().all():
        t.status = "cancelled"

    await db.commit()

    return {
        "booking_id": booking.id,
        "status": "cancelled",
        "original_fare": booking.total_fare,
        "refund_percentage": refund_pct,
        "refund_amount": refund_amount,
        "penalty_amount": penalty_amount,
        "hours_before_departure": round(hours_left, 1),
        "message": f"Booking successfully cancelled. Refund of ₹{refund_amount} processed according to transit policy."
    }
