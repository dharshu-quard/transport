from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.models.tables import User

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    token_query: Optional[str] = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials if credentials else token_query
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    query = select(User).where(User.id == user_id, User.is_deleted == False)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )
    return user

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == "admin":
            return current_user # Admin has superuser access
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {allowed_roles}"
            )
        return current_user
    return role_checker

def verify_depot_scope(user: User, target_depot_id: Optional[str]) -> bool:
    """Depot managers see only their depot. Admin sees all."""
    if user.role == "admin":
        return True
    if user.role == "depot_manager":
        if not target_depot_id or user.depot_id == target_depot_id:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access or mutate resources outside assigned depot."
        )
    return True
