import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from backend.app.core.database import get_db
from backend.app.core.rbac import get_current_user, require_role
from backend.app.models.tables import User, Complaint, LostFound, Depot
from ml.complaint_classifier import classify_complaint_text

router = APIRouter(prefix="/support", tags=["Complaints & Lost and Found"])

class SubmitComplaintRequest(BaseModel):
    description: str
    user_category: Optional[str] = "General"
    photo_url: Optional[str] = None
    trip_id: Optional[str] = None
    bus_id: Optional[str] = None

class ResolveComplaintRequest(BaseModel):
    resolution: str
    status: str = "resolved"

class ReportLostFoundRequest(BaseModel):
    report_type: str # lost or found
    item_name: str
    description: str
    category: str = "Personal Belongings"
    contact_info: Optional[str] = None
    bus_id: Optional[str] = None
    depot_id: Optional[str] = None

@router.post("/complaints")
async def submit_complaint(
    req: SubmitComplaintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Run NLP Auto-Classification
    classification = classify_complaint_text(req.description)

    complaint = Complaint(
        user_id=current_user.id,
        category=classification["predicted_category"],
        user_category=req.user_category or classification["predicted_category"],
        description=req.description,
        photo_url=req.photo_url or "/uploads/complaints/default_issue.png",
        trip_id=req.trip_id,
        bus_id=req.bus_id,
        status="open",
        depot_id=current_user.depot_id or "depot-1"
    )
    db.add(complaint)
    await db.commit()

    return {
        "complaint_id": complaint.id,
        "predicted_category": classification["predicted_category"],
        "confidence": classification["confidence"],
        "routed_department": classification["routed_department"],
        "priority": classification["priority"],
        "status": "open",
        "message": f"Complaint filed. Auto-categorized as '{classification['predicted_category']}' and assigned to {classification['routed_department']}."
    }

@router.get("/complaints")
async def list_complaints(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Complaint).order_by(Complaint.created_at.desc())
    if current_user.role == "passenger":
        q = q.where(Complaint.user_id == current_user.id)
    elif current_user.role == "depot_manager":
        q = q.where(Complaint.depot_id == current_user.depot_id)

    res = await db.execute(q.limit(50))
    complaints = res.scalars().all()
    return [{
        "id": c.id,
        "category": c.category,
        "description": c.description,
        "photo_url": c.photo_url,
        "status": c.status,
        "resolution": c.resolution,
        "created_at": c.created_at.isoformat()
    } for c in complaints]

@router.post("/complaints/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: str,
    req: ResolveComplaintRequest,
    current_user: User = Depends(require_role(["depot_manager", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    c = (await db.execute(select(Complaint).where(Complaint.id == complaint_id))).scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    c.status = req.status
    c.resolution = req.resolution
    c.assigned_to = current_user.id
    await db.commit()

    return {"complaint_id": c.id, "status": c.status, "resolution": c.resolution}

@router.post("/lost-found")
async def report_lost_found(
    req: ReportLostFoundRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    lf = LostFound(
        report_type=req.report_type,
        user_id=current_user.id,
        item_name=req.item_name,
        description=req.description,
        category=req.category,
        contact_info=req.contact_info or current_user.phone,
        bus_id=req.bus_id,
        depot_id=req.depot_id or current_user.depot_id,
        status="reported"
    )
    db.add(lf)
    await db.flush()

    # Automated Matching Engine
    # If this is 'lost', search 'found' reports with similar keyword or category
    opp_type = "found" if req.report_type == "lost" else "lost"
    search_term = req.item_name.strip().split()[0] # First keyword

    match_q = select(LostFound).where(
        LostFound.report_type == opp_type,
        LostFound.status == "reported",
        or_(
            LostFound.item_name.ilike(f"%{search_term}%"),
            LostFound.description.ilike(f"%{search_term}%"),
            LostFound.category == req.category
        )
    ).limit(1)

    match_candidate = (await db.execute(match_q)).scalars().first()
    matched = False
    if match_candidate:
        matched = True
        lf.status = "matched"
        lf.matched_id = match_candidate.id
        match_candidate.status = "matched"
        match_candidate.matched_id = lf.id

    await db.commit()

    return {
        "item_id": lf.id,
        "report_type": lf.report_type,
        "status": lf.status,
        "matched": matched,
        "matched_with_item_id": lf.matched_id,
        "message": "AI MATCH FOUND! A corresponding item was previously recorded." if matched else "Report logged. We will notify you when a match is found."
    }

@router.get("/lost-found")
async def list_lost_found(
    report_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    q = select(LostFound).order_by(LostFound.created_at.desc())
    if report_type:
        q = q.where(LostFound.report_type == report_type)

    rows = (await db.execute(q.limit(40))).scalars().all()
    return [{
        "id": item.id,
        "report_type": item.report_type,
        "item_name": item.item_name,
        "description": item.description,
        "category": item.category,
        "status": item.status,
        "contact_info": item.contact_info,
        "matched_id": item.matched_id,
        "created_at": item.created_at.isoformat()
    } for item in rows]
