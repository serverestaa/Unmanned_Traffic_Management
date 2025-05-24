# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from .database import init_db
from .auth.router import router as auth_router
from .drones.router import router as drones_router
from .flights.router import router as flights_router
from .monitoring.router import router as monitoring_router
from .monitoring.telemetry import telemetry_generator
from .utils.logger import setup_logger
from .monitoring.scripts.populate_hex_grid import router as populate_hex_grid_router
# Set up application logger
logger = setup_logger("utm.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    # Start telemetry generator
    logger.info("Starting telemetry generator...")
    asyncio.create_task(telemetry_generator.start())
    logger.info("Telemetry generator started.")

    yield

    # Shutdown
    logger.info("Stopping telemetry generator...")
    telemetry_generator.stop()
    logger.info("Application shutdown complete.")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(drones_router)
app.include_router(flights_router)
app.include_router(monitoring_router)
app.include_router(populate_hex_grid_router, tags=["populate-hex-grid"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to UTM API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}