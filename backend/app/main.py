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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized.")

    # Start telemetry generator
    print("Starting telemetry generator...")
    asyncio.create_task(telemetry_generator.start())
    print("Telemetry generator started.")

    yield

    # Shutdown
    print("Stopping telemetry generator...")
    telemetry_generator.stop()
    print("Application shutdown complete.")


app = FastAPI(
    title="UTM (Unmanned Traffic Management) System",
    description="MVP for drone coordination and monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(drones_router)
app.include_router(flights_router)
app.include_router(monitoring_router)


@app.get("/")
async def root():
    return {
        "message": "UTM System API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}