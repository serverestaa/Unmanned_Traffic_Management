# app/monitoring/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from ..database import Base
from ..drones.models import Drone
from ..auth.models import User
from ..flights.models import FlightRequest


class HexGridCell(Base):
    __tablename__ = "hex_grid_cells"

    id = Column(Integer, primary_key=True, index=True)
    h3_index = Column(String, unique=True, index=True, nullable=False)  # H3 index at resolution 8
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    geometry = Column(Geometry('POLYGON', srid=4326, spatial_index=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    drones_count = Column(Integer, default=0)  # Track number of drones in this hex
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # Track when drones were last updated

    # Relationships
    current_positions = relationship("CurrentDronePosition", back_populates="hex_cell", cascade="all, delete-orphan")

    __table_args__ = (
        # Add GiST index for faster spatial queries
        Index('idx_hex_grid_cell_geometry', 'geometry', postgresql_using='gist'),
    )


class CurrentDronePosition(Base):
    __tablename__ = "current_drone_positions"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    flight_request_id = Column(Integer, ForeignKey("flight_requests.id"))
    hex_cell_id = Column(Integer, ForeignKey("hex_grid_cells.id"), nullable=False, index=True)
    
    # Position data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    
    # Flight data
    speed = Column(Float, default=0.0)  # m/s
    heading = Column(Float, default=0.0)  # degrees
    battery_level = Column(Float, default=100.0)  # percentage
    
    # Status
    status = Column(String, default="airborne")  # airborne, landed, emergency
    
    # Timestamp
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    hex_cell = relationship("HexGridCell", back_populates="current_positions")
    drone = relationship("Drone")
    flight_request = relationship("FlightRequest")

    __table_args__ = (
        # Add composite index for common query patterns
        Index('idx_current_pos_hex_cell_status', 'hex_cell_id', 'status'),
    )


class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    flight_request_id = Column(Integer, ForeignKey("flight_requests.id"))

    # Position data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)

    # Flight data
    speed = Column(Float, default=0.0)  # m/s
    heading = Column(Float, default=0.0)  # degrees
    battery_level = Column(Float, default=100.0)  # percentage

    # Status
    status = Column(String, default="airborne")  # airborne, landed, emergency

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    drone = relationship("Drone", back_populates="telemetry")
    flight_request = relationship("FlightRequest")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    flight_request_id = Column(Integer, ForeignKey("flight_requests.id"))

    # Alert details
    alert_type = Column(String, nullable=False)  # geofence_violation, altitude_violation, emergency, low_battery
    severity = Column(String, default="medium")  # low, medium, high, critical
    message = Column(Text, nullable=False)

    # Location when alert occurred
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)

    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    drone = relationship("Drone")
    flight_request = relationship("FlightRequest")
    resolver = relationship("User", foreign_keys=[resolved_by])