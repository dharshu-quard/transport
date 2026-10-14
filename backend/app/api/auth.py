from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password, create_access_token, create_refresh_token, verify_otp, decode_token
)
from backend.app.core.rbac import get_current_user
from backend.app.models.tables import User, Depot

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginPasswordRequest(BaseModel):
    phone_or_email: str
    password: str

class LoginOtpRequest(BaseModel):
    phone: str
    otp: str

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/login-otp")
async def login_with_otp(req: LoginOtpRequest, db: AsyncSession = Depends(get_db)):
    """
    OTP login endpoint. Accepts phone and dev OTP (123456) per specification rules.
    """
    if not verify_otp(req.phone, req.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Use test OTP: 123456"
        )

    # Look up user by phone
    query = select(User).where(User.phone == req.phone, User.is_deleted == False)
    res = await db.execute(query)
    user = res.scalars().first()

    if not user:
        # Create passenger user automatically if phone doesn't exist yet
        user = User(
            phone=req.phone,
            full_name=f"Commuter ({req.phone[-4:]})",
            role="passenger",
            preferred_language="ta"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token_data = {"sub": user.id, "role": user.role, "depot_id": user.depot_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
            "role": user.role,
            "depot_id": user.depot_id,
            "preferred_language": user.preferred_language
        }
    }

@router.post("/login-password")
async def login_with_password(req: LoginPasswordRequest, db: AsyncSession = Depends(get_db)):
    query = select(User).where(
        (User.phone == req.phone_or_email) | (User.email == req.phone_or_email),
        User.is_deleted == False
    )
    res = await db.execute(query)
    user = res.scalars().first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone/email or password credentials."
        )

    token_data = {"sub": user.id, "role": user.role, "depot_id": user.depot_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
            "role": user.role,
            "depot_id": user.depot_id,
            "preferred_language": user.preferred_language
        }
    }

@router.post("/refresh")
async def refresh_access_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    res = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer active")

    token_data = {"sub": user.id, "role": user.role, "depot_id": user.depot_id}
    new_access_token = create_access_token(token_data)
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    depot_name = None
    if current_user.depot_id:
        d_res = await db.execute(select(Depot).where(Depot.id == current_user.depot_id))
        d_obj = d_res.scalars().first()
        if d_obj:
            depot_name = d_obj.name

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "email": current_user.email,
        "role": current_user.role,
        "depot_id": current_user.depot_id,
        "depot_name": depot_name,
        "preferred_language": current_user.preferred_language
    }
