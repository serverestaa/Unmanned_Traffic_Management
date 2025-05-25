# app/monitoring/router.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, delete, text
from datetime import datetime, timedelta
import json
import asyncio
import h3
from typing import Dict, Set
from collections import defaultdict

from ..database import get_db, AsyncSessionLocal
from ..auth.utils import get_current_active_user
from ..auth.models import User
from ..drones.models import Drone
from ..flights.models import FlightRequest, RestrictedZone
from .models import TelemetryData, Alert, HexGridCell, CurrentDronePosition
from .schemas import (
    TelemetryData as TelemetryDataSchema,
    Alert as AlertSchema,
    DroneStatus,
    MonitoringDashboard,
    WebSocketMessage,
    ZoneDroneCount,
    TelemetryDataCreate
)
from ..utils.logger import setup_logger
from ..utils.geospatial import point_in_circle

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])
logger = setup_logger("utm.monitoring")


# Monitoring metrics
class MonitoringMetrics:
    def __init__(self):
        self.telemetry_processed = 0
        self.telemetry_errors = 0
        self.zone_violations = 0
        self.websocket_connections = 0
        self.processing_times = []
        self.last_reset = datetime.utcnow()

    def record_processing_time(self, time_ms: float):
        self.processing_times.append(time_ms)
        # Keep only last 1000 measurements
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-1000:]

    def get_stats(self):
        uptime = (datetime.utcnow() - self.last_reset).total_seconds()
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0

        return {
            "telemetry_processed": self.telemetry_processed,
            "telemetry_errors": self.telemetry_errors,
            "zone_violations": self.zone_violations,
            "websocket_connections": self.websocket_connections,
            "uptime_seconds": uptime,
            "telemetry_rate": self.telemetry_processed / uptime if uptime > 0 else 0,
            "avg_processing_time_ms": avg_processing_time,
            "error_rate": self.telemetry_errors / self.telemetry_processed if self.telemetry_processed > 0 else 0
        }


metrics = MonitoringMetrics()


class RestrictedZoneCache:
    def __init__(self, ttl_seconds: int = 300):  # 5 minute cache
        self.zones: List[RestrictedZone] = []
        self.last_update = None
        self.ttl_seconds = ttl_seconds
        self.lock = asyncio.Lock()

    async def get_zones(self, db: AsyncSession) -> List[RestrictedZone]:
        async with self.lock:
            now = datetime.utcnow()

            if (not self.last_update or
                    (now - self.last_update).total_seconds() > self.ttl_seconds):
                # Refresh cache
                result = await db.execute(
                    select(RestrictedZone).where(RestrictedZone.is_active == True)
                )
                self.zones = result.scalars().all()
                self.last_update = now
                logger.info(f"Refreshed restricted zone cache: {len(self.zones)} zones")

            return self.zones


zone_cache = RestrictedZoneCache()


async def check_restricted_zone_violation_optimized(
        drone_id: int,
        latitude: float,
        longitude: float,
        altitude: float,
        db: AsyncSession
) -> Optional[dict]:
    """
    Optimized zone violation check using cached zones
    """
    try:
        zones = await zone_cache.get_zones(db)

        for zone in zones:
            # Quick distance check
            if point_in_circle(latitude, longitude, zone.center_lat, zone.center_lng, zone.radius):
                # Check altitude
                if altitude > zone.max_altitude:
                    metrics.zone_violations += 1
                    return {
                        "zone_id": zone.id,
                        "zone_name": zone.name,
                        "zone_type": "restricted",
                        "severity": "high",
                        "message": f"Drone entered restricted zone: {zone.name} (altitude: {altitude}m exceeds max: {zone.max_altitude}m)"
                    }
                else:
                    metrics.zone_violations += 1
                    return {
                        "zone_id": zone.id,
                        "zone_name": zone.name,
                        "zone_type": "restricted",
                        "severity": "medium",
                        "message": f"Drone entered restricted zone: {zone.name}"
                    }

        return None

    except Exception as e:
        logger.error(f"Error checking restricted zone: {str(e)}", exc_info=True)
        return None


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
        # Store last known positions to detect zone entries
        last_positions = {}

        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(1)

            # Get current drone positions instead of telemetry for efficiency
            async with AsyncSessionLocal() as db:
                # Get all current drone positions with drone info
                result = await db.execute(
                    select(CurrentDronePosition, Drone)
                    .join(Drone, CurrentDronePosition.drone_id == Drone.id)
                    .where(CurrentDronePosition.status.in_(["airborne", "hovering"]))
                )
                current_positions = result.all()

                if current_positions:
                    drone_telemetry = {}
                    restricted_zone_alerts = []

                    for position, drone in current_positions:
                        # Check if position was updated recently (within last 30 seconds)
                        if (datetime.utcnow() - position.last_update).total_seconds() > 30:
                            continue

                        drone_telemetry[position.drone_id] = {
                            "drone_id": position.drone_id,
                            "drone_info": {
                                "brand": drone.brand,
                                "model": drone.model,
                                "serial_number": drone.serial_number
                            },
                            "latitude": position.latitude,
                            "longitude": position.longitude,
                            "altitude": position.altitude,
                            "speed": position.speed,
                            "heading": position.heading,
                            "battery_level": position.battery_level,
                            "status": position.status,
                            "timestamp": position.last_update.isoformat(),
                            "flight_request_id": position.flight_request_id
                        }

                        # Check for restricted zone violations
                        violation = await check_restricted_zone_violation_optimized(
                            position.drone_id,
                            position.latitude,
                            position.longitude,
                            position.altitude,
                            db
                        )

                        if violation:
                            # Check if this is a new violation
                            last_pos = last_positions.get(position.drone_id)
                            is_new_violation = True

                            if last_pos:
                                last_violation = await check_restricted_zone_violation_optimized(
                                    position.drone_id,
                                    last_pos['latitude'],
                                    last_pos['longitude'],
                                    last_pos['altitude'],
                                    db
                                )
                                if last_violation and last_violation['zone_id'] == violation['zone_id']:
                                    is_new_violation = False

                            if is_new_violation:
                                # Check if alert already exists
                                existing_alert = await db.execute(
                                    select(Alert)
                                    .where(
                                        and_(
                                            Alert.drone_id == position.drone_id,
                                            Alert.alert_type == "restricted_zone_violation",
                                            Alert.is_resolved == False,
                                            Alert.created_at > datetime.utcnow() - timedelta(minutes=5)
                                        )
                                    )
                                )
                                if not existing_alert.scalar_one_or_none():
                                    # Create alert in database
                                    alert = Alert(
                                        drone_id=position.drone_id,
                                        flight_request_id=position.flight_request_id,
                                        alert_type="restricted_zone_violation",
                                        severity=violation['severity'],
                                        message=violation['message'],
                                        latitude=position.latitude,
                                        longitude=position.longitude,
                                        altitude=position.altitude
                                    )
                                    db.add(alert)
                                    await db.commit()
                                    await db.refresh(alert)

                                    # Add to alerts list
                                    restricted_zone_alerts.append({
                                        "alert_id": alert.id,
                                        "drone_id": position.drone_id,
                                        "zone_id": violation['zone_id'],
                                        "zone_name": violation['zone_name'],
                                        "zone_type": violation['zone_type'],
                                        "severity": violation['severity'],
                                        "message": violation['message'],
                                        "latitude": position.latitude,
                                        "longitude": position.longitude,
                                        "altitude": position.altitude,
                                        "timestamp": datetime.utcnow().isoformat()
                                    })

                        # Update last known position
                        last_positions[position.drone_id] = {
                            'latitude': position.latitude,
                            'longitude': position.longitude,
                            'altitude': position.altitude
                        }

                    # Send telemetry update
                    if drone_telemetry:
                        await websocket.send_text(json.dumps({
                            "type": "telemetry_update",
                            "data": list(drone_telemetry.values())
                        }))

                    # Send restricted zone alerts if any
                    if restricted_zone_alerts:
                        await websocket.send_text(json.dumps({
                            "type": "restricted_zone_alert",
                            "data": restricted_zone_alerts
                        }))

                        # Also broadcast to all connected clients
                        await manager.broadcast({
                            "type": "restricted_zone_alert",
                            "data": restricted_zone_alerts
                        })

                # Clean up stale positions (older than 5 minutes)
                stale_time = datetime.utcnow() - timedelta(minutes=5)
                await db.execute(
                    delete(CurrentDronePosition)
                    .where(
                        and_(
                            CurrentDronePosition.last_update < stale_time,
                            CurrentDronePosition.status.in_(["landed", "emergency", "disconnected"])
                        )
                    )
                )
                await db.commit()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


@router.get("/dashboard", response_model=MonitoringDashboard)
async def get_monitoring_dashboard_optimized(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Optimized dashboard endpoint with efficient queries"""
    # Use a single query to get all needed data
    dashboard_query = """
        WITH active_flights AS (
            SELECT COUNT(*) as count
            FROM flight_requests
            WHERE status IN ('approved', 'active')
            AND planned_start_time <= NOW()
            AND planned_end_time >= NOW()
        ),
        total_drones AS (
            SELECT COUNT(*) as count
            FROM drones
            WHERE ($1 = 'admin' OR owner_id = $2)
        ),
        active_alerts AS (
            SELECT COUNT(*) as count
            FROM alerts
            WHERE is_resolved = FALSE
        ),
        drone_positions AS (
            SELECT 
                d.id as drone_id,
                d.brand,
                d.model,
                d.serial_number,
                d.owner_id,
                cp.flight_request_id,
                cp.latitude,
                cp.longitude,
                cp.altitude,
                cp.speed,
                cp.heading,
                cp.battery_level,
                cp.status,
                cp.last_update
            FROM drones d
            JOIN current_drone_positions cp ON d.id = cp.drone_id
            WHERE ($1 = 'admin' OR d.owner_id = $2)
            AND cp.status IN ('airborne', 'hovering')
        )
        SELECT 
            (SELECT count FROM active_flights) as active_flights,
            (SELECT count FROM total_drones) as total_drones,
            (SELECT count FROM active_alerts) as active_alerts,
            (SELECT json_agg(drone_positions.*) FROM drone_positions) as drone_statuses
    """

    result = await db.execute(
        text(dashboard_query),
        {"1": current_user.role, "2": str(current_user.id)}
    )
    row = result.first()

    # Process drone statuses
    drone_statuses = []
    if row.drone_statuses:
        for drone_data in row.drone_statuses:
            # Get alerts for this drone
            alerts_result = await db.execute(
                select(Alert)
                .filter(
                    and_(
                        Alert.drone_id == drone_data['drone_id'],
                        Alert.is_resolved == False
                    )
                )
                .order_by(desc(Alert.created_at))
                .limit(5)
            )
            alerts = alerts_result.scalars().all()

            drone_status = DroneStatus(
                drone_id=drone_data['drone_id'],
                drone_info={
                    "id": drone_data['drone_id'],
                    "brand": drone_data['brand'],
                    "model": drone_data['model'],
                    "serial_number": drone_data['serial_number'],
                    "owner_id": str(drone_data['owner_id'])
                },
                latest_telemetry=TelemetryDataSchema(
                    id=0,
                    drone_id=drone_data['drone_id'],
                    flight_request_id=drone_data['flight_request_id'],
                    latitude=drone_data['latitude'],
                    longitude=drone_data['longitude'],
                    altitude=drone_data['altitude'],
                    speed=drone_data['speed'],
                    heading=drone_data['heading'],
                    battery_level=drone_data['battery_level'],
                    status=drone_data['status'],
                    timestamp=drone_data['last_update']
                ),
                active_alerts=alerts,
                flight_request_id=drone_data['flight_request_id']
            )
            drone_statuses.append(drone_status)

    return MonitoringDashboard(
        active_flights=row.active_flights or 0,
        total_drones=row.total_drones or 0,
        active_alerts=row.active_alerts or 0,
        drone_statuses=drone_statuses
    )


@router.get("/zones/hex/{h3_index}", response_model=ZoneDroneCount)
async def get_drones_in_hex(
        h3_index: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all drones currently in a specific hexagonal zone."""
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

        # Get or create hex cell
        hex_cell = await db.execute(
            select(HexGridCell).where(HexGridCell.h3_index == h3_index)
        )
        hex_cell = hex_cell.scalar_one_or_none()

        if not hex_cell:
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

    # Check permissions
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
    telemetry: TelemetryDataCreate,
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

        # Get old hex cell if drone is moving from one hex to another
        old_hex_cell = None
        if current_pos and current_pos.hex_cell_id != hex_cell.id:
            old_hex_cell = await db.execute(
                select(HexGridCell).where(HexGridCell.id == current_pos.hex_cell_id)
            )
            old_hex_cell = old_hex_cell.scalar_one_or_none()

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
            # Increment drone count for new hex cell
            if hex_cell.drones_count:
                hex_cell.drones_count += 1
            else:
                hex_cell.drones_count = 1

        # Update drone counts if drone moved between hex cells
        if old_hex_cell:
            if old_hex_cell.drones_count:
                old_hex_cell.drones_count-= 1
            else:
                old_hex_cell.drones_count = 0

            if hex_cell.drones_count:
                hex_cell.drones_count += 1
            else:
                hex_cell.drones_count = 1
        
        await db.commit()
        await db.refresh(db_telemetry)
        return db_telemetry
        
    except Exception as e:
        logger.error(f"Error processing telemetry data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing telemetry data"
        )


@router.get("/zone/drones", response_model=List[ZoneDroneCount])
async def get_zone_drones(
    zones: str = Query(..., description="Comma-separated list of H3 indices"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get drones in specified H3 zones with optimized spatial querying.
    Uses both H3 indices and spatial indexes for maximum performance.
    """
    # Split the comma-separated zones into a list
    zone_list = zones.split(',')
    
    # First get the hex cells for the given H3 indices
    hex_cells = await db.execute(
        select(HexGridCell)
        .where(HexGridCell.h3_index.in_(zone_list))
    )
    hex_cells = hex_cells.scalars().all()
    
    if not hex_cells:
        return []
    
    # Get all drones in these cells with a single optimized query
    result = await db.execute(
        select(
            HexGridCell,
            func.count(CurrentDronePosition.id).label('drone_count'),
            func.json_agg(
                func.json_build_object(
                    'id', CurrentDronePosition.id,
                    'drone_id', CurrentDronePosition.drone_id,
                    'flight_request_id', CurrentDronePosition.flight_request_id,
                    'hex_cell_id', CurrentDronePosition.hex_cell_id,
                    'latitude', CurrentDronePosition.latitude,
                    'longitude', CurrentDronePosition.longitude,
                    'altitude', CurrentDronePosition.altitude,
                    'speed', CurrentDronePosition.speed,
                    'heading', CurrentDronePosition.heading,
                    'battery_level', CurrentDronePosition.battery_level,
                    'status', CurrentDronePosition.status,
                    'last_update', CurrentDronePosition.last_update
                )
            ).label('drones')
        )
        .join(CurrentDronePosition, CurrentDronePosition.hex_cell_id == HexGridCell.id)
        .where(HexGridCell.id.in_([cell.id for cell in hex_cells]))
        .group_by(HexGridCell.id)
    )
    
    zone_counts = []
    for row in result:
        zone_counts.append(ZoneDroneCount(
            hex_cell=row[0],
            drone_count=row[1],
            drones=row[2] if row[2] else []
        ))
    
    return zone_counts


@router.post("/telemetry/process", response_model=TelemetryDataSchema)
async def process_telemetry(
    telemetry: TelemetryDataCreate,
    db: AsyncSession = Depends(get_db)
):
    return await process_telemetry_data(telemetry, db)


@router.get("/all-hex")
async def get_all_hex(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all hexagonal grid cells from the database.
    Returns a list of all hex cells with their properties.
    """
    try:
        # Query all hex cells
        result = await db.execute(
            select(HexGridCell)
            .order_by(HexGridCell.h3_index)
        )
        hex_cells = result.scalars().all()
        
        # Convert to list of dictionaries for proper serialization
        hex_cells_data = []
        for cell in hex_cells:
            hex_cells_data.append({
                "id": cell.id,
                "h3_index": cell.h3_index,
                "center_lat": cell.center_lat,
                "center_lng": cell.center_lng,
                "created_at": cell.created_at,
                "last_updated": cell.last_updated
            })
        
        return hex_cells_data
        
    except Exception as e:
        logger.error(f"Error retrieving hex cells: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving hex cells"
        )


@router.get("/metrics")
async def get_monitoring_metrics(
        current_user: User = Depends(get_current_active_user)
):
    """Get monitoring system metrics"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access metrics"
        )

    return metrics.get_stats()