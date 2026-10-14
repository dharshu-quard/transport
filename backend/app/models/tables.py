import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin

# 1. User
class User(Base, BaseModelMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="passenger", nullable=False, index=True) # passenger, driver, conductor, employee, family_member, depot_manager, admin
    depot_id = Column(String(36), ForeignKey("depots.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    preferred_language = Column(String(10), default="ta", nullable=False) # ta, en

    depot = relationship("Depot", back_populates="users", foreign_keys=[depot_id])
    bookings = relationship("Booking", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

# 2. Role
class Role(Base, BaseModelMixin):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, default=list)

# 3. Corporation
class Corporation(Base, BaseModelMixin):
    __tablename__ = "corporations"

    name = Column(String(255), nullable=False) # e.g. TNSTC Madurai, MTC Chennai
    code = Column(String(50), unique=True, nullable=False) # e.g. TNSTC-MDU, MTC-CHN
    state = Column(String(100), default="Tamil Nadu", nullable=False)
    headquarters = Column(String(100), nullable=False)

    depots = relationship("Depot", back_populates="corporation")
    routes = relationship("Route", back_populates="corporation")

# 4. Depot
class Depot(Base, BaseModelMixin):
    __tablename__ = "depots"

    corporation_id = Column(String(36), ForeignKey("corporations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, default=50)
    contact_phone = Column(String(20), nullable=True)

    corporation = relationship("Corporation", back_populates="depots")
    users = relationship("User", back_populates="depot", foreign_keys=[User.depot_id])
    buses = relationship("Bus", back_populates="depot")
    duties = relationship("Duty", back_populates="depot")

# 5. Bus
class Bus(Base, BaseModelMixin):
    __tablename__ = "buses"

    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False, index=True)
    registration_number = Column(String(50), unique=True, nullable=False, index=True) # e.g. TN-01-N-9901
    bus_type = Column(String(50), default="Ordinary", nullable=False) # Ordinary, Express, Deluxe, AC-Sleeper
    total_seats = Column(Integer, default=40, nullable=False)
    status = Column(String(50), default="active", nullable=False) # active, maintenance, breakdown, standby
    fuel_type = Column(String(50), default="Diesel") # Diesel, Electric, CNG
    mileage_km = Column(Float, default=150000.0)
    last_serviced_at = Column(DateTime, nullable=True)

    depot = relationship("Depot", back_populates="buses")
    duties = relationship("Duty", back_populates="bus")
    trips = relationship("Trip", back_populates="bus")
    gps_pings = relationship("GpsPing", back_populates="bus")

# 6. Route
class Route(Base, BaseModelMixin):
    __tablename__ = "routes"

    corporation_id = Column(String(36), ForeignKey("corporations.id"), nullable=False, index=True)
    route_number = Column(String(50), nullable=False, index=True) # e.g. 101, 23C, 45B
    name = Column(String(255), nullable=False) # e.g. Chennai CMBT - Madurai Mattuthavani
    origin_depot_id = Column(String(36), ForeignKey("depots.id"), nullable=True)
    destination_depot_id = Column(String(36), ForeignKey("depots.id"), nullable=True)
    total_distance_km = Column(Float, default=0.0)
    estimated_duration_mins = Column(Integer, default=0)
    base_fare = Column(Float, default=20.0)
    is_active = Column(Boolean, default=True)

    corporation = relationship("Corporation", back_populates="routes")
    route_stops = relationship("RouteStop", back_populates="route", order_by="RouteStop.stop_sequence")
    schedules = relationship("Schedule", back_populates="route")

# 7. Stop
class Stop(Base, BaseModelMixin):
    __tablename__ = "stops"

    name = Column(String(255), nullable=False, index=True)
    name_ta = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_code = Column(String(50), default="TN-ZONE-1")
    is_major = Column(Boolean, default=False)

    route_stops = relationship("RouteStop", back_populates="stop")

# 8. RouteStop
class RouteStop(Base, BaseModelMixin):
    __tablename__ = "route_stops"

    route_id = Column(String(36), ForeignKey("routes.id"), nullable=False, index=True)
    stop_id = Column(String(36), ForeignKey("stops.id"), nullable=False, index=True)
    stop_sequence = Column(Integer, nullable=False)
    stage_number = Column(Integer, default=1)
    distance_from_origin_km = Column(Float, default=0.0)
    travel_time_mins = Column(Integer, default=0)
    fare_from_origin = Column(Float, default=0.0)

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")

# 9. Fare
class Fare(Base, BaseModelMixin):
    __tablename__ = "fares"

    route_id = Column(String(36), ForeignKey("routes.id"), nullable=False, index=True)
    from_stop_id = Column(String(36), ForeignKey("stops.id"), nullable=False)
    to_stop_id = Column(String(36), ForeignKey("stops.id"), nullable=False)
    bus_type = Column(String(50), default="Ordinary")
    base_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

# 10. Schedule
class Schedule(Base, BaseModelMixin):
    __tablename__ = "schedules"

    route_id = Column(String(36), ForeignKey("routes.id"), nullable=False, index=True)
    departure_time = Column(String(10), nullable=False) # e.g. "06:00"
    arrival_time = Column(String(10), nullable=False)   # e.g. "12:30"
    frequency_mins = Column(Integer, default=60)
    days_of_week = Column(JSON, default=lambda: [1,2,3,4,5,6,7])
    is_active = Column(Boolean, default=True)

    route = relationship("Route", back_populates="schedules")
    duties = relationship("Duty", back_populates="schedule")

# 11. Duty
class Duty(Base, BaseModelMixin):
    __tablename__ = "duties"

    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False, index=True)
    schedule_id = Column(String(36), ForeignKey("schedules.id"), nullable=True)
    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False)
    driver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    conductor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    duty_date = Column(String(20), nullable=False, index=True) # YYYY-MM-DD
    status = Column(String(50), default="scheduled") # scheduled, active, completed, cancelled
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)

    depot = relationship("Depot", back_populates="duties")
    schedule = relationship("Schedule", back_populates="duties")
    bus = relationship("Bus", back_populates="duties")
    driver = relationship("User", foreign_keys=[driver_id])
    conductor = relationship("User", foreign_keys=[conductor_id])
    trips = relationship("Trip", back_populates="duty")

# 12. Trip
class Trip(Base, BaseModelMixin):
    __tablename__ = "trips"

    duty_id = Column(String(36), ForeignKey("duties.id"), nullable=True, index=True)
    route_id = Column(String(36), ForeignKey("routes.id"), nullable=False, index=True)
    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="scheduled", index=True) # scheduled, in_transit, completed, delayed, cancelled
    current_stage = Column(Integer, default=1)
    delay_minutes = Column(Integer, default=0)

    duty = relationship("Duty", back_populates="trips")
    route = relationship("Route")
    bus = relationship("Bus", back_populates="trips")
    bookings = relationship("Booking", back_populates="trip")

# 13. Booking
class Booking(Base, BaseModelMixin):
    __tablename__ = "bookings"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    from_stop_id = Column(String(36), ForeignKey("stops.id"), nullable=False)
    to_stop_id = Column(String(36), ForeignKey("stops.id"), nullable=False)
    booking_reference = Column(String(50), unique=True, nullable=False, index=True)
    total_fare = Column(Float, nullable=False)
    status = Column(String(50), default="confirmed", index=True) # confirmed, cancelled, completed
    booking_channel = Column(String(50), default="app") # app, web, autopilot, conductor
    payment_status = Column(String(50), default="paid") # paid, refunded, failed

    user = relationship("User", back_populates="bookings")
    trip = relationship("Trip", back_populates="bookings")
    from_stop = relationship("Stop", foreign_keys=[from_stop_id])
    to_stop = relationship("Stop", foreign_keys=[to_stop_id])
    tickets = relationship("Ticket", back_populates="booking")
    payment = relationship("Payment", back_populates="booking", uselist=False)

# 14. Ticket
class Ticket(Base, BaseModelMixin):
    __tablename__ = "tickets"

    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False, index=True)
    seat_number = Column(Integer, nullable=False)
    passenger_name = Column(String(255), nullable=False)
    passenger_age = Column(Integer, nullable=True)
    passenger_gender = Column(String(10), nullable=True)
    qr_code_data = Column(Text, nullable=False)
    qr_signature = Column(String(255), nullable=False)
    status = Column(String(50), default="valid", index=True) # valid, boarded, expired, cancelled
    boarded_at = Column(DateTime, nullable=True)
    validated_by_conductor_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    booking = relationship("Booking", back_populates="tickets")
    validated_by = relationship("User", foreign_keys=[validated_by_conductor_id])

# 15. Payment
class Payment(Base, BaseModelMixin):
    __tablename__ = "payments"

    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False, unique=True)
    transaction_ref = Column(String(100), unique=True, nullable=False, index=True)
    payment_method = Column(String(50), default="upi") # upi, card, netbanking, cash
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="success") # success, pending, failed
    gateway_response = Column(JSON, default=dict)

    booking = relationship("Booking", back_populates="payment")
    refund = relationship("Refund", back_populates="payment", uselist=False)

# 16. Refund
class Refund(Base, BaseModelMixin):
    __tablename__ = "refunds"

    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    refund_amount = Column(Float, nullable=False)
    penalty_amount = Column(Float, default=0.0)
    reason = Column(String(255), nullable=True)
    status = Column(String(50), default="processed") # processed, pending, rejected
    processed_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="refund")

# 17. GpsPing
class GpsPing(Base, BaseModelMixin):
    __tablename__ = "gps_pings"

    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=45.0)
    heading = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    is_deviated = Column(Boolean, default=False)

    bus = relationship("Bus", back_populates="gps_pings")

# 18. Attendance
class Attendance(Base, BaseModelMixin):
    __tablename__ = "attendance"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    status = Column(String(50), default="present") # present, absent, late, on_leave
    date = Column(String(20), nullable=False, index=True) # YYYY-MM-DD

    user = relationship("User")
    depot = relationship("Depot")

# 19. LeaveRequest
class LeaveRequest(Base, BaseModelMixin):
    __tablename__ = "leave_requests"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False)
    leave_type = Column(String(50), default="casual") # casual, medical, earned
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="pending") # pending, approved, rejected
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

# 20. DutyChangeRequest
class DutyChangeRequest(Base, BaseModelMixin):
    __tablename__ = "duty_change_requests"

    requester_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    target_duty_id = Column(String(36), ForeignKey("duties.id"), nullable=False)
    substitute_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="pending") # pending, approved, rejected
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    requester = relationship("User", foreign_keys=[requester_id])
    substitute = relationship("User", foreign_keys=[substitute_user_id])
    target_duty = relationship("Duty", foreign_keys=[target_duty_id])

# 21. Inspection
class Inspection(Base, BaseModelMixin):
    __tablename__ = "inspections"

    duty_id = Column(String(36), ForeignKey("duties.id"), nullable=True)
    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    inspector_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    brakes_ok = Column(Boolean, default=True)
    tires_ok = Column(Boolean, default=True)
    wipers_ok = Column(Boolean, default=True)
    lights_ok = Column(Boolean, default=True)
    emergency_exit_ok = Column(Boolean, default=True)
    remarks = Column(Text, nullable=True)
    passed = Column(Boolean, default=True)

    bus = relationship("Bus")
    inspector = relationship("User")

# 22. Breakdown
class Breakdown(Base, BaseModelMixin):
    __tablename__ = "breakdowns"

    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True)
    reported_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    issue_type = Column(String(100), nullable=False) # Engine Overheating, Tire Puncture, Brake Failure, Electrical
    severity = Column(String(50), default="high") # low, medium, high, critical
    description = Column(Text, nullable=False)
    status = Column(String(50), default="reported") # reported, dispatched, repaired, resolved
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    bus = relationship("Bus")
    reporter = relationship("User")

# 23. Complaint
class Complaint(Base, BaseModelMixin):
    __tablename__ = "complaints"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True)
    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=True)
    category = Column(String(100), default="General") # AI predicted category
    user_category = Column(String(100), default="General")
    description = Column(Text, nullable=False)
    photo_url = Column(String(500), nullable=True)
    status = Column(String(50), default="open", index=True) # open, investigating, resolved, closed
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=True)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolution = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    depot = relationship("Depot")

# 24. LostFound
class LostFound(Base, BaseModelMixin):
    __tablename__ = "lost_found"

    report_type = Column(String(20), nullable=False, index=True) # lost, found
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=True)
    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=True)
    item_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="Personal Belongings") # Electronics, Bag, Documents, Wallet, etc.
    contact_info = Column(String(255), nullable=True)
    status = Column(String(50), default="reported") # reported, matched, claimed, closed
    matched_id = Column(String(36), ForeignKey("lost_found.id"), nullable=True)

    user = relationship("User")

# 25. Employee
class Employee(Base, BaseModelMixin):
    __tablename__ = "employees"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False)
    employee_code = Column(String(50), unique=True, nullable=False, index=True) # e.g. TNSTC-EMP-1001
    designation = Column(String(100), nullable=False)
    date_of_joining = Column(String(20), nullable=False)
    licence_number = Column(String(100), nullable=True)
    licence_expiry_date = Column(String(20), nullable=True)
    max_family_passes = Column(Integer, default=4)
    is_active = Column(Boolean, default=True)

    user = relationship("User")
    depot = relationship("Depot")
    family_members = relationship("FamilyMember", back_populates="employee")
    pass_applications = relationship("PassApplication", back_populates="employee")

# 26. FamilyMember
class FamilyMember(Base, BaseModelMixin):
    __tablename__ = "family_members"

    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    relation_type = Column(String(50), nullable=False) # spouse, child, parent
    date_of_birth = Column(String(20), nullable=False)
    id_proof_type = Column(String(50), default="Aadhaar")
    id_proof_number = Column(String(100), nullable=False)
    is_eligible = Column(Boolean, default=True)

    employee = relationship("Employee", back_populates="family_members")

# 27. PassApplication
class PassApplication(Base, BaseModelMixin):
    __tablename__ = "pass_applications"

    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    family_member_id = Column(String(36), ForeignKey("family_members.id"), nullable=True)
    pass_type = Column(String(50), default="employee") # employee, family
    academic_year_or_period = Column(String(50), default="2026-2027")
    status = Column(String(50), default="submitted", index=True) # submitted, depot_approved, depot_rejected, admin_approved, admin_rejected
    depot_reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    depot_reviewed_at = Column(DateTime, nullable=True)
    admin_reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    admin_reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="pass_applications")
    family_member = relationship("FamilyMember")
    pass_record = relationship("Pass", back_populates="application", uselist=False)

# 28. Pass
class Pass(Base, BaseModelMixin):
    __tablename__ = "passes"

    application_id = Column(String(36), ForeignKey("pass_applications.id"), nullable=False, unique=True)
    pass_number = Column(String(50), unique=True, nullable=False, index=True)
    holder_name = Column(String(255), nullable=False)
    holder_type = Column(String(50), nullable=False) # employee, spouse, child, parent
    valid_from = Column(String(20), nullable=False)
    valid_until = Column(String(20), nullable=False)
    qr_code_data = Column(Text, nullable=False)
    qr_signature = Column(String(255), nullable=False)
    status = Column(String(50), default="active", index=True) # active, expired, suspended, revoked

    application = relationship("PassApplication", back_populates="pass_record")

# 29. Document
class Document(Base, BaseModelMixin):
    __tablename__ = "documents"

    entity_type = Column(String(50), nullable=False, index=True) # employee, pass_application, complaint
    entity_id = Column(String(36), nullable=False, index=True)
    document_type = Column(String(50), nullable=False) # aadhaar, ration_card, employee_id, medical
    file_path = Column(String(500), nullable=False)
    encrypted_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=True)

# 30. Notification
class Notification(Base, BaseModelMixin):
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    title_ta = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    body_ta = Column(Text, nullable=False)
    channel = Column(String(50), default="in_app") # fcm, in_app, sms
    notification_type = Column(String(50), default="general") # booking, alert, autopilot, pass, duty
    is_read = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)

    user = relationship("User", back_populates="notifications")

# 31. MaintenanceRecord
class MaintenanceRecord(Base, BaseModelMixin):
    __tablename__ = "maintenance_records"

    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False)
    service_type = Column(String(100), nullable=False) # routine, preventive, overhaul, breakdown_fix
    cost = Column(Float, default=0.0)
    odometer_reading_km = Column(Float, default=0.0)
    description = Column(Text, nullable=False)
    technician_name = Column(String(255), nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    bus = relationship("Bus")
    depot = relationship("Depot")

# 32. FuelRecord
class FuelRecord(Base, BaseModelMixin):
    __tablename__ = "fuel_records"

    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=False)
    liters = Column(Float, nullable=False)
    cost_per_liter = Column(Float, default=95.0)
    total_cost = Column(Float, nullable=False)
    odometer_km = Column(Float, nullable=False)
    fuel_station = Column(String(255), default="Depot Pump")
    fuel_date = Column(String(20), nullable=False)

    bus = relationship("Bus")
    depot = relationship("Depot")

# 33. Incident
class Incident(Base, BaseModelMixin):
    __tablename__ = "incidents"

    bus_id = Column(String(36), ForeignKey("buses.id"), nullable=False, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True)
    driver_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    incident_type = Column(String(50), nullable=False) # drowsiness_alert, route_deviation, speed_violation, sos
    severity = Column(String(50), default="high") # low, medium, high, critical
    metadata_json = Column(JSON, default=dict)
    resolved = Column(Boolean, default=False)

    bus = relationship("Bus")
    trip = relationship("Trip")
    driver = relationship("User")

# 34. AuditLog
class AuditLog(Base, BaseModelMixin):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    role = Column(String(50), nullable=True)
    depot_id = Column(String(36), ForeignKey("depots.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True) # e.g. CREATE_BUS, UPDATE_FARE, APPROVE_PASS
    entity_name = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(100), default="127.0.0.1")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
    depot = relationship("Depot")

# 35. AutopilotRule
class AutopilotRule(Base, BaseModelMixin):
    __tablename__ = "autopilot_rules"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    route_id = Column(String(36), ForeignKey("routes.id"), nullable=False)
    preferred_time_start = Column(String(10), nullable=False) # e.g. "07:30"
    preferred_time_end = Column(String(10), nullable=False)   # e.g. "09:00"
    days_of_week = Column(JSON, default=lambda: [1,2,3,4,5]) # Monday to Friday
    max_fare_limit = Column(Float, default=150.0)
    max_monthly_bookings = Column(Integer, default=22)
    current_month_bookings = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    consent_given = Column(Boolean, default=True)
    consent_timestamp = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)

    user = relationship("User")
    route = relationship("Route")

# 36. ConfigRule
class ConfigRule(Base, BaseModelMixin):
    __tablename__ = "config_rules"

    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
