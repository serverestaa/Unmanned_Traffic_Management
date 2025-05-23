# app/monitoring/telemetry.py
import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database import AsyncSessionLocal
from ..flights.models import FlightRequest, Waypoint
from ..drones.models import Drone
from ..utils.geospatial import calculate_distance, point_in_circle
from .models import TelemetryData, Alert
from .schemas import TelemetryDataCreate, AlertCreate
from ..utils.logger import setup_logger

logger = setup_logger("utm.telemetry")

class TelemetryGenerator:
    def __init__(self):
        self.active_flights: Dict[int, dict] = {}  # flight_request_id -> flight_data
        self.is_running = False
        logger.info("TelemetryGenerator initialized")

    async def start(self):
        """Start the telemetry generation loop"""
        logger.info("Starting telemetry generation loop")
        self.is_running = True
        while self.is_running:
            try:
                await self.update_active_flights()
                await self.generate_telemetry()
                await asyncio.sleep(1)  # Update every second
            except Exception as e:
                logger.error(f"Error in telemetry generation loop: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Wait longer on error

    def stop(self):
        """Stop the telemetry generation"""
        logger.info("Stopping telemetry generation")
        self.is_running = False

    async def update_active_flights(self):
        """Update the list of active flights"""
        try:
            async with AsyncSessionLocal() as session:
                # Get all approved and active flight requests
                result = await session.execute(
                    select(FlightRequest).where(
                        and_(
                            FlightRequest.status.in_(["approved", "active"]),
                            FlightRequest.planned_end_time > datetime.utcnow()
                        )
                    )
                )
                flights = result.scalars().all()
                
                # Update active flights
                current_flight_ids = set(self.active_flights.keys())
                new_flight_ids = {flight.id for flight in flights}
                
                # Remove completed flights
                for flight_id in current_flight_ids - new_flight_ids:
                    logger.info(f"Flight {flight_id} completed or cancelled")
                    del self.active_flights[flight_id]
                
                # Add new flights
                for flight in flights:
                    if flight.id not in self.active_flights:
                        logger.info(f"New active flight detected: {flight.id}")
                        self.active_flights[flight.id] = {
                            "current_position": 0,  # Index in waypoints
                            "start_time": datetime.utcnow(),
                            "status": "active"
                        }
        except Exception as e:
            logger.error(f"Error updating active flights: {str(e)}", exc_info=True)

    async def generate_telemetry(self):
        """Generate telemetry data for active flights"""
        try:
            async with AsyncSessionLocal() as session:
                for flight_id, flight_data in self.active_flights.items():
                    try:
                        # Get flight request details
                        result = await session.execute(
                            select(FlightRequest).where(FlightRequest.id == flight_id)
                        )
                        flight = result.scalar_one_or_none()
                        
                        if not flight:
                            logger.warning(f"Flight {flight_id} not found, removing from active flights")
                            del self.active_flights[flight_id]
                            continue
                        
                        # Generate and save telemetry data
                        telemetry = await self._generate_flight_telemetry(flight, flight_data)
                        if telemetry:
                            session.add(telemetry)
                            await session.commit()
                            logger.debug(f"Generated telemetry for flight {flight_id}")
                    except Exception as e:
                        logger.error(f"Error generating telemetry for flight {flight_id}: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Error in generate_telemetry: {str(e)}", exc_info=True)

    async def _generate_flight_telemetry(self, flight: FlightRequest, flight_data: dict) -> Optional[TelemetryData]:
        """Generate telemetry data for a single flight"""
        try:
            # Calculate current position based on time
            elapsed_time = (datetime.utcnow() - flight_data["start_time"]).total_seconds()
            total_duration = (flight.planned_end_time - flight.planned_start_time).total_seconds()
            
            if elapsed_time >= total_duration:
                logger.info(f"Flight {flight.id} completed")
                flight_data["status"] = "completed"
                return None
            
            # Generate position data
            position = self._calculate_position(flight, elapsed_time, total_duration)
            
            return TelemetryData(
                drone_id=flight.drone_id,
                flight_request_id=flight.id,
                latitude=position["lat"],
                longitude=position["lng"],
                altitude=position["alt"],
                speed=position["speed"],
                heading=position["heading"],
                battery_level=position["battery"],
                status=flight_data["status"]
            )
        except Exception as e:
            logger.error(f"Error generating flight telemetry: {str(e)}", exc_info=True)
            return None

    def _calculate_position(self, flight: FlightRequest, elapsed_time: float, total_duration: float) -> dict:
        """Calculate current position and flight parameters"""
        try:
            # Simple linear interpolation for demo purposes
            progress = elapsed_time / total_duration
            
            # Calculate position
            lat = 40.7128 + (progress * 0.1)  # Example: moving north
            lng = -74.0060 + (progress * 0.1)  # Example: moving east
            alt = 50.0 + (math.sin(progress * math.pi) * 30.0)  # Example: altitude variation
            
            return {
                "lat": lat,
                "lng": lng,
                "alt": alt,
                "speed": 10.0,  # m/s
                "heading": 45.0,  # degrees
                "battery": 100.0 - (progress * 20.0)  # Example: linear battery drain
            }
        except Exception as e:
            logger.error(f"Error calculating position: {str(e)}", exc_info=True)
            raise

# Create global telemetry generator instance
telemetry_generator = TelemetryGenerator()