# app/monitoring/router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta
import json
import asyncio
import h3

from ..database import get_db
from ..auth.utils import get_current_active_user
from ..auth.models import User
from ..drones.models import Drone
from ..flights.models import FlightRequest
from .models import TelemetryData, Alert, HexGridCell, CurrentDronePosition
from .schemas import (
    TelemetryData as TelemetryDataSchema,
    Alert as AlertSchema,
    DroneStatus,
    MonitoringDashboard,
    WebSocketMessage,
    ZoneDroneCount
)
from ..utils.logger import setup_logger

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

logger = setup_logger("utm.monitoring")


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


@router.get("/zones/hex/{h3_index}", response_model=ZoneDroneCount)
async def get_drones_in_hex(
    h3_index: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all drones currently in a specific hexagonal zone.
    The h3_index should be at resolution 8 (approximately 0.74 km² cells).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access zone monitoring"
        )

    try:
        # Validate h3_index
        if not h3.h3_is_valid(h3_index):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid H3 index"
            )

        # Get hex cell
        hex_cell = await db.execute(
            select(HexGridCell).where(HexGridCell.h3_index == h3_index)
        )
        hex_cell = hex_cell.scalar_one_or_none()
        
        if not hex_cell:
            # Create new hex cell if it doesn't exist
            center = h3.h3_to_geo(h3_index)
            hex_cell = HexGridCell(
                h3_index=h3_index,
                center_lat=center[0],
                center_lng=center[1]
            )
            db.add(hex_cell)
            await db.commit()
            await db.refresh(hex_cell)

        # Get all drones in this hex cell
        drones = await db.execute(
            select(CurrentDronePosition)
            .where(CurrentDronePosition.hex_cell_id == hex_cell.id)
        )
        drones = drones.scalars().all()

        return ZoneDroneCount(
            hex_cell=hex_cell,
            drone_count=len(drones),
            drones=drones
        )

    except Exception as e:
        logger.error(f"Error getting drones in hex {h3_index}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving zone data"
        )


@router.get("/zones/latlng/{lat}/{lng}", response_model=ZoneDroneCount)
async def get_drones_at_location(
    lat: float,
    lng: float,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all drones in the hexagonal zone containing the given latitude/longitude.
    Uses H3 resolution 8 (approximately 0.74 km² cells).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access zone monitoring"
        )

    try:
        # Convert lat/lng to H3 index at resolution 8
        h3_index = h3.geo_to_h3(lat, lng, 8)
        
        # Reuse the hex endpoint logic
        return await get_drones_in_hex(h3_index, db, current_user)

    except Exception as e:
        logger.error(f"Error getting drones at {lat},{lng}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving zone data"
        )


async def process_telemetry_data(
    telemetry: TelemetryDataSchema,
    db: AsyncSession
) -> TelemetryData:
    """Process incoming telemetry data and update current position"""
    try:
        # Create telemetry record
        db_telemetry = TelemetryData(**telemetry.model_dump())
        db.add(db_telemetry)
        
        # Get hex cell for current position
        h3_index = h3.geo_to_h3(telemetry.latitude, telemetry.longitude, 8)
        hex_cell = await db.execute(
            select(HexGridCell).where(HexGridCell.h3_index == h3_index)
        )
        hex_cell = hex_cell.scalar_one_or_none()
        
        if not hex_cell:
            logger.warning(f"No hex cell found for H3 index {h3_index}. Position may be outside Kazakhstan.")
            # Still create telemetry record but skip position update
            await db.commit()
            await db.refresh(db_telemetry)
            return db_telemetry
        
        # Update or create current position
        current_pos = await db.execute(
            select(CurrentDronePosition)
            .where(CurrentDronePosition.drone_id == telemetry.drone_id)
        )
        current_pos = current_pos.scalar_one_or_none()
        
        if current_pos:
            # Update existing position
            current_pos.hex_cell_id = hex_cell.id
            current_pos.latitude = telemetry.latitude
            current_pos.longitude = telemetry.longitude
            current_pos.altitude = telemetry.altitude
            current_pos.speed = telemetry.speed
            current_pos.heading = telemetry.heading
            current_pos.battery_level = telemetry.battery_level
            current_pos.status = telemetry.status
            current_pos.flight_request_id = telemetry.flight_request_id
        else:
            # Create new position
            current_pos = CurrentDronePosition(
                drone_id=telemetry.drone_id,
                flight_request_id=telemetry.flight_request_id,
                hex_cell_id=hex_cell.id,
                latitude=telemetry.latitude,
                longitude=telemetry.longitude,
                altitude=telemetry.altitude,
                speed=telemetry.speed,
                heading=telemetry.heading,
                battery_level=telemetry.battery_level,
                status=telemetry.status
            )
            db.add(current_pos)
        
        await db.commit()
        await db.refresh(db_telemetry)
        return db_telemetry
        
    except Exception as e:
        logger.error(f"Error processing telemetry data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing telemetry data"
        )


# Import here to avoid circular imports
from ..database import AsyncSessionLocal