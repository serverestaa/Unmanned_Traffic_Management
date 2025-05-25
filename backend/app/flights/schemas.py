# app/flights/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class WaypointBase(BaseModel):
    latitude: float
    longitude: float


class WaypointCreate(WaypointBase):
    sequence: int


class Waypoint(WaypointBase):
    id: int
    sequence: int
    flight_request_id: int

    class Config:
        from_attributes = True


class RestrictedZoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    center_lat: float
    center_lng: float
    radius: float
    max_altitude: Optional[float] = 0.0


class RestrictedZoneCreate(RestrictedZoneBase):
    pass


class RestrictedZoneUpdate(BaseModel):
    radius: float
    max_altitude: Optional[float] = None


class RestrictedZone(RestrictedZoneBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class FlightRequestBase(BaseModel):
    drone_id: int
    planned_start_time: datetime
    planned_end_time: datetime
    max_altitude: float
    purpose: Optional[str] = None


class FlightRequestCreate(FlightRequestBase):
    waypoints: List[WaypointCreate]


class FlightRequestUpdate(BaseModel):
    status: Optional[str] = None
    approval_notes: Optional[str] = None


class FlightRequest(FlightRequestBase):
    id: int
    pilot_id: uuid.UUID
    status: str
    approval_notes: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FlightRequestWithDetails(FlightRequest):
    waypoints: List[WaypointBase] = []
    drone: dict  # Basic drone info
    pilot: dict  # Basic pilot info


class ConflictCheck(BaseModel):
    has_conflicts: bool
    conflicts: List[str] = []
    restricted_zones: List[RestrictedZone] = []