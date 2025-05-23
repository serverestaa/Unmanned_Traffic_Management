# app/drones/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Drone(Base):
    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    serial_number = Column(String, unique=True, nullable=False, index=True)
    max_altitude = Column(Float, default=120.0)  # meters
    max_speed = Column(Float, default=15.0)  # m/s
    weight = Column(Float)  # kg
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="drones")
    flight_requests = relationship("FlightRequest", back_populates="drone")
    telemetry = relationship("TelemetryData", back_populates="drone")