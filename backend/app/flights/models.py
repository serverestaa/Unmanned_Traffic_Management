# app/flights/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography, Geometry
from ..database import Base


class RestrictedZone(Base):
    __tablename__ = "restricted_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius = Column(Float, nullable=False)  # meters
    max_altitude = Column(Float, default=0.0)  # max allowed altitude in zone
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FlightRequest(Base):
    __tablename__ = "flight_requests"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    pilot_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Flight details
    planned_start_time = Column(DateTime(timezone=True), nullable=False)
    planned_end_time = Column(DateTime(timezone=True), nullable=False)
    max_altitude = Column(Float, nullable=False)
    purpose = Column(String)

    # Route as LineString geometry (waypoints)
    route = Column(Geography('LINESTRING', srid=4326))

    # Status
    status = Column(String, default="pending")  # pending, approved, rejected, active, completed
    approval_notes = Column(Text)
    approved_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))

    # Relationships
    drone = relationship("Drone", back_populates="flight_requests")
    pilot = relationship("User", back_populates="flight_requests", foreign_keys=[pilot_id])
    approver = relationship("User", back_populates="approved_flights", foreign_keys=[approved_by])


class Waypoint(Base):
    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True)
    flight_request_id = Column(Integer, ForeignKey("flight_requests.id"), nullable=False)
    sequence = Column(Integer, nullable=False)  # Order in the route
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)

    # Relationships
    flight_request = relationship("FlightRequest")