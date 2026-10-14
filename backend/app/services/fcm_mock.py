from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.tables import Notification
from backend.app.core.i18n import get_text

class MockNotificationService:
    """
    Mock FCM adapter storing bilingual notifications in-app.
    """
    @staticmethod
    async def send_notification(
        db: AsyncSession,
        user_id: str,
        title_key: str,
        body_key: str,
        notification_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        custom_title_en: Optional[str] = None,
        custom_title_ta: Optional[str] = None,
        custom_body_en: Optional[str] = None,
        custom_body_ta: Optional[str] = None
    ) -> Notification:
        title_en = custom_title_en or get_text(title_key, "en")
        title_ta = custom_title_ta or get_text(title_key, "ta")
        body_en = custom_body_en or get_text(body_key, "en")
        body_ta = custom_body_ta or get_text(body_key, "ta")

        notif = Notification(
            user_id=user_id,
            title=title_en,
            title_ta=title_ta,
            body=body_en,
            body_ta=body_ta,
            channel="in_app",
            notification_type=notification_type,
            metadata_json=metadata or {}
        )
        db.add(notif)
        await db.flush()
        return notif

notification_service = MockNotificationService()
