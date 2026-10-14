from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.tables import AuditLog, User

async def record_audit_log(
    db: AsyncSession,
    user: Optional[User],
    action: str,
    entity_name: str,
    entity_id: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1"
) -> AuditLog:
    """Writes an immutable audit log record for every administrative/manager mutation."""
    audit_entry = AuditLog(
        user_id=user.id if user else None,
        role=user.role if user else "system",
        depot_id=user.depot_id if user else None,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)
    await db.flush()
    return audit_entry
