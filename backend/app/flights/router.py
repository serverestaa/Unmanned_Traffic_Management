# app/flights/router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from geoalchemy2.functions import ST_GeomFromText
from datetime import datetime
from ..utils.logger import setup_logger

from ..database import get_db
from ..auth.utils import get_current_active_user
from ..auth.models import User
from ..drones.models import Drone
from ..utils.geospatial import route_intersects_zone, create_linestring_from_waypoints, calculate_distance
from .models import FlightRequest, RestrictedZone, Waypoint
from .schemas import (
    FlightRequestCreate, FlightRequestUpdate, FlightRequest as FlightRequestSchema,
    FlightRequestWithDetails, RestrictedZoneCreate, RestrictedZone as RestrictedZoneSchema,
    ConflictCheck, WaypointBase, RestrictedZoneUpdate
)

router = APIRouter(prefix="/flights", tags=["Flights"])
logger = setup_logger("utm.flights")


@router.post("/restricted-zones", response_model=RestrictedZoneSchema)
async def create_restricted_zone(
        zone: RestrictedZoneCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Only admins can create restricted zones
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    db_zone = RestrictedZone(**zone.dict())
    db.add(db_zone)
    await db.commit()
    await db.refresh(db_zone)
    return db_zone


@router.get("/restricted-zones", response_model=List[RestrictedZoneSchema])
async def get_restricted_zones(
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RestrictedZone).filter(RestrictedZone.is_active == True)
    )
    return result.scalars().all()


@router.post("/check-conflicts", response_model=ConflictCheck)
async def check_route_conflicts(
        waypoints: List[WaypointBase],  # [{"latitude": float, "longitude": float, "altitude": float}]
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    conflicts = []
    conflicting_zones = []

    # Get all active restricted zones
    result = await db.execute(
        select(RestrictedZone).filter(RestrictedZone.is_active == True)
    )
    restricted_zones = result.scalars().all()

    # Convert waypoints to coordinate tuples
    route_points = [(wp.latitude, wp.longitude) for wp in waypoints]

    for zone in restricted_zones:
        # Check if route intersects with restricted zone
        if route_intersects_zone(route_points, zone.center_lat, zone.center_lng, zone.radius):
            conflicts.append(f"Route intersects with restricted zone: {zone.name}")
            distance = calculate_distance(route_points[0][0], route_points[0][1], zone.center_lat, zone.center_lng)
            conflicts.append(f"Distance to the restricted zone: {distance}m, while restricted zone radius is {zone.radius}m")
            conflicting_zones.append(zone)

        # Check altitude conflicts for waypoints in zone
        for wp in waypoints:
            if (wp.altitude > zone.max_altitude and
                    route_intersects_zone([(wp.latitude, wp.longitude)],
                                          zone.center_lat, zone.center_lng, zone.radius)):
                conflicts.append(
                    f"Altitude {wp.altitude}m exceeds limit {zone.max_altitude}m in zone: {zone.name}"
                )

    return ConflictCheck(
        has_conflicts=len(conflicts) > 0,
        conflicts=conflicts,
        restricted_zones=conflicting_zones
    )


@router.post("/requests", response_model=FlightRequestWithDetails)
async def create_flight_request(
        flight_request: FlightRequestCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Verify drone ownership
    result = await db.execute(
        select(Drone).filter(
            and_(Drone.id == flight_request.drone_id, Drone.owner_id == current_user.id)
        )
    )
    drone = result.scalar_one_or_none()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found or not owned by user"
        )

    # Check for conflicts
    waypoints_data = [
        WaypointBase(latitude=wp.latitude, longitude=wp.longitude, altitude=wp.altitude)
        for wp in flight_request.waypoints
    ]
    conflicts = await check_route_conflicts(waypoints_data, db, current_user)

    if conflicts.has_conflicts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Route conflicts detected: {'; '.join(conflicts.conflicts)}"
        )

    # Create flight request
    route_points = [(wp.latitude, wp.longitude) for wp in flight_request.waypoints]
    route_wkt = create_linestring_from_waypoints(route_points)

    db_flight_request = FlightRequest(
        drone_id=flight_request.drone_id,
        pilot_id=current_user.id,
        planned_start_time=flight_request.planned_start_time,
        planned_end_time=flight_request.planned_end_time,
        max_altitude=flight_request.max_altitude,
        purpose=flight_request.purpose,
        route=ST_GeomFromText(route_wkt, 4326)
    )
    db.add(db_flight_request)
    await db.flush()  # Get the ID

    # Create waypoints
    for wp in flight_request.waypoints:
        db_waypoint = Waypoint(
            flight_request_id=db_flight_request.id,
            sequence=wp.sequence,
            latitude=wp.latitude,
            longitude=wp.longitude,
            altitude=wp.altitude
        )
        db.add(db_waypoint)

    await db.commit()
    await db.refresh(db_flight_request)

    # Get waypoints
    waypoints_result = await db.execute(
        select(Waypoint)
        .filter(Waypoint.flight_request_id == db_flight_request.id)
        .order_by(Waypoint.sequence)
    )
    waypoints = waypoints_result.scalars().all()

    # Get drone and pilot info
    drone_result = await db.execute(select(Drone).filter(Drone.id == db_flight_request.drone_id))
    drone = drone_result.scalar_one()

    pilot_result = await db.execute(select(User).filter(User.id == db_flight_request.pilot_id))
    pilot = pilot_result.scalar_one()

    # Construct the response using model_dump() for SQLAlchemy models
    response_data = {
        "id": db_flight_request.id,
        "drone_id": db_flight_request.drone_id,
        "pilot_id": db_flight_request.pilot_id,
        "planned_start_time": db_flight_request.planned_start_time,
        "planned_end_time": db_flight_request.planned_end_time,
        "max_altitude": db_flight_request.max_altitude,
        "purpose": db_flight_request.purpose,
        "status": db_flight_request.status,
        "approval_notes": db_flight_request.approval_notes,
        "approved_by": db_flight_request.approved_by,
        "created_at": db_flight_request.created_at,
        "approved_at": db_flight_request.approved_at,
        "waypoints": waypoints,
        "drone": {
            "id": drone.id,
            "brand": drone.brand,
            "model": drone.model,
            "serial_number": drone.serial_number
        },
        "pilot": {
            "id": pilot.id,
            "full_name": pilot.full_name,
            "email": pilot.email
        }
    }

    return FlightRequestWithDetails(**response_data)


@router.get("/requests", response_model=List[FlightRequestWithDetails])
async def get_my_flight_requests(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Get flight requests
    result = await db.execute(
        select(FlightRequest).filter(FlightRequest.pilot_id == current_user.id)
    )
    flight_requests = result.scalars().all()
    
    # For each flight request, get waypoints, drone, and pilot info
    detailed_requests = []
    for flight_request in flight_requests:
        # Get waypoints
        waypoints_result = await db.execute(
            select(Waypoint)
            .filter(Waypoint.flight_request_id == flight_request.id)
            .order_by(Waypoint.sequence)
        )
        waypoints = waypoints_result.scalars().all()

        # Get drone info
        drone_result = await db.execute(select(Drone).filter(Drone.id == flight_request.drone_id))
        drone = drone_result.scalar_one()

        # Get pilot info
        pilot_result = await db.execute(select(User).filter(User.id == flight_request.pilot_id))
        pilot = pilot_result.scalar_one()

        # Convert waypoints to dictionaries
        waypoints_data = [
            {
                "id": wp.id,
                "sequence": wp.sequence,
                "latitude": wp.latitude,
                "longitude": wp.longitude,
                "altitude": wp.altitude,
                "flight_request_id": wp.flight_request_id
            }
            for wp in waypoints
        ]

        # Construct response data
        response_data = {
            "id": flight_request.id,
            "drone_id": flight_request.drone_id,
            "pilot_id": flight_request.pilot_id,
            "planned_start_time": flight_request.planned_start_time,
            "planned_end_time": flight_request.planned_end_time,
            "max_altitude": flight_request.max_altitude,
            "purpose": flight_request.purpose,
            "status": flight_request.status,
            "approval_notes": flight_request.approval_notes,
            "approved_by": flight_request.approved_by,
            "created_at": flight_request.created_at,
            "approved_at": flight_request.approved_at,
            "waypoints": waypoints_data,
            "drone": {
                "id": drone.id,
                "brand": drone.brand,
                "model": drone.model,
                "serial_number": drone.serial_number
            },
            "pilot": {
                "id": pilot.id,
                "full_name": pilot.full_name,
                "email": pilot.email
            }
        }
        detailed_requests.append(FlightRequestWithDetails(**response_data))

    return detailed_requests


@router.get("/requests/all", response_model=List[FlightRequestWithDetails])
async def get_all_flight_requests(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Only admins can see all flight requests
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get all flight requests
    result = await db.execute(select(FlightRequest))
    flight_requests = result.scalars().all()
    
    # For each flight request, get waypoints, drone, and pilot info
    detailed_requests = []
    for flight_request in flight_requests:
        # Get waypoints
        waypoints_result = await db.execute(
            select(Waypoint)
            .filter(Waypoint.flight_request_id == flight_request.id)
            .order_by(Waypoint.sequence)
        )
        waypoints = waypoints_result.scalars().all()

        # Get drone info
        drone_result = await db.execute(select(Drone).filter(Drone.id == flight_request.drone_id))
        drone = drone_result.scalar_one()

        # Get pilot info
        pilot_result = await db.execute(select(User).filter(User.id == flight_request.pilot_id))
        pilot = pilot_result.scalar_one()

        # Convert waypoints to dictionaries
        waypoints_data = [
            {
                "id": wp.id,
                "sequence": wp.sequence,
                "latitude": wp.latitude,
                "longitude": wp.longitude,
                "altitude": wp.altitude,
                "flight_request_id": wp.flight_request_id
            }
            for wp in waypoints
        ]

        # Construct response data
        response_data = {
            "id": flight_request.id,
            "drone_id": flight_request.drone_id,
            "pilot_id": flight_request.pilot_id,
            "planned_start_time": flight_request.planned_start_time,
            "planned_end_time": flight_request.planned_end_time,
            "max_altitude": flight_request.max_altitude,
            "purpose": flight_request.purpose,
            "status": flight_request.status,
            "approval_notes": flight_request.approval_notes,
            "approved_by": flight_request.approved_by,
            "created_at": flight_request.created_at,
            "approved_at": flight_request.approved_at,
            "waypoints": waypoints_data,
            "drone": {
                "id": drone.id,
                "brand": drone.brand,
                "model": drone.model,
                "serial_number": drone.serial_number
            },
            "pilot": {
                "id": pilot.id,
                "full_name": pilot.full_name,
                "email": pilot.email
            }
        }
        detailed_requests.append(FlightRequestWithDetails(**response_data))

    return detailed_requests


@router.get("/requests/{request_id}", response_model=FlightRequestWithDetails)
async def get_flight_request(
        request_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(FlightRequest).filter(FlightRequest.id == request_id)
    )
    flight_request = result.scalar_one_or_none()
    if not flight_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight request not found"
        )

    # Check permissions
    if flight_request.pilot_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get waypoints
    waypoints_result = await db.execute(
        select(Waypoint)
        .filter(Waypoint.flight_request_id == request_id)
        .order_by(Waypoint.sequence)
    )
    waypoints = waypoints_result.scalars().all()

    # Get drone and pilot info
    drone_result = await db.execute(select(Drone).filter(Drone.id == flight_request.drone_id))
    drone = drone_result.scalar_one()

    pilot_result = await db.execute(select(User).filter(User.id == flight_request.pilot_id))
    pilot = pilot_result.scalar_one()

    # Convert waypoints to dictionaries
    waypoints_data = [
        {
            "id": wp.id,
            "sequence": wp.sequence,
            "latitude": wp.latitude,
            "longitude": wp.longitude,
            "altitude": wp.altitude,
            "flight_request_id": wp.flight_request_id
        }
        for wp in waypoints
    ]

    # Construct response data
    response_data = {
        "id": flight_request.id,
        "drone_id": flight_request.drone_id,
        "pilot_id": flight_request.pilot_id,
        "planned_start_time": flight_request.planned_start_time,
        "planned_end_time": flight_request.planned_end_time,
        "max_altitude": flight_request.max_altitude,
        "purpose": flight_request.purpose,
        "status": flight_request.status,
        "approval_notes": flight_request.approval_notes,
        "approved_by": flight_request.approved_by,
        "created_at": flight_request.created_at,
        "approved_at": flight_request.approved_at,
        "waypoints": waypoints_data,
        "drone": {
            "id": drone.id,
            "brand": drone.brand,
            "model": drone.model,
            "serial_number": drone.serial_number
        },
        "pilot": {
            "id": pilot.id,
            "full_name": pilot.full_name,
            "email": pilot.email
        }
    }

    return FlightRequestWithDetails(**response_data)


@router.put("/requests/{request_id}", response_model=FlightRequestSchema)
async def update_flight_request_status(
        request_id: int,
        update_data: FlightRequestUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(FlightRequest).filter(FlightRequest.id == request_id)
    )
    flight_request = result.scalar_one_or_none()
    if not flight_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight request not found"
        )

    # Only admins can approve/reject requests
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Update request
    if update_data.status:
        flight_request.status = update_data.status
        if update_data.status in ["approved", "rejected"]:
            from datetime import datetime
            flight_request.approved_at = datetime.utcnow()
            flight_request.approved_by = current_user.id

    if update_data.approval_notes:
        flight_request.approval_notes = update_data.approval_notes

    await db.commit()
    await db.refresh(flight_request)
    return flight_request


@router.delete("/restricted-zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restricted_zone(
        zone_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Delete a restricted zone. Only admins can delete zones.
    """
    # Only admins can delete restricted zones
    if current_user.role != "admin":
        logger.warning(f"Non-admin user {current_user.email} attempted to delete restricted zone {zone_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get the zone
    result = await db.execute(
        select(RestrictedZone).filter(RestrictedZone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    
    if not zone:
        logger.warning(f"Attempted to delete non-existent restricted zone {zone_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricted zone not found"
        )

    # Check if there are any active flight requests that intersect with this zone
    current_time = datetime.utcnow()
    result = await db.execute(
        select(FlightRequest).filter(
            and_(
                FlightRequest.status.in_(["approved", "active"]),
                FlightRequest.planned_end_time > current_time
            )
        )
    )
    active_flights = result.scalars().all()

    for flight in active_flights:
        # Get waypoints for the flight
        waypoints_result = await db.execute(
            select(Waypoint)
            .filter(Waypoint.flight_request_id == flight.id)
            .order_by(Waypoint.sequence)
        )
        waypoints = waypoints_result.scalars().all()
        route_points = [(wp.latitude, wp.longitude) for wp in waypoints]

        if route_intersects_zone(route_points, zone.center_lat, zone.center_lng, zone.radius):
            logger.warning(f"Cannot delete zone {zone_id} as it intersects with active flight {flight.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete zone as it intersects with active flight request {flight.id}"
            )

    # Delete the zone
    try:
        await db.delete(zone)
        await db.commit()
        logger.info(f"Restricted zone {zone_id} deleted by admin {current_user.email}")
    except Exception as e:
        logger.error(f"Error deleting restricted zone {zone_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting restricted zone"
        )


@router.put("/restricted-zones/{zone_id}", response_model=RestrictedZoneSchema)
async def update_restricted_zone(
        zone_id: int,
        zone_update: RestrictedZoneUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Update the radius and/or max altitude of a restricted zone.
    Only admins can update restricted zones.
    """
    # Only admins can update restricted zones
    if current_user.role != "admin":
        logger.warning(f"Non-admin user {current_user.email} attempted to update restricted zone {zone_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get the zone
    result = await db.execute(
        select(RestrictedZone).filter(RestrictedZone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    
    if not zone:
        logger.warning(f"Attempted to update non-existent restricted zone {zone_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricted zone not found"
        )

    # Check if there are any active flight requests that would be affected by this change
    current_time = datetime.utcnow()
    result = await db.execute(
        select(FlightRequest).filter(
            and_(
                FlightRequest.status.in_(["approved", "active"]),
                FlightRequest.planned_end_time > current_time
            )
        )
    )
    active_flights = result.scalars().all()

    for flight in active_flights:
        # Get waypoints for the flight
        waypoints_result = await db.execute(
            select(Waypoint)
            .filter(Waypoint.flight_request_id == flight.id)
            .order_by(Waypoint.sequence)
        )
        waypoints = waypoints_result.scalars().all()
        route_points = [(wp.latitude, wp.longitude) for wp in waypoints]

        # Check if the flight would be affected by the new radius
        if route_intersects_zone(route_points, zone.center_lat, zone.center_lng, zone_update.radius):
            logger.warning(f"Cannot update zone {zone_id} as it would affect active flight {flight.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update zone as it would affect active flight request {flight.id}"
            )

    # Update the zone
    try:
        zone.radius = zone_update.radius
        if zone_update.max_altitude is not None:
            zone.max_altitude = zone_update.max_altitude
        
        await db.commit()
        await db.refresh(zone)
        logger.info(f"Restricted zone {zone_id} updated by admin {current_user.email}")
        return zone
    except Exception as e:
        logger.error(f"Error updating restricted zone {zone_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating restricted zone"
        )