# app/monitoring/router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta
import json
import asyncio

from ..database import get_db
from ..auth.utils import get_current_active_user
from ..auth.models import User
from ..drones.models import Drone
from ..flights.models import FlightRequest
from .models import TelemetryData, Alert
from .schemas import (
    TelemetryData as TelemetryDataSchema,
    Alert as AlertSchema,
    DroneStatus,
    MonitoringDashboard,
    WebSocketMessage
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                dead_connections.append(connection)

        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(1)

            # Get latest telemetry data
            async with AsyncSessionLocal() as db:
                # Get recent telemetry (last 10 seconds)
                recent_time = datetime.utcnow() - timedelta(seconds=10)
                result = await db.execute(
                    select(TelemetryData)
                    .filter(TelemetryData.timestamp > recent_time)
                    .order_by(desc(TelemetryData.timestamp))
                )
                recent_telemetry = result.scalars().all()

                if recent_telemetry:
                    # Group by drone_id and get latest for each
                    drone_telemetry = {}
                    for t in recent_telemetry:
                        if t.drone_id not in drone_telemetry:
                            drone_telemetry[t.drone_id] = {
                                "drone_id": t.drone_id,
                                "latitude": t.latitude,
                                "longitude": t.longitude,
                                "altitude": t.altitude,
                                "speed": t.speed,
                                "heading": t.heading,
                                "battery_level": t.battery_level,
                                "status": t.status,
                                "timestamp": t.timestamp.isoformat(),
                                "flight_request_id": t.flight_request_id
                            }

                    # Send telemetry update
                    await websocket.send_text(json.dumps({
                        "type": "telemetry_update",
                        "data": list(drone_telemetry.values())
                    }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/dashboard", response_model=MonitoringDashboard)
async def get_monitoring_dashboard(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Get active flights count
    now = datetime.utcnow()
    active_flights_result = await db.execute(
        select(func.count(FlightRequest.id)).filter(
            and_(
                FlightRequest.status.in_(["approved", "active"]),
                FlightRequest.planned_start_time <= now,
                FlightRequest.planned_end_time >= now
            )
        )
    )
    active_flights = active_flights_result.scalar()

    # Get total drones count (user's drones or all if admin)
    if current_user.role == "admin":
        total_drones_result = await db.execute(select(func.count(Drone.id)))
    else:
        total_drones_result = await db.execute(
            select(func.count(Drone.id)).filter(Drone.owner_id == current_user.id)
        )
    total_drones = total_drones_result.scalar()

    # Get active alerts count
    active_alerts_result = await db.execute(
        select(func.count(Alert.id)).filter(Alert.is_resolved == False)
    )
    active_alerts = active_alerts_result.scalar()

    # Get drone statuses
    drone_statuses = []

    # Get drones with recent telemetry (last 5 minutes)
    recent_time = datetime.utcnow() - timedelta(minutes=5)

    if current_user.role == "admin":
        drones_query = select(Drone)
    else:
        drones_query = select(Drone).filter(Drone.owner_id == current_user.id)

    drones_result = await db.execute(drones_query)
    drones = drones_result.scalars().all()

    for drone in drones:
        # Get latest telemetry
        telemetry_result = await db.execute(
            select(TelemetryData)
            .filter(TelemetryData.drone_id == drone.id)
            .order_by(desc(TelemetryData.timestamp))
            .limit(1)
        )
        latest_telemetry = telemetry_result.scalar_one_or_none()

        # Get active alerts for this drone
        alerts_result = await db.execute(
            select(Alert)
            .filter(and_(Alert.drone_id == drone.id, Alert.is_resolved == False))
            .order_by(desc(Alert.created_at))
        )
        drone_alerts = alerts_result.scalars().all()

        # Get current flight request if any
        current_flight = None
        if latest_telemetry and latest_telemetry.flight_request_id:
            current_flight = latest_telemetry.flight_request_id

        drone_status = DroneStatus(
            drone_id=drone.id,
            drone_info={
                "id": drone.id,
                "brand": drone.brand,
                "model": drone.model,
                "serial_number": drone.serial_number,
                "owner_id": drone.owner_id
            },
            latest_telemetry=latest_telemetry,
            active_alerts=drone_alerts,
            flight_request_id=current_flight
        )
        drone_statuses.append(drone_status)

    return MonitoringDashboard(
        active_flights=active_flights,
        total_drones=total_drones,
        active_alerts=active_alerts,
        drone_statuses=drone_statuses
    )


@router.get("/telemetry/{drone_id}", response_model=List[TelemetryDataSchema])
async def get_drone_telemetry(
        drone_id: int,
        hours: int = 1,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Check drone access
    drone_result = await db.execute(select(Drone).filter(Drone.id == drone_id))
    drone = drone_result.scalar_one_or_none()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )

    if drone.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get telemetry data
    since_time = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(TelemetryData)
        .filter(and_(
            TelemetryData.drone_id == drone_id,
            TelemetryData.timestamp > since_time
        ))
        .order_by(desc(TelemetryData.timestamp))
    )

    return result.scalars().all()


@router.get("/alerts/", response_model=List[AlertSchema])
async def get_alerts(
        resolved: bool = False,
        hours: int = 24,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    since_time = datetime.utcnow() - timedelta(hours=hours)

    # Build query based on user role
    if current_user.role == "admin":
        query = select(Alert).filter(
            and_(
                Alert.is_resolved == resolved,
                Alert.created_at > since_time
            )
        )
    else:
        # Only show alerts for user's drones
        query = select(Alert).join(Drone).filter(
            and_(
                Alert.is_resolved == resolved,
                Alert.created_at > since_time,
                Drone.owner_id == current_user.id
            )
        )

    result = await db.execute(query.order_by(desc(Alert.created_at)))
    return result.scalars().all()


@router.put("/alerts/{alert_id}/resolve", response_model=AlertSchema)
async def resolve_alert(
        alert_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Alert).filter(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Check permissions (admin or drone owner)
    if current_user.role != "admin":
        drone_result = await db.execute(select(Drone).filter(Drone.id == alert.drone_id))
        drone = drone_result.scalar_one()
        if drone.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

    # Resolve alert
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id

    await db.commit()
    await db.refresh(alert)

    # Broadcast alert resolution
    await manager.broadcast({
        "type": "alert_resolved",
        "data": {
            "alert_id": alert.id,
            "drone_id": alert.drone_id,
            "resolved_by": current_user.full_name
        }
    })

    return alert


# Import here to avoid circular imports
from ..database import AsyncSessionLocal