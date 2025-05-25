# app/monitoring/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
import uuid


class TelemetryDataBase(BaseModel):
    drone_id: int
    flight_request_id: Optional[int] = None
    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    battery_level: Optional[float] = 100.0
    status: Optional[str] = "airborne"


class TelemetryDataCreate(TelemetryDataBase):
    pass


class TelemetryData(TelemetryDataBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    drone_id: int
    flight_request_id: Optional[int] = None
    alert_type: str
    severity: Optional[str] = "medium"
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    id: int
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DroneStatus(BaseModel):
    drone_id: int
    drone_info: dict
    latest_telemetry: Optional[TelemetryData] = None
    active_alerts: List[Alert] = []
    flight_request_id: Optional[int] = None


class MonitoringDashboard(BaseModel):
    active_flights: int
    total_drones: int
    active_alerts: int
    drone_statuses: List[DroneStatus] = []


class WebSocketMessage(BaseModel):
    type: str  # telemetry, alert, status_update
    data: dict


class HexGridCellBase(BaseModel):
    h3_index: str
    center_lat: float
    center_lng: float


class HexGridCell(HexGridCellBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CurrentDronePositionBase(BaseModel):
    drone_id: int
    flight_request_id: Optional[int] = None
    hex_cell_id: int
    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    battery_level: Optional[float] = 100.0
    status: Optional[str] = "airborne"


class CurrentDronePosition(CurrentDronePositionBase):
    id: int
    last_update: datetime

    class Config:
        from_attributes = True


class ZoneDroneCount(BaseModel):
    hex_cell: HexGridCell
    drone_count: int
    drones: List[CurrentDronePosition]


class RestrictedZoneInfo(BaseModel):
    id: int
    name: str
    zone_type: str
    min_altitude: float
    max_altitude: float
    geometry: Optional[dict] = None


class RestrictedZoneAlert(BaseModel):
    alert_id: int
    drone_id: int
    zone_id: int
    zone_name: str
    zone_type: str
    severity: str
    message: str
    latitude: float
    longitude: float
    altitude: float
    timestamp: str


class RestrictedZoneWebSocketMessage(BaseModel):
    type: str  # "restricted_zone_alert", "restricted_zones_info", "heartbeat"
    data: Optional[Union[List[RestrictedZoneAlert], List[RestrictedZoneInfo]]] = None
    timestamp: Optional[str] = None
