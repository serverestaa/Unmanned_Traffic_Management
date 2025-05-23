# app/auth/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="pilot")  # pilot, admin, operator
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    drones = relationship("Drone", back_populates="owner")
    flight_requests = relationship("FlightRequest", back_populates="pilot", foreign_keys="[FlightRequest.pilot_id]")
    approved_flights = relationship("FlightRequest", back_populates="approver", foreign_keys="[FlightRequest.approved_by]")