# app/drones/router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..auth.utils import get_current_active_user
from ..auth.models import User
from .models import Drone
from .schemas import DroneCreate, DroneUpdate, Drone as DroneSchema

router = APIRouter(prefix="/drones", tags=["Drones"])


@router.post("/", response_model=DroneSchema)
async def create_drone(
        drone: DroneCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Check if serial number already exists
    result = await db.execute(select(Drone).filter(Drone.serial_number == drone.serial_number))
    existing_drone = result.scalar_one_or_none()
    if existing_drone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Drone with this serial number already exists"
        )

    db_drone = Drone(
        **drone.dict(),
        owner_id=current_user.id
    )
    db.add(db_drone)
    await db.commit()
    await db.refresh(db_drone)
    return db_drone


@router.get("/", response_model=List[DroneSchema])
async def get_my_drones(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Drone).filter(Drone.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/all", response_model=List[DroneSchema])
async def get_all_drones(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # Only admins can see all drones
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    result = await db.execute(select(Drone))
    return result.scalars().all()


@router.get("/{drone_id}", response_model=DroneSchema)
async def get_drone(
        drone_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Drone).filter(Drone.id == drone_id))
    drone = result.scalar_one_or_none()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )

    # Check ownership or admin role
    if drone.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return drone


@router.put("/{drone_id}", response_model=DroneSchema)
async def update_drone(
        drone_id: int,
        drone_update: DroneUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Drone).filter(Drone.id == drone_id))
    drone = result.scalar_one_or_none()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )

    # Check ownership
    if drone.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Update drone
    update_data = drone_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drone, field, value)

    await db.commit()
    await db.refresh(drone)
    return drone


@router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drone(
        drone_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Drone).filter(Drone.id == drone_id))
    drone = result.scalar_one_or_none()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )

    # Check ownership
    if drone.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    await db.delete(drone)
    await db.commit()