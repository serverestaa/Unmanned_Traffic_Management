# app/drones/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class DroneBase(BaseModel):
    brand: str
    model: str
    serial_number: str
    max_altitude: Optional[float] = 120.0
    max_speed: Optional[float] = 15.0
    weight: Optional[float] = None


class DroneCreate(DroneBase):
    pass


class DroneUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    max_altitude: Optional[float] = None
    max_speed: Optional[float] = None
    weight: Optional[float] = None
    is_active: Optional[bool] = None


class Drone(DroneBase):
    id: int
    is_active: bool
    owner_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DroneWithOwner(Drone):
    owner: dict  # Will contain basic user info