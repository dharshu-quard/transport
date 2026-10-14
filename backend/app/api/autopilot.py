import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.rbac import get_current_user
from backend.app.models.tables import User, AutopilotRule, Route, Booking, AuditLog
from backend.app.services.autopilot_service import execute_autopilot_cycle

router = APIRouter(prefix="/autopilot", tags=["Journey Autopilot"])

class CreateAutopilotPlanRequest(BaseModel):
    route_id: str
    preferred_time_start: str = "07:30"
    preferred_time_end: str = "09:00"
    days_of_week: List[int] = [1, 2, 3, 4, 5] # Monday-Friday
    max_fare_limit: float = 150.0
    max_monthly_bookings: int = 22
    consent_given: bool = True

@router.post("/plan")
async def create_or_update_autopilot_plan(
    req: CreateAutopilotPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not req.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Explicit user consent is mandatory for recurring automatic bookings."
        )

    # Check if user already has an active rule
    res = await db.execute(select(AutopilotRule).where(
        AutopilotRule.user_id == current_user.id,
        AutopilotRule.is_deleted == False
    ))
    rule = res.scalars().first()

    if not rule:
        rule = AutopilotRule(
            user_id=current_user.id,
            route_id=req.route_id,
            preferred_time_start=req.preferred_time_start,
            preferred_time_end=req.preferred_time_end,
            days_of_week=req.days_of_week,
            max_fare_limit=req.max_fare_limit,
            max_monthly_bookings=req.max_monthly_bookings,
            current_month_bookings=0,
            is_active=True,
            consent_given=True,
            consent_timestamp=datetime.utcnow()
        )
        db.add(rule)
    else:
        rule.route_id = req.route_id
        rule.preferred_time_start = req.preferred_time_start
        rule.preferred_time_end = req.preferred_time_end
        rule.days_of_week = req.days_of_week
        rule.max_fare_limit = req.max_fare_limit
        rule.max_monthly_bookings = req.max_monthly_bookings
        rule.is_active = True
        rule.consent_given = True

    await db.commit()
    return {
        "rule_id": rule.id,
        "is_active": rule.is_active,
        "message": "Journey Autopilot plan activated with explicit consent. Your regular commute is now automated."
    }

@router.get("/plan")
async def get_autopilot_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AutopilotRule, Route).join(
        Route, AutopilotRule.route_id == Route.id
    ).where(
        AutopilotRule.user_id == current_user.id,
        AutopilotRule.is_deleted == False
    ))
    row = res.first()
    if not row:
        return {"has_plan": False, "plan": None}

    rule, route = row

    # Fetch recent automated bookings
    bk_q = select(Booking).where(
        Booking.user_id == current_user.id,
        Booking.booking_channel == "autopilot"
    ).order_by(Booking.created_at.desc()).limit(5)
    bookings = (await db.execute(bk_q)).scalars().all()

    return {
        "has_plan": True,
        "plan": {
            "id": rule.id,
            "route_id": rule.route_id,
            "route_name": route.name,
            "preferred_window": f"{rule.preferred_time_start} - {rule.preferred_time_end}",
            "days_of_week": rule.days_of_week,
            "max_fare_limit": rule.max_fare_limit,
            "max_monthly_bookings": rule.max_monthly_bookings,
            "current_month_bookings": rule.current_month_bookings,
            "is_active": rule.is_active,
            "consent_timestamp": rule.consent_timestamp.isoformat() if rule.consent_timestamp else None,
            "last_run_at": rule.last_run_at.isoformat() if rule.last_run_at else None,
            "recent_automated_bookings": [{
                "reference": b.booking_reference,
                "fare": b.total_fare,
                "status": b.status,
                "created_at": b.created_at.isoformat()
            } for b in bookings]
        }
    }

@router.post("/plan/toggle")
async def toggle_autopilot_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AutopilotRule).where(
        AutopilotRule.user_id == current_user.id,
        AutopilotRule.is_deleted == False
    ))
    rule = res.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="No active autopilot plan found")

    rule.is_active = not rule.is_active
    await db.commit()
    return {
        "is_active": rule.is_active,
        "message": f"Journey Autopilot {'resumed' if rule.is_active else 'paused'}."
    }

@router.post("/trigger-cron")
async def manual_trigger_autopilot_cycle():
    """
    Triggers an on-demand Autopilot scheduling evaluation.
    Used for automated tests and live demonstration.
    """
    res = await execute_autopilot_cycle()
    return {
        "status": "success",
        "message": "Autopilot cycle completed",
        **res
    }
