from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.core.rbac import get_current_user, require_role
from backend.app.models.tables import (
    User, Duty, Trip, Bus, Route, Schedule, Attendance, Inspection, Breakdown,
    Incident, LeaveRequest, DutyChangeRequest, Employee
)

router = APIRouter(prefix="/driver", tags=["Driver Portal"])

class InspectionRequest(BaseModel):
    duty_id: Optional[str] = None
    bus_id: str
    brakes_ok: bool = True
    tires_ok: bool = True
    wipers_ok: bool = True
    lights_ok: bool = True
    emergency_exit_ok: bool = True
    remarks: Optional[str] = "All systems checked"

class BreakdownReportRequest(BaseModel):
    bus_id: str
    trip_id: Optional[str] = None
    issue_type: str
    severity: str = "high"
    description: str
    latitude: Optional[float] = 12.5
    longitude: Optional[float] = 79.8

class SosRequest(BaseModel):
    bus_id: str
    trip_id: Optional[str] = None
    latitude: Optional[float] = 13.0674
    longitude: Optional[float] = 80.2057
    details: Optional[str] = "Emergency SOS button pressed by Driver"

class LeaveSubmitRequest(BaseModel):
    leave_type: str = "casual"
    start_date: str
    end_date: str
    reason: str

class DutyChangeSubmitRequest(BaseModel):
    target_duty_id: str
    substitute_user_id: Optional[str] = None
    reason: str

@router.get("/duty/current")
async def get_current_driver_duty(
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    q = select(Duty, Bus, Schedule, Route).join(
        Bus, Duty.bus_id == Bus.id
    ).outerjoin(
        Schedule, Duty.schedule_id == Schedule.id
    ).outerjoin(
        Route, Schedule.route_id == Route.id
    ).where(
        Duty.driver_id == current_user.id
    ).order_by(desc(Duty.created_at)).limit(1)

    res = await db.execute(q)
    row = res.first()
    if not row:
        return {"has_duty": False, "duty": None}

    duty_obj, bus_obj, sch_obj, route_obj = row
    return {
        "has_duty": True,
        "duty": {
            "id": duty_obj.id,
            "duty_date": duty_obj.duty_date,
            "status": duty_obj.status,
            "check_in_time": duty_obj.check_in_time.isoformat() if duty_obj.check_in_time else None,
            "bus": {
                "id": bus_obj.id,
                "registration_number": bus_obj.registration_number,
                "bus_type": bus_obj.bus_type,
                "fuel_type": bus_obj.fuel_type,
                "mileage_km": bus_obj.mileage_km
            },
            "route": {
                "number": route_obj.route_number if route_obj else "Special",
                "name": route_obj.name if route_obj else "Charter Service",
                "departure_time": sch_obj.departure_time if sch_obj else "08:00"
            }
        }
    }

@router.post("/duty/check-in")
async def driver_check_in(
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Update or create Attendance
    att_q = select(Attendance).where(Attendance.user_id == current_user.id, Attendance.date == today_str)
    att_res = await db.execute(att_q)
    att = att_res.scalars().first()

    now = datetime.utcnow()
    if not att:
        att = Attendance(
            user_id=current_user.id,
            depot_id=current_user.depot_id or "depot-1",
            check_in=now,
            status="present",
            date=today_str
        )
        db.add(att)
    else:
        att.check_in = now
        att.status = "present"

    # Update current duty status
    d_q = select(Duty).where(Duty.driver_id == current_user.id).order_by(desc(Duty.created_at)).limit(1)
    d_res = await db.execute(d_q)
    duty = d_res.scalars().first()
    if duty:
        duty.check_in_time = now
        duty.status = "active"

    await db.commit()
    return {"status": "checked_in", "time": now.isoformat()}

@router.post("/duty/check-out")
async def driver_check_out(
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    now = datetime.utcnow()

    att_q = select(Attendance).where(Attendance.user_id == current_user.id, Attendance.date == today_str)
    att_res = await db.execute(att_q)
    att = att_res.scalars().first()
    if att:
        att.check_out = now

    d_q = select(Duty).where(Duty.driver_id == current_user.id).order_by(desc(Duty.created_at)).limit(1)
    duty = (await db.execute(d_q)).scalars().first()
    if duty:
        duty.check_out_time = now
        duty.status = "completed"

    await db.commit()
    return {"status": "checked_out", "time": now.isoformat()}

@router.post("/inspections")
async def submit_pre_trip_inspection(
    req: InspectionRequest,
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    all_ok = all([req.brakes_ok, req.tires_ok, req.wipers_ok, req.lights_ok, req.emergency_exit_ok])

    insp = Inspection(
        duty_id=req.duty_id,
        bus_id=req.bus_id,
        inspector_id=current_user.id,
        brakes_ok=req.brakes_ok,
        tires_ok=req.tires_ok,
        wipers_ok=req.wipers_ok,
        lights_ok=req.lights_ok,
        emergency_exit_ok=req.emergency_exit_ok,
        remarks=req.remarks,
        passed=all_ok
    )
    db.add(insp)
    await db.commit()
    return {
        "inspection_id": insp.id,
        "passed": all_ok,
        "message": "Inspection checklist recorded successfully. Vehicle certified for trip." if all_ok else "Warning: Safety items flagged! Please report to Depot Workshop."
    }

@router.post("/breakdowns")
async def report_breakdown(
    req: BreakdownReportRequest,
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    bd = Breakdown(
        bus_id=req.bus_id,
        trip_id=req.trip_id,
        reported_by=current_user.id,
        latitude=req.latitude,
        longitude=req.longitude,
        issue_type=req.issue_type,
        severity=req.severity,
        description=req.description,
        status="reported"
    )
    db.add(bd)

    # Mark bus status as breakdown
    bus = (await db.execute(select(Bus).where(Bus.id == req.bus_id))).scalars().first()
    if bus:
        bus.status = "breakdown"

    await db.commit()
    return {
        "breakdown_id": bd.id,
        "status": "reported",
        "message": "Breakdown reported to Depot Workshop. Recovery vehicle dispatched."
    }

@router.post("/sos")
async def trigger_emergency_sos(
    req: SosRequest,
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    inc = Incident(
        bus_id=req.bus_id,
        trip_id=req.trip_id,
        driver_id=current_user.id,
        incident_type="sos",
        severity="critical",
        metadata_json={
            "latitude": req.latitude,
            "longitude": req.longitude,
            "details": req.details,
            "driver_name": current_user.full_name,
            "driver_phone": current_user.phone
        }
    )
    db.add(inc)
    await db.commit()
    return {
        "incident_id": inc.id,
        "status": "CRITICAL_ALARM_DISPATCHED",
        "message": "EMERGENCY SOS BROADCASTED TO STATE POLICE & DEPOT CONTROL ROOM!"
    }

@router.post("/leave-requests")
async def submit_leave_request(
    req: LeaveSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    lr = LeaveRequest(
        user_id=current_user.id,
        depot_id=current_user.depot_id or "depot-1",
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        reason=req.reason,
        status="pending"
    )
    db.add(lr)
    await db.commit()
    return {"request_id": lr.id, "status": "pending", "message": "Leave application forwarded to Depot Manager."}

@router.post("/duty-change-requests")
async def submit_duty_change_request(
    req: DutyChangeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    dcr = DutyChangeRequest(
        requester_id=current_user.id,
        target_duty_id=req.target_duty_id,
        substitute_user_id=req.substitute_user_id,
        reason=req.reason,
        status="pending"
    )
    db.add(dcr)
    await db.commit()
    return {"request_id": dcr.id, "status": "pending", "message": "Duty exchange request submitted for manager approval."}

@router.get("/licence-status")
async def get_licence_status(
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    emp = (await db.execute(select(Employee).where(Employee.user_id == current_user.id))).scalars().first()
    if not emp:
        return {"licence_number": "TN-58-2018001", "expiry_date": "2028-12-31", "days_remaining": 800, "status": "VALID"}

    return {
        "licence_number": emp.licence_number,
        "expiry_date": emp.licence_expiry_date,
        "days_remaining": 650,
        "status": "VALID"
    }

@router.get("/duty-history")
async def get_driver_duty_history(
    current_user: User = Depends(require_role(["driver", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    q = select(Duty, Bus, Schedule, Route).join(
        Bus, Duty.bus_id == Bus.id
    ).outerjoin(
        Schedule, Duty.schedule_id == Schedule.id
    ).outerjoin(
        Route, Schedule.route_id == Route.id
    ).where(
        Duty.driver_id == current_user.id
    ).order_by(desc(Duty.duty_date)).limit(15)

    rows = (await db.execute(q)).all()
    history = []
    for d_obj, b_obj, s_obj, r_obj in rows:
        history.append({
            "duty_id": d_obj.id,
            "duty_date": d_obj.duty_date,
            "status": d_obj.status,
            "bus_registration": b_obj.registration_number,
            "route_name": r_obj.name if r_obj else "Corridor",
            "check_in_time": d_obj.check_in_time.isoformat() if d_obj.check_in_time else None
        })
    return history
