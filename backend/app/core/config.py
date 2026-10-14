import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "TamilNadu Transit 360 AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "tnstc-transit-360-super-secret-key-production-change-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DEV_OTP: str = "123456"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./transit360.db"
    DATABASE_SYNC_URL: str = "sqlite:///./transit360.db"

    # HMAC QR Secret
    QR_SIGNING_SECRET: str = "transit-360-tamper-proof-qr-secret-key-chennai-2026"

    # Ports
    BACKEND_PORT: int = 8000
    ADMIN_WEB_PORT: int = 5173
    MOBILE_WEB_PORT: int = 8081

    # Feature Toggles / Mocks
    MOCK_FCM: bool = True
    MOCK_PAYMENT_GATEWAY: bool = True
    MOCK_GOV_REGISTRY: bool = True
    ENABLE_GPS_SIMULATOR: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
