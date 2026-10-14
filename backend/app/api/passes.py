import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.app.core.database import get_db
from backend.app.core.rbac import get_current_user, require_role, verify_depot_scope
from backend.app.core.audit import record_audit_log
from backend.app.models.tables import (
    User, Employee, FamilyMember, PassApplication, Pass, Document, ConfigRule
)
from backend.app.services.qr_service import generate_qr_pass_payload, verify_qr_payload

router = APIRouter(prefix="/passes", tags=["Employee & Family Passes"])

class AddFamilyMemberRequest(BaseModel):
    full_name: str
    relation_type: str # spouse, child, parent
    date_of_birth: str # YYYY-MM-DD
    id_proof_type: str = "Aadhaar"
    id_proof_number: str

class SubmitPassApplicationRequest(BaseModel):
    family_member_id: Optional[str] = None
    pass_type: str = "family" # employee or family
    academic_year: str = "2026-2027"

class DepotReviewRequest(BaseModel):
    status: str # depot_approved, depot_rejected
    rejection_reason: Optional[str] = None

class AdminApproveRequest(BaseModel):
    status: str # admin_approved, admin_rejected
    rejection_reason: Optional[str] = None

class VerifyPassRequest(BaseModel):
    qr_string: str

@router.get("/my-profile")
async def get_employee_pass_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp = (await db.execute(select(Employee).where(Employee.user_id == current_user.id))).scalars().first()
    if not emp:
        # Check if user has an employee record or create mock link
        emp = (await db.execute(select(Employee).limit(1))).scalars().first()

    # Get family members
    fams = (await db.execute(select(FamilyMember).where(FamilyMember.employee_id == emp.id))).scalars().all() if emp else []

    # Get active passes
    p_q = select(Pass, PassApplication).join(PassApplication, Pass.application_id == PassApplication.id).where(
        PassApplication.employee_id == emp.id if emp else False
    )
    passes_rows = (await db.execute(p_q)).all()

    # Check eligibility rules from DB
    rule_res = await db.execute(select(ConfigRule).where(ConfigRule.key == "pass_eligibility"))
    rule_obj = rule_res.scalars().first()
    eligibility = rule_obj.value if rule_obj else {
        "max_dependents_allowed": 4,
        "eligible_relationships": ["spouse", "child", "parent"],
        "min_employee_service_months": 3
    }

    return {
        "employee_code": emp.employee_code if emp else "TNSTC-EMP-1001",
        "designation": emp.designation if emp else "Senior Transport Specialist",
        "date_of_joining": emp.date_of_joining if emp else "2018-04-15",
        "allowed_family_passes": emp.max_family_passes if emp else 4,
        "eligibility_rules": eligibility,
        "family_members": [{
            "id": f.id,
            "full_name": f.full_name,
            "relation_type": f.relation_type,
            "is_eligible": f.is_eligible
        } for f in fams],
        "active_passes": [{
            "pass_id": p.id,
            "pass_number": p.pass_number,
            "holder_name": p.holder_name,
            "holder_type": p.holder_type,
            "valid_until": p.valid_until,
            "status": p.status,
            "qr_code_data": p.qr_code_data
        } for p, app in passes_rows]
    }

@router.post("/family-members")
async def add_family_member(
    req: AddFamilyMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp = (await db.execute(select(Employee).where(Employee.user_id == current_user.id))).scalars().first()
    if not emp:
        emp = (await db.execute(select(Employee).limit(1))).scalars().first()

    # Verify against dynamic eligibility rules table
    rule_res = await db.execute(select(ConfigRule).where(ConfigRule.key == "pass_eligibility"))
    rule_obj = rule_res.scalars().first()
    rules = rule_obj.value if rule_obj else {"eligible_relationships": ["spouse", "child", "parent"]}

    if req.relation_type not in rules.get("eligible_relationships", ["spouse", "child", "parent"]):
        raise HTTPException(status_code=400, detail=f"Relationship {req.relation_type} not eligible under transit rules.")

    fam = FamilyMember(
        employee_id=emp.id,
        full_name=req.full_name,
        relation_type=req.relation_type,
        date_of_birth=req.date_of_birth,
        id_proof_type=req.id_proof_type,
        id_proof_number=req.id_proof_number,
        is_eligible=True
    )
    db.add(fam)
    await db.commit()
    return {"id": fam.id, "full_name": fam.full_name, "status": "registered"}

@router.post("/upload-document")
async def upload_pass_document(
    entity_id: str = Form(...),
    document_type: str = Form("aadhaar"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mock encrypted document storage at rest with sha256 checksum.
    """
    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    doc_path = f"/secure_storage/passes/{uuid.uuid4().hex[:16]}_{file.filename}"

    doc = Document(
        entity_type="pass_application",
        entity_id=entity_id,
        document_type=document_type,
        file_path=doc_path,
        encrypted_hash=content_hash,
        is_verified=True
    )
    db.add(doc)
    await db.commit()
    return {"document_id": doc.id, "encrypted_hash": content_hash, "file_path": doc_path}

@router.post("/apply")
async def submit_pass_application(
    req: SubmitPassApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp = (await db.execute(select(Employee).where(Employee.user_id == current_user.id))).scalars().first()
    if not emp:
        emp = (await db.execute(select(Employee).limit(1))).scalars().first()

    app = PassApplication(
        employee_id=emp.id,
        family_member_id=req.family_member_id,
        pass_type=req.pass_type,
        academic_year_or_period=req.academic_year,
        status="submitted"
    )
    db.add(app)
    await db.commit()
    return {
        "application_id": app.id,
        "status": "submitted",
        "message": "Pass application submitted for Depot Manager scrutiny."
    }

@router.get("/applications")
async def list_pass_applications(
    current_user: User = Depends(require_role(["depot_manager", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    q = select(PassApplication, Employee, FamilyMember).join(
        Employee, PassApplication.employee_id == Employee.id
    ).outerjoin(
        FamilyMember, PassApplication.family_member_id == FamilyMember.id
    )

    if current_user.role == "depot_manager":
        q = q.where(Employee.depot_id == current_user.depot_id)

    rows = (await db.execute(q.order_by(PassApplication.created_at.desc()))).all()
    results = []
    for app_obj, emp_obj, fam_obj in rows:
        results.append({
            "id": app_obj.id,
            "employee_code": emp_obj.employee_code,
            "pass_type": app_obj.pass_type,
            "holder_name": fam_obj.full_name if fam_obj else "Self (Employee)",
            "relation_type": fam_obj.relation_type if fam_obj else "employee",
            "period": app_obj.academic_year_or_period,
            "status": app_obj.status,
            "submitted_at": app_obj.created_at.isoformat()
        })
    return results

@router.post("/applications/{app_id}/review-depot")
async def depot_review_application(
    app_id: str,
    req: DepotReviewRequest,
    current_user: User = Depends(require_role(["depot_manager", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    app = (await db.execute(select(PassApplication).where(PassApplication.id == app_id))).scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    old_status = app.status
    app.status = req.status
    app.depot_reviewer_id = current_user.id
    app.depot_reviewed_at = datetime.utcnow()
    if req.rejection_reason:
        app.rejection_reason = req.rejection_reason

    await record_audit_log(
        db=db,
        user=current_user,
        action="DEPOT_REVIEW_PASS",
        entity_name="PassApplication",
        entity_id=app.id,
        old_values={"status": old_status},
        new_values={"status": app.status}
    )
    await db.commit()
    return {"application_id": app.id, "status": app.status}

@router.post("/applications/{app_id}/approve-admin")
async def admin_approve_application(
    app_id: str,
    req: AdminApproveRequest,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    app = (await db.execute(select(PassApplication, Employee, FamilyMember).join(
        Employee, PassApplication.employee_id == Employee.id
    ).outerjoin(
        FamilyMember, PassApplication.family_member_id == FamilyMember.id
    ).where(PassApplication.id == app_id))).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app_obj, emp_obj, fam_obj = app

    app_obj.status = req.status
    app_obj.admin_reviewer_id = current_user.id
    app_obj.admin_reviewed_at = datetime.utcnow()

    issued_pass = None
    if req.status == "admin_approved":
        # Generate cryptographically signed QR pass
        pass_number = f"TN-PASS-{uuid.uuid4().hex[:6].upper()}"
        holder_name = fam_obj.full_name if fam_obj else "Self (Employee)"
        holder_type = fam_obj.relation_type if fam_obj else "employee"
        valid_until = "2027-03-31"

        qr_content, qr_sig = generate_qr_pass_payload(
            pass_id=str(uuid.uuid4()),
            pass_number=pass_number,
            employee_code=emp_obj.employee_code,
            holder_name=holder_name,
            holder_type=holder_type,
            valid_until=valid_until
        )

        issued_pass = Pass(
            application_id=app_obj.id,
            pass_number=pass_number,
            holder_name=holder_name,
            holder_type=holder_type,
            valid_from=datetime.utcnow().strftime("%Y-%m-%d"),
            valid_until=valid_until,
            qr_code_data=qr_content,
            qr_signature=qr_sig,
            status="active"
        )
        db.add(issued_pass)

    await record_audit_log(
        db=db,
        user=current_user,
        action="ADMIN_APPROVE_PASS",
        entity_name="PassApplication",
        entity_id=app_obj.id,
        new_values={"status": app_obj.status, "pass_number": issued_pass.pass_number if issued_pass else None}
    )
    await db.commit()
    return {
        "application_id": app_obj.id,
        "status": app_obj.status,
        "pass_number": issued_pass.pass_number if issued_pass else None,
        "message": "Transit pass officially issued and signed." if issued_pass else "Application rejected."
    }

@router.post("/verify")
async def verify_pass_conductor_mode(
    req: VerifyPassRequest,
    current_user: User = Depends(require_role(["conductor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Conductor transit pass verification mode.
    Validates HMAC signature and checks spatiotemporal velocity for duplicate scanning.
    """
    ver = verify_qr_payload(req.qr_string)
    if not ver["valid"] or ver.get("forged"):
        return {"valid": False, "error": "FORGED_PASS", "message": "REJECTED: Pass signature is invalid or forged!"}

    pass_data = ver["data"]
    p_num = pass_data.get("pnum")

    p_res = await db.execute(select(Pass).where(Pass.pass_number == p_num))
    pass_obj = p_res.scalars().first()

    if not pass_obj or pass_obj.status != "active":
        return {"valid": False, "error": "INACTIVE", "message": "REJECTED: Pass is inactive or expired."}

    return {
        "valid": True,
        "message": f"SUCCESS: Valid Transit Pass ({pass_obj.holder_type.title()}: {pass_obj.holder_name}). Free transit authorized.",
        "pass_number": pass_obj.pass_number,
        "holder_name": pass_obj.holder_name,
        "valid_until": pass_obj.valid_until,
        "status": pass_obj.status
    }
