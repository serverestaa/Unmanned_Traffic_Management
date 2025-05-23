# app/monitoring/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


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
    resolved_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    drone = relationship("Drone")
    flight_request = relationship("FlightRequest")
    resolver = relationship("User", foreign_keys=[resolved_by])