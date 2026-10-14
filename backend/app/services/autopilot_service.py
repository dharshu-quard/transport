import uuid
import logging
from datetime import datetime
from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.tables import (
    AutopilotRule, Route, RouteStop, Trip, Booking, Ticket, Payment, User, AuditLog
)
from backend.app.services.fare_service import calculate_fare
from backend.app.services.payment_mock import payment_gateway
from backend.app.services.qr_service import generate_qr_ticket_payload
from backend.app.services.fcm_mock import notification_service

logger = logging.getLogger("autopilot_service")

async def execute_autopilot_cycle() -> dict:
    """
    Evaluates all active passenger Journey Autopilot rules and automatically
    reserves seats within defined limits, recording full audit trails.
    """
    results = {"processed": 0, "booked": 0, "skipped": 0, "logs": []}

    async with AsyncSessionLocal() as db:
        try:
            # Query active rules with consent
            query = select(AutopilotRule).where(
                AutopilotRule.is_active == True,
                AutopilotRule.consent_given == True,
                AutopilotRule.is_deleted == False
            )
            res = await db.execute(query)
            rules = res.scalars().all()

            for rule in rules:
                results["processed"] += 1
                rule_id = rule.id
                user_id = rule.user_id
                route_id = rule.route_id

                # Check monthly cap
                if rule.current_month_bookings >= rule.max_monthly_bookings:
                    msg = f"Skipping rule {rule_id}: Reached monthly limit of {rule.max_monthly_bookings} bookings."
                    results["skipped"] += 1
                    results["logs"].append(msg)
                    continue

                # Fetch user
                user_q = select(User).where(User.id == user_id)
                user_res = await db.execute(user_q)
                user = user_res.scalars().first()
                if not user:
                    continue

                # Fetch available trip for this route
                trip_q = select(Trip).where(
                    Trip.route_id == route_id,
                    Trip.status.in_(["scheduled", "in_transit"]),
                    Trip.is_deleted == False
                ).limit(1)
                trip_res = await db.execute(trip_q)
                trip = trip_res.scalars().first()

                if not trip:
                    msg = f"Rule {rule_id}: No scheduled trips found for route {route_id} today."
                    results["skipped"] += 1
                    results["logs"].append(msg)
                    continue

                # Fetch stops for route
                rs_q = select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.stop_sequence)
                rs_res = await db.execute(rs_q)
                route_stops = rs_res.scalars().all()

                if len(route_stops) < 2:
                    continue

                from_stop_id = route_stops[0].stop_id
                to_stop_id = route_stops[-1].stop_id

                # Calculate fare
                base_f, tax_f, total_fare = calculate_fare(
                    from_stop_seq=route_stops[0].stop_sequence,
                    to_stop_seq=route_stops[-1].stop_sequence,
                    total_stages=len(route_stops),
                    base_route_fare=120.0
                )

                # Check max fare threshold
                if total_fare > rule.max_fare_limit:
                    msg = f"Rule {rule_id}: Total fare (₹{total_fare}) exceeds max budget threshold (₹{rule.max_fare_limit})."
                    results["skipped"] += 1
                    results["logs"].append(msg)
                    continue

                # Step 1: Pre-booking notification reminder
                await notification_service.send_notification(
                    db=db,
                    user_id=user_id,
                    title_key="autopilot_booking_executed",
                    body_key="welcome",
                    notification_type="autopilot",
                    custom_title_en="Journey Autopilot: Booking Upcoming Commute",
                    custom_title_ta="தானியங்கி பயணம்: வரவிருக்கும் பயண முன்பதிவு தொடங்குகிறது",
                    custom_body_en=f"Reserving your regular seat for today's commute (Fare: ₹{total_fare}).",
                    custom_body_ta=f"இன்றைய வழக்கமான பயணத்திற்கான இருக்கை முன்பதிவு செய்யப்படுகிறது (கட்டணம்: ₹{total_fare})."
                )

                # Step 2: Book seat & generate ticket
                booking_ref = f"AUTO-{uuid.uuid4().hex[:8].upper()}"
                booking = Booking(
                    user_id=user_id,
                    trip_id=trip.id,
                    from_stop_id=from_stop_id,
                    to_stop_id=to_stop_id,
                    booking_reference=booking_ref,
                    total_fare=total_fare,
                    status="confirmed",
                    booking_channel="autopilot",
                    payment_status="paid"
                )
                db.add(booking)
                await db.flush()

                # Step 3: Mock payment processing
                charge = payment_gateway.process_charge(total_fare, "autopilot_autopay", user_id)
                pay = Payment(
                    booking_id=booking.id,
                    transaction_ref=charge["transaction_ref"],
                    payment_method="autopilot_autopay",
                    amount=total_fare,
                    status="success",
                    gateway_response=charge
                )
                db.add(pay)
                await db.flush()

                # Step 4: Cryptographically signed HMAC QR Ticket
                seat_num = (rule.current_month_bookings % 38) + 1
                qr_content, qr_sig = generate_qr_ticket_payload(
                    ticket_id=str(uuid.uuid4()),
                    booking_ref=booking_ref,
                    trip_id=trip.id,
                    passenger_name=user.full_name,
                    seat_number=seat_num,
                    fare=total_fare
                )
                ticket = Ticket(
                    booking_id=booking.id,
                    seat_number=seat_num,
                    passenger_name=user.full_name,
                    qr_code_data=qr_content,
                    qr_signature=qr_sig,
                    status="valid"
                )
                db.add(ticket)

                # Step 5: Update rule counters
                rule.current_month_bookings += 1
                rule.last_run_at = datetime.utcnow()

                # Step 6: Write immutable audit log
                audit = AuditLog(
                    user_id=user_id,
                    role="passenger",
                    action="AUTOPILOT_BOOKING_EXECUTED",
                    entity_name="Booking",
                    entity_id=booking.id,
                    new_values={
                        "booking_ref": booking_ref,
                        "fare": total_fare,
                        "seat": seat_num,
                        "rule_id": rule_id
                    }
                )
                db.add(audit)

                # Step 7: Post-booking notification
                await notification_service.send_notification(
                    db=db,
                    user_id=user_id,
                    title_key="autopilot_booking_executed",
                    body_key="booking_confirmed",
                    notification_type="autopilot",
                    custom_title_en="Journey Autopilot: Ticket Confirmed!",
                    custom_title_ta="தானியங்கி பயணம்: பயணச்சீட்டு உறுதியானது!",
                    custom_body_en=f"Ticket {booking_ref} issued for Seat {seat_num}. Have a safe journey!",
                    custom_body_ta=f"பயணச்சீட்டு {booking_ref} இருக்கை {seat_num}-க்கு உறுதியானது. இனிய பயணம்!"
                )

                results["booked"] += 1
                msg = f"Successfully auto-booked ticket {booking_ref} for {user.full_name} (Fare: ₹{total_fare})"
                results["logs"].append(msg)

            await db.commit()
            return results

        except Exception as e:
            logger.error(f"Error in autopilot execution cycle: {e}")
            await db.rollback()
            return {"error": str(e), "logs": results["logs"]}
