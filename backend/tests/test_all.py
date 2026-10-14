import pytest
import uuid
import json
import time
from backend.app.services.fare_service import calculate_fare
from backend.app.services.qr_service import (
    generate_qr_ticket_payload, generate_qr_pass_payload, verify_qr_payload
)
from ml.deviation_model import check_route_deviation
from ml.pass_fraud_model import detect_pass_fraud_velocity
from ml.complaint_classifier import classify_complaint_text
from ml.maintenance_model import calculate_maintenance_risk
from ml.drowsiness_detector import DrowsinessDetector

def test_fare_calculation_stages():
    """Verify stage fare calculation with 5% tax and class multipliers."""
    # Ordinary bus, 3 stages out of 6
    base_f, tax_f, total_fare = calculate_fare(
        from_stop_seq=1, to_stop_seq=4, total_stages=6, base_route_fare=100.0, bus_type="Ordinary"
    )
    assert total_fare > 0
    assert tax_f == round(base_f * 0.05, 2)
    assert total_fare == round(base_f + tax_f, 2)

    # Deluxe bus should be more expensive than Ordinary for identical distance
    _, _, deluxe_fare = calculate_fare(
        from_stop_seq=1, to_stop_seq=4, total_stages=6, base_route_fare=100.0, bus_type="Deluxe"
    )
    assert deluxe_fare > total_fare

def test_tamper_proof_qr_ticket_verification():
    """Test HMAC cryptographic offline signature on tickets."""
    t_id = str(uuid.uuid4())
    qr_str, sig = generate_qr_ticket_payload(
        ticket_id=t_id,
        booking_ref="TNK-TEST-001",
        trip_id="TRIP-1",
        passenger_name="Dharshini Siva",
        seat_number=12,
        fare=145.0
    )

    # 1. Valid signature passes verification
    res = verify_qr_payload(qr_str)
    assert res["valid"] is True
    assert res["forged"] is False
    assert res["data"]["pax"] == "Dharshini Siva"
    assert res["data"]["seat"] == 12

    # 2. Tampered payload is rejected as forged
    tampered = json.loads(qr_str)
    tampered["data"]["fare"] = 1.0 # Malicious alteration
    tampered_str = json.dumps(tampered)

    tampered_res = verify_qr_payload(tampered_str)
    assert tampered_res["valid"] is False
    assert tampered_res["forged"] is True
    assert "signature mismatch" in tampered_res["error"].lower()

def test_tamper_proof_qr_pass_verification():
    """Test cryptographic offline signature on employee family passes."""
    p_id = str(uuid.uuid4())
    qr_str, sig = generate_qr_pass_payload(
        pass_id=p_id,
        pass_number="TN-PASS-8899",
        employee_code="TNSTC-EMP-1001",
        holder_name="Vasanthi S",
        holder_type="spouse",
        valid_until="2027-03-31"
    )

    res = verify_qr_payload(qr_str)
    assert res["valid"] is True
    assert res["data"]["pnum"] == "TN-PASS-8899"
    assert res["data"]["role"] == "spouse"

def test_route_corridor_deviation_detector():
    """Verify route corridor deviation detection and anomaly scores."""
    sample_corridor = [
        (13.0674, 80.2057), # Chennai CMBT
        (12.9249, 80.1000), # Tambaram
        (11.9401, 79.4861)  # Villupuram
    ]

    # Point right on the road (between Chennai & Tambaram)
    on_route = check_route_deviation(13.0, 80.15, sample_corridor, corridor_threshold_km=2.0)
    assert on_route["is_deviated"] is False

    # Point strayed 50 km off course towards Bay of Bengal / coast
    off_route = check_route_deviation(12.8, 80.6, sample_corridor, corridor_threshold_km=2.0)
    assert off_route["is_deviated"] is True
    assert off_route["severity"] in ["high", "critical"]
    assert off_route["anomaly_score"] > 0.5

def test_spatiotemporal_pass_fraud():
    """Verify detection of cloned passes scanned at impossible speeds."""
    from datetime import datetime, timedelta
    t0 = datetime(2026, 5, 1, 9, 0, 0)
    t1 = t0 + timedelta(minutes=20) # 20 mins later

    # Chennai and Madurai (450 km away in 20 mins = 1350 km/h)
    fraud = detect_pass_fraud_velocity(
        pass_id="PASS-99",
        current_lat=9.9252,
        current_lon=78.1198,
        current_time=t1,
        last_scan={"latitude": 13.0674, "longitude": 80.2057, "timestamp": t0}
    )
    assert fraud["fraud_detected"] is True
    assert fraud["implied_speed_kmh"] > 1000.0

def test_complaint_auto_classifier():
    """Verify NLP complaint classification into respective transit departments."""
    c1 = classify_complaint_text("The driver was speeding and drove through a red light near the junction.")
    assert c1["predicted_category"] == "Driver Behavior"

    c2 = classify_complaint_text("The floor was covered in dust and trash and the seats were stained.")
    assert c2["predicted_category"] == "Cleanliness"

    c3 = classify_complaint_text("Bus was delayed by over an hour without any update.")
    assert c3["predicted_category"] == "Punctuality"

def test_predictive_maintenance_scoring():
    """Verify fleet health score and recommended maintenance actions."""
    # Low risk bus
    low_risk = calculate_maintenance_risk(mileage_km=45000, days_since_service=10, past_breakdowns=0, failed_inspections=0)
    assert low_risk["risk_score"] < 40.0

    # High risk bus
    high_risk = calculate_maintenance_risk(mileage_km=380000, days_since_service=80, past_breakdowns=3, failed_inspections=2)
    assert high_risk["risk_score"] > 65.0
    assert len(high_risk["recommended_actions"]) > 0

def test_drowsiness_eye_aspect_ratio_detector():
    """Verify assistive drowsiness detector triggers alarm only after sustained closure."""
    detector = DrowsinessDetector(ear_threshold=0.22, sustained_secs=2.0)
    t = time.time()

    # Open eyes -> attentive
    r1 = detector.process_ear_sample(ear_value=0.32, timestamp=t)
    assert r1["is_eye_closed"] is False
    assert r1["trigger_alarm"] is False

    # Brief blink (0.2s) -> no alarm
    r2 = detector.process_ear_sample(ear_value=0.15, timestamp=t + 0.2)
    assert r2["trigger_alarm"] is False

    # Sustained closure (> 2.0s) -> alarm triggered!
    r3 = detector.process_ear_sample(ear_value=0.12, timestamp=t + 2.5)
    assert r3["trigger_alarm"] is True
    assert r3["status"] == "ALERT_DROWSY"
