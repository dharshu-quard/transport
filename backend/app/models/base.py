import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class BaseModelMixin:
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            val = getattr(self, column.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[column.name] = val
        return result
