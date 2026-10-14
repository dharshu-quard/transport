import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "HEALTHY"
        assert "TamilNadu Transit 360 AI" in data["system"]

@pytest.mark.anyio
async def test_otp_login_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Dev OTP 123456
        res = await ac.post("/api/auth/login-otp", json={"phone": "9876543210", "otp": "123456"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["phone"] == "9876543210"

@pytest.mark.anyio
async def test_passenger_search_and_booking_and_conductor_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login passenger
        login_res = await ac.post("/api/auth/login-otp", json={"phone": "9876543210", "otp": "123456"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get stops
        stops_res = await ac.get("/api/passenger/stops", headers=headers)
        assert stops_res.status_code == 200
        stops = stops_res.json()
        assert len(stops) >= 4
        from_stop = stops[0]["id"]
        to_stop = stops[-1]["id"]

        # 3. Search routes
        search_res = await ac.get(f"/api/passenger/routes/search?from_stop_id={from_stop}&to_stop_id={to_stop}", headers=headers)
        assert search_res.status_code == 200
        routes = search_res.json()

        # If direct route exists or check first route's trips
        if routes and routes[0]["trips"]:
            trip_id = routes[0]["trips"][0]["trip_id"]

            # 4. Book Ticket
            book_res = await ac.post("/api/passenger/bookings", json={
                "trip_id": trip_id,
                "from_stop_id": from_stop,
                "to_stop_id": to_stop,
                "passenger_name": "Dharshini Siva",
                "payment_method": "upi"
            }, headers=headers)

            assert book_res.status_code == 200
            booking_data = book_res.json()
            assert booking_data["status"] == "confirmed"
            qr_data = booking_data["qr_code_data"]
            assert len(qr_data) > 0

            # 5. Conductor scans QR (Valid)
            conductor_res = await ac.post("/api/auth/login-otp", json={"phone": "9700002001", "otp": "123456"})
            c_token = conductor_res.json()["access_token"]
            c_headers = {"Authorization": f"Bearer {c_token}"}

            val_res = await ac.post("/api/conductor/validate-qr", json={"qr_string": qr_data}, headers=c_headers)
            assert val_res.status_code == 200
            val_data = val_res.json()
            assert val_data["valid"] is True
            assert val_data["ticket"]["status"] == "boarded"

            # 6. Conductor scans duplicate (Rejection)
            dup_res = await ac.post("/api/conductor/validate-qr", json={"qr_string": qr_data}, headers=c_headers)
            assert dup_res.status_code == 200
            dup_data = dup_res.json()
            assert dup_data["valid"] is False
            assert dup_data["error_type"] == "DUPLICATE_SCAN"

            # 7. Conductor scans forged QR (Rejection)
            forged_qr = qr_data.replace('"fare":', '"fare":9999, "extra":')
            forged_res = await ac.post("/api/conductor/validate-qr", json={"qr_string": forged_qr}, headers=c_headers)
            assert forged_res.status_code == 200
            forged_data = forged_res.json()
            assert forged_data["valid"] is False
            assert forged_data["error_type"] == "FORGED_SIGNATURE"

@pytest.mark.anyio
async def test_ai_insights_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/ai/insights-overview")
        assert res.status_code == 200
        data = res.json()
        assert "demand_forecasts" in data
        assert "arrival_time_comparison" in data
        assert "predictive_maintenance_fleet" in data
        assert "ml_reports" in data
