import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.app.core.config import settings
from backend.app.core.database import Base, sync_engine
import backend.app.models.tables # Ensure all models are registered

# Import API Routers
from backend.app.api.auth import router as auth_router
from backend.app.api.passenger import router as passenger_router
from backend.app.api.tracking import router as tracking_router
from backend.app.api.driver import router as driver_router
from backend.app.api.conductor import router as conductor_router
from backend.app.api.admin import router as admin_router
from backend.app.api.passes import router as passes_router
from backend.app.api.autopilot import router as autopilot_router
from backend.app.api.support import router as support_router
from backend.app.api.ai_insights import router as ai_router

from backend.app.services.gps_simulator import run_gps_simulation_tick
from backend.app.services.autopilot_service import execute_autopilot_cycle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transit360")

scheduler = AsyncIOScheduler()
gps_task = None

async def gps_simulator_loop():
    logger.info("[GPS Simulator] Background simulation loop started (5s ticks).")
    while True:
        try:
            await run_gps_simulation_tick()
        except Exception as e:
            logger.error(f"[GPS Simulator] Error in tick: {e}")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=sync_engine)
    logger.info("[Startup] Database schema verified.")

    # Start APScheduler for Journey Autopilot
    scheduler.add_job(execute_autopilot_cycle, "interval", seconds=60, id="autopilot_job")
    scheduler.start()
    logger.info("[Startup] APScheduler started for Journey Autopilot.")

    # Start GPS Simulator background task
    global gps_task
    if settings.ENABLE_GPS_SIMULATOR:
        gps_task = asyncio.create_task(gps_simulator_loop())

    yield

    # Shutdown
    if gps_task:
        gps_task.cancel()
    if scheduler.running:
        scheduler.shutdown()
    logger.info("[Shutdown] Background services stopped.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="TamilNadu Transit 360 AI - Complete Intelligent Public Transit System Prototype",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix="/api")
app.include_router(passenger_router, prefix="/api")
app.include_router(tracking_router, prefix="/api")
app.include_router(driver_router, prefix="/api")
app.include_router(conductor_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(passes_router, prefix="/api")
app.include_router(autopilot_router, prefix="/api")
app.include_router(support_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "system": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "mock_adapters": {
            "fcm": settings.MOCK_FCM,
            "payment_gateway": settings.MOCK_PAYMENT_GATEWAY,
            "gov_registry": settings.MOCK_GOV_REGISTRY
        },
        "gps_simulator_active": True,
        "scheduler_running": scheduler.running
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
