# app/monitoring/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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
    resolved_by: Optional[int] = None
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