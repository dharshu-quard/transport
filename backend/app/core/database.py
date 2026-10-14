from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# Async Engine for FastAPI Endpoints
async_connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    async_connect_args["check_same_thread"] = False

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=async_connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Sync Engine for Seeding, Migrations, and Tests
sync_connect_args = {}
if "sqlite" in settings.DATABASE_SYNC_URL:
    sync_connect_args["check_same_thread"] = False

sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=False,
    connect_args=sync_connect_args
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
