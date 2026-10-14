import os
import sys
import random
import uuid
from datetime import datetime, timedelta

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))

from backend.app.core.database import SyncSessionLocal, sync_engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.tables import (
    User, Role, Corporation, Depot, Bus, Route, Stop, RouteStop, Fare,
    Schedule, Duty, Trip, Booking, Ticket, Payment, Refund, GpsPing,
    Attendance, LeaveRequest, DutyChangeRequest, Inspection, Breakdown,
    Complaint, LostFound, Employee, FamilyMember, PassApplication, Pass,
    Document, Notification, MaintenanceRecord, FuelRecord, Incident,
    AuditLog, AutopilotRule, ConfigRule
)

def run_seed():
    print("=" * 60)
    print("SEEDING TAMILNADU TRANSIT 360 AI - PRODUCTION-GRADE SYNTHETIC DATA")
    print("=" * 60)

    db = SyncSessionLocal()
    # Ensure tables exist
    Base.metadata.create_all(bind=sync_engine)

    # Check if already seeded
    existing_users = db.query(User).count()
    if existing_users >= 500:
        print(f"Database already contains {existing_users} users. Skipping redundant seeding.")
        db.close()
        return

    random.seed(42) # Deterministic seed

    # 1. Config Rules (Eligibility, Refund Policies, Autopilot limits)
    print("-> Seeding Config Rules...")
    config_items = [
        ConfigRule(
            key="refund_policy",
            value={
                "cancellation_window_hours_full": 24, # 100% refund if cancelled > 24h before
                "cancellation_window_hours_partial": 6, # 75% refund if cancelled 6h - 24h
                "partial_refund_percentage": 75,
                "late_cancellation_percentage": 50, # 50% refund if < 6h
                "no_refund_within_hours": 1 # 0% within 1 hour
            },
            description="Tiered ticket cancellation and refund calculation rules"
        ),
        ConfigRule(
            key="pass_eligibility",
            value={
                "min_employee_service_months": 3,
                "max_dependents_allowed": 4,
                "eligible_relationships": ["spouse", "child", "parent"],
                "child_max_age": 25,
                "requires_bonafide_cert_for_student": True,
                "annual_admin_fee": 0
            },
            description="Rules governing employee and family member transit pass approvals"
        ),
        ConfigRule(
            key="autopilot_safety_limits",
            value={
                "max_monthly_spend_inr": 4000.0,
                "max_bookings_per_user_per_month": 25,
                "advance_booking_hours": 12,
                "require_active_payment_method": True
            },
            description="System-wide safeguards and budget caps for Journey Autopilot"
        ),
        ConfigRule(
            key="fare_rules",
            value={
                "Ordinary_rate_per_km": 0.85,
                "Express_rate_per_km": 1.25,
                "Deluxe_rate_per_km": 1.60,
                "AC_Sleeper_rate_per_km": 2.20,
                "min_fare": 10.0
            },
            description="Base rates per kilometer according to bus class"
        )
    ]
    db.add_all(config_items)
    db.commit()

    # 2. Roles
    print("-> Seeding RBAC Roles...")
    roles = [
        Role(name="passenger", description="Public commuter with search, booking, live tracking, autopilot access"),
        Role(name="driver", description="TNSTC Driver with duty roster, vehicle inspection, SOS, breakdowns"),
        Role(name="conductor", description="TNSTC Conductor with offline QR scanning, ticketing, daily cash reconciliation"),
        Role(name="employee", description="TNSTC Employee with employee pass applications, family management"),
        Role(name="family_member", description="Dependent family member with transit pass perks"),
        Role(name="depot_manager", description="Depot Supervisor with depot-scoped roster, leave approvals, vehicle status"),
        Role(name="admin", description="State Transport Head with statewide visibility, rule config, audits, ML insights")
    ]
    db.add_all(roles)
    db.commit()

    # 3. Corporations (2 required: TNSTC-Madurai and MTC-Chennai)
    print("-> Seeding Corporations...")
    corp1 = Corporation(name="TNSTC Madurai", code="TNSTC-MDU", state="Tamil Nadu", headquarters="Madurai")
    corp2 = Corporation(name="MTC Chennai", code="MTC-CHN", state="Tamil Nadu", headquarters="Chennai")
    db.add_all([corp1, corp2])
    db.commit()

    # 4. Depots (4 required: Chennai, Coimbatore, Madurai, Trichy)
    print("-> Seeding 4 Depots...")
    depot_chn = Depot(corporation_id=corp2.id, name="Chennai Central Depot (CMBT)", code="CHN-CMBT", latitude=13.0674, longitude=80.2057, capacity=120, contact_phone="044-24795555")
    depot_cbe = Depot(corporation_id=corp1.id, name="Coimbatore Singanallur Depot", code="CBE-SNG", latitude=11.0028, longitude=76.9975, capacity=80, contact_phone="0422-2578899")
    depot_mdu = Depot(corporation_id=corp1.id, name="Madurai Mattuthavani Depot", code="MDU-MAT", latitude=9.9252, longitude=78.1198, capacity=100, contact_phone="0452-2566777")
    depot_try = Depot(corporation_id=corp1.id, name="Trichy Central Bus Depot", code="TRY-CEN", latitude=10.7905, longitude=78.7047, capacity=90, contact_phone="0431-2412233")
    depots = [depot_chn, depot_cbe, depot_mdu, depot_try]
    db.add_all(depots)
    db.commit()

    # 5. Core Users (Admin, Depot Managers, Drivers, Conductors, Passengers)
    print("-> Seeding Staff and Base Users...")
    hashed_pwd = get_password_hash("password123")
    demo_users = []

    # State Admin
    admin_user = User(
        phone="9840000001", email="admin@tnstc.gov.in", hashed_password=hashed_pwd,
        full_name="Selva Kumar (State Director)", role="admin", depot_id=depot_chn.id, preferred_language="ta"
    )
    demo_users.append(admin_user)

    # 4 Depot Managers
    mgr_names = ["Karthik Raman (Chennai)", "Venkatesh S (Coimbatore)", "Meenakshi Sundaram (Madurai)", "Anbazhagan P (Trichy)"]
    mgr_users = []
    for i, dep in enumerate(depots):
        mgr = User(
            phone=f"984000001{i+1}", email=f"manager.{dep.code.lower()}@tnstc.gov.in", hashed_password=hashed_pwd,
            full_name=mgr_names[i], role="depot_manager", depot_id=dep.id, preferred_language="ta"
        )
        demo_users.append(mgr)
        mgr_users.append(mgr)

    # Staff (Drivers & Conductors & Maintenance: Total ~100 staff)
    first_names = ["Murugan", "Senthil", "Palanisamy", "Muthu", "Ganesan", "Velu", "Karuppasamy", "Arumugam", "Thangavel", "Ramar",
                   "Saravanan", "Kannan", "Manikandan", "Ramesh", "Suresh", "Vijay", "Ajith", "Dhanush", "Sivakumar", "Rajesh",
                   "Naveen", "Prakash", "Dinesh", "Santhosh", "Vignesh", "Mohan", "Pandian", "Elango", "Sekar", "Balamurugan"]
    driver_users = []
    conductor_users = []
    employee_records = []

    for i in range(1, 51): # 50 Drivers
        dep = depots[(i - 1) % len(depots)]
        fname = f"{random.choice(first_names)} D"
        u = User(
            phone=f"9700001{i:03d}", email=f"driver.{i}@tnstc.gov.in", hashed_password=hashed_pwd,
            full_name=f"{fname} (Driver #{i})", role="driver", depot_id=dep.id, preferred_language="ta"
        )
        demo_users.append(u)
        driver_users.append(u)

    for i in range(1, 46): # 45 Conductors
        dep = depots[(i - 1) % len(depots)]
        fname = f"{random.choice(first_names)} C"
        u = User(
            phone=f"9700002{i:03d}", email=f"conductor.{i}@tnstc.gov.in", hashed_password=hashed_pwd,
            full_name=f"{fname} (Conductor #{i})", role="conductor", depot_id=dep.id, preferred_language="ta"
        )
        demo_users.append(u)
        conductor_users.append(u)

    # 5 Depot Clerks / Employee representatives
    for i in range(1, 6):
        dep = depots[(i - 1) % len(depots)]
        u = User(
            phone=f"9700003{i:03d}", email=f"emp.{i}@tnstc.gov.in", hashed_password=hashed_pwd,
            full_name=f"{random.choice(first_names)} K (Clerk #{i})", role="employee", depot_id=dep.id, preferred_language="ta"
        )
        demo_users.append(u)

    db.add_all(demo_users)
    db.commit()

    # Link Employees table for drivers & conductors
    print("-> Creating Employee Service Profiles & Family Members...")
    all_staff = driver_users + conductor_users
    for idx, staff_u in enumerate(all_staff):
        emp = Employee(
            user_id=staff_u.id,
            depot_id=staff_u.depot_id,
            employee_code=f"TNSTC-EMP-{1000 + idx}",
            designation="Senior Driver" if staff_u.role == "driver" else "Senior Conductor",
            date_of_joining="2018-04-15",
            licence_number=f"TN-58-{2010000000 + idx}" if staff_u.role == "driver" else None,
            licence_expiry_date="2028-12-31",
            max_family_passes=4,
            is_active=True
        )
        db.add(emp)
        employee_records.append(emp)
    db.commit()

    # Seed Family Members for first 15 employees
    family_members_list = []
    rel_types = ["spouse", "child", "parent"]
    for emp in employee_records[:15]:
        spouse = FamilyMember(
            employee_id=emp.id,
            full_name=f"Vasanthi {emp.employee_code[-4:]}",
            relation_type="spouse",
            date_of_birth="1988-06-12",
            id_proof_type="Aadhaar",
            id_proof_number=f"8899{random.randint(10000000, 99999999)}",
            is_eligible=True
        )
        child = FamilyMember(
            employee_id=emp.id,
            full_name=f"Kavya {emp.employee_code[-4:]}",
            relation_type="child",
            date_of_birth="2010-09-24",
            id_proof_type="Aadhaar",
            id_proof_number=f"6677{random.randint(10000000, 99999999)}",
            is_eligible=True
        )
        db.add_all([spouse, child])
        family_members_list.extend([spouse, child])
    db.commit()

    # 6. Seed 500 Commuter / Passenger Accounts
    print("-> Seeding 500 Passenger Commuter Profiles...")
    passenger_users = []
    passenger_first = ["Kavitha", "Priya", "Lakshmi", "Revathi", "Divya", "Anitha", "Deepa", "Bhuvaneshwari", "Nandhini", "Abirami",
                       "Ravi", "Sundar", "Gopinath", "Mani", "Pradeep", "Raghav", "Sridhar", "Kalyan", "Aravind", "Aakash"]
    passenger_last = ["Natarajan", "Sundaram", "Subramanian", "Iyer", "Chettiar", "Gounder", "Naicker", "Pillai", "Nadarr", "Sethi"]

    # Known test passenger for demo
    demo_passenger = User(
        phone="9876543210", email="commuter.dharshini@gmail.com", hashed_password=hashed_pwd,
        full_name="Dharshini Sivakumar (Regular Commuter)", role="passenger", depot_id=depot_chn.id, preferred_language="ta"
    )
    passenger_users.append(demo_passenger)

    for i in range(2, 501):
        p_name = f"{random.choice(passenger_first)} {random.choice(passenger_last)}"
        p_user = User(
            phone=f"9841{i:06d}",
            email=f"commuter{i}@example.com",
            hashed_password=hashed_pwd,
            full_name=p_name,
            role="passenger",
            preferred_language=random.choice(["ta", "en"])
        )
        passenger_users.append(p_user)
        if len(passenger_users) % 100 == 0:
            db.add_all(passenger_users[-100:])
            db.commit()
    db.add_all(passenger_users[-len(passenger_users)%100:])
    db.commit()

    # 7. Seed 60 Buses (across 4 depots)
    print("-> Seeding 60 Buses with realistic TN registrations...")
    bus_records = []
    depot_prefixes = {
        "CHN-CMBT": ("TN-01-N", depot_chn),
        "CBE-SNG": ("TN-38-N", depot_cbe),
        "MDU-MAT": ("TN-58-N", depot_mdu),
        "TRY-CEN": ("TN-45-N", depot_try)
    }
    bus_types = ["Ordinary", "Express", "Deluxe", "AC-Sleeper"]

    bus_count = 0
    for code, (prefix, dep) in depot_prefixes.items():
        # 15 buses per depot = 60 total
        for num in range(1001, 1016):
            b_type = bus_types[bus_count % len(bus_types)]
            seats = 50 if b_type == "Ordinary" else (40 if b_type in ["Express", "Deluxe"] else 32)
            status = "active"
            if num == 1014:
                status = "maintenance"
            elif num == 1015:
                status = "standby"

            b = Bus(
                depot_id=dep.id,
                registration_number=f"{prefix}-{num}",
                bus_type=b_type,
                total_seats=seats,
                status=status,
                fuel_type="Diesel" if num % 5 != 0 else "Electric",
                mileage_km=round(random.uniform(50000, 350000), 1),
                last_serviced_at=datetime.utcnow() - timedelta(days=random.randint(2, 45))
            )
            bus_records.append(b)
            bus_count += 1
    db.add_all(bus_records)
    db.commit()

    # 8. Stops (24 Key Tamil Nadu Stops)
    print("-> Seeding Realistic Tamil Nadu Stops...")
    raw_stops = [
        ("Chennai CMBT (Koyambedu)", "சென்னை கோயம்பேடு", 13.0674, 80.2057, True),
        ("Guindy Asiad Bus Terminal", "கிண்டி", 13.0067, 80.2026, False),
        ("Tambaram Sanatorium", "தாம்பரம்", 12.9249, 80.1000, True),
        ("Chengalpattu Toll", "செங்கல்பட்டு", 12.6841, 79.9836, False),
        ("Tindivanam Junction", "திண்டிவனம்", 12.2285, 79.6514, False),
        ("Villupuram New Bus Stand", "விழுப்புரம்", 11.9401, 79.4861, True),
        ("Ulundurpet Bypass", "உளுந்தூர்பேட்டை", 11.6917, 79.2900, False),
        ("Perambalur Four Roads", "பெரம்பலூர்", 11.2333, 78.8833, False),
        ("Trichy Central Bus Stand", "திருச்சி மத்திய பேருந்து நிலையம்", 10.7905, 78.7047, True),
        ("Dindigul Bus Stand", "திண்டுக்கல்", 10.3673, 77.9803, True),
        ("Madurai Mattuthavani", "மதுரை மாட்டுத்தாவணி", 9.9252, 78.1198, True),
        ("Madurai Periyar Bus Stand", "மதுரை பெரியார்", 9.9178, 78.1158, False),
        ("Virudhunagar Old Bus Stand", "விருதுநகர்", 9.5680, 77.9624, False),
        ("Tirunelveli New Bus Stand", "திருநெல்வேலி", 8.7139, 77.7567, True),
        ("Salem New Bus Stand", "சேலம் புதிய பேருந்து நிலையம்", 11.6643, 78.1460, True),
        ("Erode Central Bus Stand", "ஈரோடு மத்திய பேருந்து நிலையம்", 11.3410, 77.7172, True),
        ("Tiruppur Old Bus Stand", "திருப்பூர்", 11.1085, 77.3411, False),
        ("Coimbatore Singanallur", "கோவை சிங்காநல்லூர்", 11.0028, 76.9975, True),
        ("Coimbatore Gandhipuram", "கோவை காந்திபுரம்", 11.0168, 76.9680, True),
        ("Thanjavur Old Bus Stand", "தஞ்சாவூர்", 10.7870, 79.1378, True),
        ("Kumbakonam Central", "கும்பகோணம்", 10.9602, 79.3845, True),
        ("Kanchipuram Bus Stand", "காஞ்சிபுரம்", 12.8342, 79.7036, False),
        ("Vellore New Bus Stand", "வேலூர்", 12.9165, 79.1325, True),
        ("Hosur Bus Terminus", "ஓசூர்", 12.7409, 77.8253, True)
    ]
    stop_map = {}
    for name_en, name_ta, lat, lon, is_major in raw_stops:
        s = Stop(name=name_en, name_ta=name_ta, latitude=lat, longitude=lon, is_major=is_major)
        db.add(s)
        stop_map[name_en] = s
    db.commit()

    # 9. Routes & Route Stops (20 realistic routes)
    print("-> Seeding 20 Tamil Nadu Inter-city and Express Routes...")
    route_definitions = [
        ("101E", "Chennai CMBT - Madurai Mattuthavani Superfast", corp1.id, depot_chn.id, depot_mdu.id,
         ["Chennai CMBT (Koyambedu)", "Tambaram Sanatorium", "Villupuram New Bus Stand", "Trichy Central Bus Stand", "Dindigul Bus Stand", "Madurai Mattuthavani"],
         460.0, 480, 380.0),

        ("102D", "Madurai Mattuthavani - Chennai CMBT Return Express", corp1.id, depot_mdu.id, depot_chn.id,
         ["Madurai Mattuthavani", "Dindigul Bus Stand", "Trichy Central Bus Stand", "Villupuram New Bus Stand", "Tambaram Sanatorium", "Chennai CMBT (Koyambedu)"],
         460.0, 480, 380.0),

        ("201E", "Chennai CMBT - Coimbatore Singanallur Night Express", corp2.id, depot_chn.id, depot_cbe.id,
         ["Chennai CMBT (Koyambedu)", "Kanchipuram Bus Stand", "Vellore New Bus Stand", "Salem New Bus Stand", "Erode Central Bus Stand", "Tiruppur Old Bus Stand", "Coimbatore Singanallur"],
         510.0, 540, 420.0),

        ("202D", "Coimbatore Singanallur - Chennai CMBT Day Express", corp2.id, depot_cbe.id, depot_chn.id,
         ["Coimbatore Singanallur", "Tiruppur Old Bus Stand", "Erode Central Bus Stand", "Salem New Bus Stand", "Vellore New Bus Stand", "Chennai CMBT (Koyambedu)"],
         510.0, 540, 420.0),

        ("301S", "Coimbatore Gandhipuram - Madurai Mattuthavani Express", corp1.id, depot_cbe.id, depot_mdu.id,
         ["Coimbatore Gandhipuram", "Coimbatore Singanallur", "Tiruppur Old Bus Stand", "Dindigul Bus Stand", "Madurai Mattuthavani"],
         215.0, 260, 195.0),

        ("302S", "Madurai Mattuthavani - Coimbatore Gandhipuram Express", corp1.id, depot_mdu.id, depot_cbe.id,
         ["Madurai Mattuthavani", "Dindigul Bus Stand", "Tiruppur Old Bus Stand", "Coimbatore Singanallur", "Coimbatore Gandhipuram"],
         215.0, 260, 195.0),

        ("401T", "Trichy Central - Madurai Mattuthavani Corridor", corp1.id, depot_try.id, depot_mdu.id,
         ["Trichy Central Bus Stand", "Dindigul Bus Stand", "Madurai Mattuthavani"],
         135.0, 150, 120.0),

        ("402T", "Madurai Mattuthavani - Trichy Central Corridor", corp1.id, depot_mdu.id, depot_try.id,
         ["Madurai Mattuthavani", "Dindigul Bus Stand", "Trichy Central Bus Stand"],
         135.0, 150, 120.0),

        ("501C", "Chennai CMBT - Trichy Central Direct", corp2.id, depot_chn.id, depot_try.id,
         ["Chennai CMBT (Koyambedu)", "Tambaram Sanatorium", "Tindivanam Junction", "Villupuram New Bus Stand", "Ulundurpet Bypass", "Perambalur Four Roads", "Trichy Central Bus Stand"],
         330.0, 360, 280.0),

        ("502C", "Trichy Central - Chennai CMBT Direct", corp2.id, depot_try.id, depot_chn.id,
         ["Trichy Central Bus Stand", "Perambalur Four Roads", "Ulundurpet Bypass", "Villupuram New Bus Stand", "Tindivanam Junction", "Tambaram Sanatorium", "Chennai CMBT (Koyambedu)"],
         330.0, 360, 280.0),

        ("601M", "Madurai Mattuthavani - Tirunelveli New Bus Stand", corp1.id, depot_mdu.id, depot_mdu.id,
         ["Madurai Mattuthavani", "Madurai Periyar Bus Stand", "Virudhunagar Old Bus Stand", "Tirunelveli New Bus Stand"],
         160.0, 180, 145.0),

        ("602M", "Tirunelveli New Bus Stand - Madurai Mattuthavani", corp1.id, depot_mdu.id, depot_mdu.id,
         ["Tirunelveli New Bus Stand", "Virudhunagar Old Bus Stand", "Madurai Periyar Bus Stand", "Madurai Mattuthavani"],
         160.0, 180, 145.0),

        ("701S", "Salem New Bus Stand - Coimbatore Gandhipuram", corp1.id, depot_cbe.id, depot_cbe.id,
         ["Salem New Bus Stand", "Erode Central Bus Stand", "Tiruppur Old Bus Stand", "Coimbatore Gandhipuram"],
         165.0, 180, 140.0),

        ("702S", "Coimbatore Gandhipuram - Salem New Bus Stand", corp1.id, depot_cbe.id, depot_cbe.id,
         ["Coimbatore Gandhipuram", "Tiruppur Old Bus Stand", "Erode Central Bus Stand", "Salem New Bus Stand"],
         165.0, 180, 140.0),

        ("801T", "Trichy Central - Thanjavur - Kumbakonam Link", corp1.id, depot_try.id, depot_try.id,
         ["Trichy Central Bus Stand", "Thanjavur Old Bus Stand", "Kumbakonam Central"],
         95.0, 110, 85.0),

        ("802T", "Kumbakonam Central - Thanjavur - Trichy Central Link", corp1.id, depot_try.id, depot_try.id,
         ["Kumbakonam Central", "Thanjavur Old Bus Stand", "Trichy Central Bus Stand"],
         95.0, 110, 85.0),

        ("901V", "Chennai CMBT - Vellore - Hosur Express", corp2.id, depot_chn.id, depot_chn.id,
         ["Chennai CMBT (Koyambedu)", "Kanchipuram Bus Stand", "Vellore New Bus Stand", "Hosur Bus Terminus"],
         310.0, 340, 270.0),

        ("902V", "Hosur Bus Terminus - Vellore - Chennai CMBT Express", corp2.id, depot_chn.id, depot_chn.id,
         ["Hosur Bus Terminus", "Vellore New Bus Stand", "Kanchipuram Bus Stand", "Chennai CMBT (Koyambedu)"],
         310.0, 340, 270.0),

        ("110C", "Chennai CMBT - Tambaram Metro Feeder", corp2.id, depot_chn.id, depot_chn.id,
         ["Chennai CMBT (Koyambedu)", "Guindy Asiad Bus Terminal", "Tambaram Sanatorium"],
         28.0, 45, 25.0),

        ("111C", "Tambaram - Chennai CMBT Metro Feeder", corp2.id, depot_chn.id, depot_chn.id,
         ["Tambaram Sanatorium", "Guindy Asiad Bus Terminal", "Chennai CMBT (Koyambedu)"],
         28.0, 45, 25.0)
    ]

    route_records = []
    for r_num, r_name, corp_id, orig_id, dest_id, stops_seq, dist, dur, base_f in route_definitions:
        r = Route(
            corporation_id=corp_id,
            route_number=r_num,
            name=r_name,
            origin_depot_id=orig_id,
            destination_depot_id=dest_id,
            total_distance_km=dist,
            estimated_duration_mins=dur,
            base_fare=base_f,
            is_active=True
        )
        db.add(r)
        db.flush()
        route_records.append(r)

        # Add RouteStops with stages and distance
        num_stops = len(stops_seq)
        stage_dist = dist / max(num_stops - 1, 1)
        stage_time = dur / max(num_stops - 1, 1)

        for seq, s_name in enumerate(stops_seq, 1):
            st_obj = stop_map[s_name]
            rs = RouteStop(
                route_id=r.id,
                stop_id=st_obj.id,
                stop_sequence=seq,
                stage_number=seq,
                distance_from_origin_km=round((seq - 1) * stage_dist, 1),
                travel_time_mins=int((seq - 1) * stage_time),
                fare_from_origin=round(max(10.0, (seq - 1) * (base_f / max(num_stops - 1, 1))), 1)
            )
            db.add(rs)
    db.commit()

    # 10. Schedules & Duties
    print("-> Seeding Daily Schedules and Rosters...")
    schedules = []
    duty_records = []
    trip_records = []

    # Times across the day
    departure_times = ["05:30", "07:00", "08:30", "10:00", "12:00", "14:30", "16:00", "18:00", "20:30", "22:00"]

    for r_idx, r in enumerate(route_records):
        for t_idx, dept_t in enumerate(departure_times[:4]): # 4 schedules per route
            sch = Schedule(
                route_id=r.id,
                departure_time=dept_t,
                arrival_time=f"{(int(dept_t[:2]) + 5) % 24:02d}:{dept_t[3:]}",
                frequency_mins=90,
                days_of_week=[1, 2, 3, 4, 5, 6, 7],
                is_active=True
            )
            db.add(sch)
            schedules.append(sch)
    db.commit()

    # Duties for today & upcoming
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    active_buses = [b for b in bus_records if b.status == "active"]
    for i, sch in enumerate(schedules[:40]):
        assigned_bus = active_buses[i % len(active_buses)]
        driver = driver_users[i % len(driver_users)]
        conductor = conductor_users[i % len(conductor_users)]

        d = Duty(
            depot_id=assigned_bus.depot_id,
            schedule_id=sch.id,
            bus_id=assigned_bus.id,
            driver_id=driver.id,
            conductor_id=conductor.id,
            duty_date=today_str,
            status="active" if i < 15 else "scheduled",
            check_in_time=datetime.utcnow() - timedelta(hours=2) if i < 15 else None
        )
        db.add(d)
        duty_records.append(d)
    db.commit()

    # 11. Seed 2,000 Historical Trips & 30 Days Synthetic GPS / Demand
    print("-> Seeding 2,000 Historical Trips and 30-Day Demand History...")
    now = datetime.utcnow()
    trip_statuses = ["completed", "completed", "completed", "completed", "delayed"]

    # Pre-generate 2,000 historical trips over the last 30 days
    historical_trips = []
    for t_idx in range(2000):
        r = random.choice(route_records)
        days_ago = random.randint(1, 30)
        hour_of_day = random.randint(5, 22)
        trip_start = now - timedelta(days=days_ago, hours=now.hour - hour_of_day, minutes=random.randint(0, 59))
        trip_end = trip_start + timedelta(minutes=r.estimated_duration_mins + random.randint(-15, 30))

        bus = random.choice(active_buses)
        st = random.choice(trip_statuses)
        tr = Trip(
            route_id=r.id,
            bus_id=bus.id,
            start_time=trip_start,
            end_time=trip_end,
            status=st,
            current_stage=5,
            delay_minutes=random.randint(5, 25) if st == "delayed" else 0
        )
        historical_trips.append(tr)

    # Add active trips for today
    for d in duty_records[:15]:
        tr = Trip(
            duty_id=d.id,
            route_id=d.schedule.route_id,
            bus_id=d.bus_id,
            start_time=now - timedelta(minutes=45),
            status="in_transit",
            current_stage=2,
            delay_minutes=0
        )
        historical_trips.append(tr)

    # Batch commit trips
    for i in range(0, len(historical_trips), 250):
        db.add_all(historical_trips[i:i+250])
        db.commit()

    print(f"-> Committed {len(historical_trips)} trips.")

    # 12. Synthetic GPS Pings for Active Buses
    print("-> Seeding GPS Pings for Live Fleet Simulation...")
    active_trips = [t for t in historical_trips if t.status == "in_transit"]
    gps_pings_batch = []

    for at in active_trips:
        # Generate 10 consecutive pings along route
        base_lat = 13.0674
        base_lon = 80.2057
        for p_idx in range(10):
            ping = GpsPing(
                bus_id=at.bus_id,
                trip_id=at.id,
                latitude=base_lat - (p_idx * 0.05),
                longitude=base_lon - (p_idx * 0.03),
                speed_kmh=round(random.uniform(35.0, 65.0), 1),
                heading=210.0,
                timestamp=now - timedelta(seconds=(10 - p_idx) * 5),
                is_deviated=False
            )
            gps_pings_batch.append(ping)
    db.add_all(gps_pings_batch)
    db.commit()

    # 13. Seed Bookings, Tickets, Payments, and Refunds
    print("-> Seeding Sample Bookings, HMAC QR Tickets, and Refunds...")
    sample_stops = list(stop_map.values())
    bookings_batch = []
    tickets_batch = []
    payments_batch = []

    for b_idx in range(120):
        p_user = random.choice(passenger_users[:100])
        tr = random.choice(historical_trips[:500])
        from_st = sample_stops[0]
        to_st = sample_stops[min(3, len(sample_stops)-1)]
        ref = f"TNK-{100000 + b_idx}"
        fare = round(random.uniform(45.0, 320.0), 2)
        b_status = "confirmed" if b_idx < 100 else "cancelled"

        booking = Booking(
            user_id=p_user.id,
            trip_id=tr.id,
            from_stop_id=from_st.id,
            to_stop_id=to_st.id,
            booking_reference=ref,
            total_fare=fare,
            status=b_status,
            booking_channel="app",
            payment_status="paid" if b_status == "confirmed" else "refunded"
        )
        db.add(booking)
        db.flush()

        # Payment
        pay = Payment(
            booking_id=booking.id,
            transaction_ref=f"TXN-PAY-{uuid.uuid4().hex[:12].upper()}",
            payment_method=random.choice(["upi", "card", "netbanking"]),
            amount=fare,
            status="success",
            gateway_response={"gateway": "MockRazorpay", "status": "authorized"}
        )
        db.add(pay)
        db.flush()

        # Ticket with QR
        from backend.app.services.qr_service import generate_qr_ticket_payload
        qr_payload, qr_sig = generate_qr_ticket_payload(
            ticket_id=str(uuid.uuid4()),
            booking_ref=ref,
            trip_id=tr.id,
            passenger_name=p_user.full_name,
            seat_number=(b_idx % 40) + 1,
            fare=fare
        )

        ticket = Ticket(
            booking_id=booking.id,
            seat_number=(b_idx % 40) + 1,
            passenger_name=p_user.full_name,
            passenger_age=32,
            passenger_gender="F" if "a" in p_user.full_name.lower() else "M",
            qr_code_data=qr_payload,
            qr_signature=qr_sig,
            status="valid" if b_status == "confirmed" else "cancelled"
        )
        db.add(ticket)

        # Add refund for cancelled booking
        if b_status == "cancelled":
            ref_amt = round(fare * 0.75, 2)
            refund = Refund(
                booking_id=booking.id,
                payment_id=pay.id,
                refund_amount=ref_amt,
                penalty_amount=round(fare - ref_amt, 2),
                reason="Passenger requested cancellation > 6 hours prior to departure",
                status="processed"
            )
            db.add(refund)

    db.commit()

    # 14. Attendance & Pre-trip Inspections
    print("-> Seeding Attendance records and Pre-trip Inspections...")
    for idx, d in enumerate(duty_records[:20]):
        # Driver check-in
        att_drv = Attendance(
            user_id=d.driver_id,
            depot_id=d.depot_id,
            check_in=datetime.utcnow() - timedelta(hours=3),
            check_out=None,
            status="present",
            date=today_str
        )
        # Conductor check-in
        att_cnd = Attendance(
            user_id=d.conductor_id,
            depot_id=d.depot_id,
            check_in=datetime.utcnow() - timedelta(hours=3),
            check_out=None,
            status="present",
            date=today_str
        )
        # Pre-trip Inspection
        insp = Inspection(
            duty_id=d.id,
            bus_id=d.bus_id,
            inspector_id=d.driver_id,
            brakes_ok=True,
            tires_ok=True,
            wipers_ok=True,
            lights_ok=True,
            emergency_exit_ok=True,
            remarks="All safety checks passed before trip rollout",
            passed=True
        )
        db.add_all([att_drv, att_cnd, insp])
    db.commit()

    # 15. Maintenance & Fuel Records
    print("-> Seeding Maintenance and Fuel Logs for Fleet...")
    for b in bus_records[:30]:
        maint = MaintenanceRecord(
            bus_id=b.id,
            depot_id=b.depot_id,
            service_type="preventive",
            cost=random.choice([3500.0, 7200.0, 12000.0]),
            odometer_reading_km=b.mileage_km - 450.0,
            description="Routine oil change, air filter replacement, and brake pad inspection",
            technician_name="Rajan M"
        )
        fuel = FuelRecord(
            bus_id=b.id,
            depot_id=b.depot_id,
            liters=round(random.uniform(65.0, 140.0), 1),
            cost_per_liter=94.50,
            total_cost=round(100.0 * 94.50, 2),
            odometer_km=b.mileage_km,
            fuel_station=f"{b.depot.name} Fuel Outlet",
            fuel_date=yesterday_str
        )
        db.add_all([maint, fuel])
    db.commit()

    # 16. Complaints & Lost/Found
    print("-> Seeding Public Complaints and Lost & Found items...")
    complaint_samples = [
        ("Driver Behavior", "Driver was driving aggressively and honking excessively near Perambalur bypass."),
        ("Cleanliness", "Bus seats and floor were not properly swept at Madurai terminal."),
        ("Punctuality", "Bus arrived 40 minutes late without prior SMS alert at Koyambedu."),
        ("Ticketing", "Conductor machine gave duplicate receipt printout."),
        ("AC Malfunction", "AC blower was not cooling in coach seat 14-16 during afternoon trip.")
    ]
    for c_cat, c_desc in complaint_samples:
        comp = Complaint(
            user_id=demo_passenger.id,
            category=c_cat,
            user_category=c_cat,
            description=c_desc,
            photo_url="/uploads/complaints/sample_issue.jpg",
            status="open",
            depot_id=depot_chn.id
        )
        db.add(comp)

    # Lost and Found (1 matched pair)
    lost_item = LostFound(
        report_type="lost",
        user_id=demo_passenger.id,
        depot_id=depot_mdu.id,
        item_name="Brown Leather Wallet",
        description="Lost brown Titan leather wallet containing college ID and bus pass near seat 12",
        category="Wallet",
        contact_info="9876543210",
        status="matched"
    )
    db.add(lost_item)
    db.flush()

    found_item = LostFound(
        report_type="found",
        user_id=conductor_users[0].id,
        depot_id=depot_mdu.id,
        item_name="Brown Titan Wallet",
        description="Found brown leather wallet under seat 12 during post-trip cleaning at Mattuthavani",
        category="Wallet",
        contact_info="0452-2566777",
        status="matched",
        matched_id=lost_item.id
    )
    db.add(found_item)
    db.flush()
    lost_item.matched_id = found_item.id
    db.commit()

    # 17. Seed Employee Pass Applications & Passes
    print("-> Seeding Employee Family Pass Applications and Issued Passes...")
    for idx, f_mem in enumerate(family_members_list[:5]):
        emp = f_mem.employee
        app = PassApplication(
            employee_id=emp.id,
            family_member_id=f_mem.id,
            pass_type="family",
            academic_year_or_period="2026-2027",
            status="admin_approved" if idx < 3 else "submitted",
            depot_reviewer_id=mgr_users[0].id,
            depot_reviewed_at=datetime.utcnow() - timedelta(days=2) if idx < 3 else None,
            admin_reviewer_id=admin_user.id if idx < 3 else None,
            admin_reviewed_at=datetime.utcnow() - timedelta(days=1) if idx < 3 else None
        )
        db.add(app)
        db.flush()

        if app.status == "admin_approved":
            from backend.app.services.qr_service import generate_qr_pass_payload
            p_payload, p_sig = generate_qr_pass_payload(
                pass_id=str(uuid.uuid4()),
                pass_number=f"TN-PASS-{202600 + idx}",
                employee_code=emp.employee_code,
                holder_name=f_mem.full_name,
                holder_type=f_mem.relation_type,
                valid_until="2027-03-31"
            )
            issued_pass = Pass(
                application_id=app.id,
                pass_number=f"TN-PASS-{202600 + idx}",
                holder_name=f_mem.full_name,
                holder_type=f_mem.relation_type,
                valid_from="2026-04-01",
                valid_until="2027-03-31",
                qr_code_data=p_payload,
                qr_signature=p_sig,
                status="active"
            )
            db.add(issued_pass)
    db.commit()

    # 18. Autopilot Recurring Commute Rules
    print("-> Seeding Journey Autopilot recurring rules...")
    auto_rule = AutopilotRule(
        user_id=demo_passenger.id,
        route_id=route_records[0].id,
        preferred_time_start="07:30",
        preferred_time_end="09:00",
        days_of_week=[1, 2, 3, 4, 5],
        max_fare_limit=150.0,
        max_monthly_bookings=22,
        current_month_bookings=4,
        is_active=True,
        consent_given=True,
        consent_timestamp=datetime.utcnow() - timedelta(days=10)
    )
    db.add(auto_rule)
    db.commit()

    # 19. Initial Audit Logs
    print("-> Seeding Audit Logs...")
    audit1 = AuditLog(
        user_id=admin_user.id,
        role="admin",
        depot_id=depot_chn.id,
        action="SEED_DATABASE",
        entity_name="System",
        new_values={"details": "Initial synthetic dataset loaded across 4 depots with 60 buses and 20 routes."},
        ip_address="127.0.0.1"
    )
    db.add(audit1)
    db.commit()

    db.close()
    print("=" * 60)
    print("SUCCESS: DATABASE SEEDING COMPLETED WITH FULL REALISTIC DATASET!")
    print("=" * 60)

if __name__ == "__main__":
    run_seed()
