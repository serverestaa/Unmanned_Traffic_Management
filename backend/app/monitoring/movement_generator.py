# app/monitoring/movement_generator.py
import random
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..flights.models import FlightRequest, Waypoint
from ..drones.models import Drone
from ..utils.geospatial import calculate_distance
from .models import TelemetryData
from ..utils.logger import setup_logger

logger = setup_logger("utm.movement_generator")


@dataclass
class MapBoundary:
    """Defines the rectangular boundary of the map"""
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float
    min_alt: float = 0.0
    max_alt: float = 120.0  # Default max altitude in meters


@dataclass
class DronePosition:
    """Represents a drone's position in 3D space"""
    latitude: float
    longitude: float
    altitude: float
    timestamp: datetime
    
    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MovementHop:
    """Represents a single hop in the drone's path"""
    position: DronePosition
    distance_from_previous: float  # meters
    time_to_reach: float  # seconds


class DroneMovementGenerator:
    """Generates realistic drone movement patterns with random hops"""
    
    def __init__(self, map_boundary: MapBoundary):
        self.map_boundary = map_boundary
        self.active_movements: Dict[int, List[MovementHop]] = {}  # drone_id -> movement plan
        self.current_positions: Dict[int, DronePosition] = {}  # drone_id -> current position
        logger.info(f"DroneMovementGenerator initialized with boundary: {map_boundary}")
    
    def generate_random_hop(self, current_pos: DronePosition, max_distance: float) -> DronePosition:
        """Generate a random hop within map boundaries and distance constraints"""
        max_attempts = 50
        
        for _ in range(max_attempts):
            # Generate random angle (0-360 degrees)
            angle = random.uniform(0, 2 * math.pi)
            
            # Generate random distance (30-100% of max distance)
            distance = random.uniform(0.3 * max_distance, max_distance)
            
            # Calculate new position using haversine approximation
            # Convert distance to degrees (rough approximation)
            lat_change = (distance / 111000) * math.cos(angle)  # 111km per degree latitude
            lng_change = (distance / (111000 * math.cos(math.radians(current_pos.latitude)))) * math.sin(angle)
            
            new_lat = current_pos.latitude + lat_change
            new_lng = current_pos.longitude + lng_change
            
            # Generate random altitude change (-20 to +20 meters)
            alt_change = random.uniform(-20, 20)
            new_alt = current_pos.altitude + alt_change
            
            # Check boundaries
            if (self.map_boundary.min_lat <= new_lat <= self.map_boundary.max_lat and
                self.map_boundary.min_lng <= new_lng <= self.map_boundary.max_lng and
                self.map_boundary.min_alt <= new_alt <= self.map_boundary.max_alt):
                
                return DronePosition(
                    latitude=new_lat,
                    longitude=new_lng,
                    altitude=new_alt,
                    timestamp=datetime.utcnow()
                )
        
        # If no valid position found, return a position closer to center
        center_lat = (self.map_boundary.min_lat + self.map_boundary.max_lat) / 2
        center_lng = (self.map_boundary.min_lng + self.map_boundary.max_lng) / 2
        
        return DronePosition(
            latitude=current_pos.latitude + (center_lat - current_pos.latitude) * 0.1,
            longitude=current_pos.longitude + (center_lng - current_pos.longitude) * 0.1,
            altitude=random.uniform(30, 80),
            timestamp=datetime.utcnow()
        )
    
    def generate_movement_plan(
        self,
        drone_id: int,
        initial_position: Tuple[float, float, float],  # (lat, lng, alt)
        velocity: float,  # m/s
        num_hops: int
    ) -> List[MovementHop]:
        """Generate a complete movement plan with random hops"""
        
        # Initialize with starting position
        current_pos = DronePosition(
            latitude=initial_position[0],
            longitude=initial_position[1],
            altitude=initial_position[2],
            timestamp=datetime.utcnow()
        )
        
        movement_plan = []
        
        # Maximum distance per hop based on velocity and reasonable hop duration (30-120 seconds)
        max_hop_duration = 120  # seconds
        max_hop_distance = velocity * max_hop_duration
        
        for hop_num in range(num_hops):
            # Generate next hop position
            next_pos = self.generate_random_hop(current_pos, max_hop_distance)
            
            # Calculate distance and time
            distance = calculate_distance(
                current_pos.latitude, current_pos.longitude,
                next_pos.latitude, next_pos.longitude
            )
            
            # Add altitude difference to distance (3D distance)
            alt_diff = abs(next_pos.altitude - current_pos.altitude)
            distance_3d = math.sqrt(distance**2 + alt_diff**2)
            
            # Calculate time to reach based on velocity
            time_to_reach = distance_3d / velocity if velocity > 0 else 0
            
            # Update timestamp for next position
            next_pos.timestamp = current_pos.timestamp + timedelta(seconds=time_to_reach)
            
            # Create hop
            hop = MovementHop(
                position=next_pos,
                distance_from_previous=distance_3d,
                time_to_reach=time_to_reach
            )
            
            movement_plan.append(hop)
            current_pos = next_pos
            
            logger.debug(f"Generated hop {hop_num + 1} for drone {drone_id}: "
                        f"distance={distance_3d:.2f}m, time={time_to_reach:.2f}s")
        
        # Store the movement plan
        self.active_movements[drone_id] = movement_plan
        self.current_positions[drone_id] = DronePosition(
            latitude=initial_position[0],
            longitude=initial_position[1],
            altitude=initial_position[2],
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Generated movement plan for drone {drone_id} with {num_hops} hops")
        return movement_plan
    
    def get_current_position(self, drone_id: int) -> Optional[DronePosition]:
        """Get the current interpolated position of a drone"""
        
        if drone_id not in self.active_movements or drone_id not in self.current_positions:
            return None
        
        movement_plan = self.active_movements[drone_id]
        if not movement_plan:
            return self.current_positions[drone_id]
        
        current_time = datetime.utcnow()
        start_pos = self.current_positions[drone_id]
        
        # Find which hop we're currently in
        for i, hop in enumerate(movement_plan):
            if current_time < hop.position.timestamp:
                # We're in transit to this hop
                target_pos = hop.position
                
                # Calculate progress (0-1)
                total_time = (target_pos.timestamp - start_pos.timestamp).total_seconds()
                elapsed_time = (current_time - start_pos.timestamp).total_seconds()
                
                if total_time <= 0:
                    progress = 1.0
                else:
                    progress = min(1.0, elapsed_time / total_time)
                
                # Interpolate position
                interpolated_lat = start_pos.latitude + (target_pos.latitude - start_pos.latitude) * progress
                interpolated_lng = start_pos.longitude + (target_pos.longitude - start_pos.longitude) * progress
                interpolated_alt = start_pos.altitude + (target_pos.altitude - start_pos.altitude) * progress
                
                return DronePosition(
                    latitude=interpolated_lat,
                    longitude=interpolated_lng,
                    altitude=interpolated_alt,
                    timestamp=current_time
                )
            
            # Update start position for next iteration
            start_pos = hop.position
        
        # If we've completed all hops, return the final position
        return movement_plan[-1].position if movement_plan else start_pos
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing between two points in degrees (0-360)"""
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)
        
        # Calculate difference in longitude
        dlon = lon2_rad - lon1_rad
        
        # Calculate bearing
        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        
        # Convert to degrees and normalize to 0-360
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
    
    def get_telemetry_data(self, drone_id: int, flight_request_id: Optional[int] = None) -> Optional[Dict]:
        """Get current telemetry data for a drone"""
        
        current_pos = self.get_current_position(drone_id)
        if not current_pos:
            return None
        # Calculate speed and heading based on movement
        speed = 0.0
        heading = 0.0
        
        if drone_id in self.active_movements and self.active_movements[drone_id]:
            # Find current and next positions
            movement_plan = self.active_movements[drone_id]
            prev_pos = self.current_positions[drone_id]
            
            for hop in movement_plan:
                if current_pos.timestamp < hop.position.timestamp:
                    # Calculate speed (assuming constant velocity between hops)
                    time_diff = (hop.position.timestamp - prev_pos.timestamp).total_seconds()
                    if time_diff > 0:
                        distance = calculate_distance(
                            prev_pos.latitude, prev_pos.longitude,
                            hop.position.latitude, hop.position.longitude
                        )
                        speed = distance / time_diff
                    
                    # Calculate heading
                    heading = self.calculate_bearing(
                        prev_pos.latitude, prev_pos.longitude,
                        hop.position.latitude, hop.position.longitude
                    )
                    break
                prev_pos = hop.position
        
        # Simulate battery drain (simple linear model)
        start_time = self.current_positions[drone_id].timestamp
        flight_duration = (current_pos.timestamp - start_time).total_seconds()
        battery_drain_rate = 0.1  # % per minute
        battery_level = max(0, 100 - (flight_duration / 60) * battery_drain_rate)
        
        return {
            "drone_id": drone_id,
            "flight_request_id": flight_request_id,
            "latitude": current_pos.latitude,
            "longitude": current_pos.longitude,
            "altitude": current_pos.altitude,
            "speed": speed,
            "heading": heading,
            "battery_level": battery_level,
            "status": "airborne" if battery_level > 10 else "landing",
            "timestamp": current_pos.timestamp
        }
    
    async def start_telemetry_generation(self, drone_id: int, flight_request_id: Optional[int] = None):
        """Start generating telemetry data for a drone"""
        
        logger.info(f"Starting telemetry generation for drone {drone_id}")
        
        while drone_id in self.active_movements:
            try:
                telemetry_data = self.get_telemetry_data(drone_id, flight_request_id)
                
                if telemetry_data:
                    # Save to database
                    async with AsyncSessionLocal() as session:
                        telemetry = TelemetryData(
                            drone_id=telemetry_data["drone_id"],
                            flight_request_id=telemetry_data["flight_request_id"],
                            latitude=telemetry_data["latitude"],
                            longitude=telemetry_data["longitude"],
                            altitude=telemetry_data["altitude"],
                            speed=telemetry_data["speed"],
                            heading=telemetry_data["heading"],
                            battery_level=telemetry_data["battery_level"],
                            status=telemetry_data["status"]
                        )
                        session.add(telemetry)
                        await session.commit()
                    
                    # Check if movement is complete
                    current_pos = self.get_current_position(drone_id)
                    if self.active_movements[drone_id]:
                        last_hop = self.active_movements[drone_id][-1]
                        if current_pos.timestamp >= last_hop.position.timestamp:
                            logger.info(f"Drone {drone_id} completed movement plan")
                            break
                
                await asyncio.sleep(1)  # Generate telemetry every second
                
            except Exception as e:
                logger.error(f"Error generating telemetry for drone {drone_id}: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
        
        # Clean up
        if drone_id in self.active_movements:
            del self.active_movements[drone_id]
        if drone_id in self.current_positions:
            del self.current_positions[drone_id]
        
        logger.info(f"Stopped telemetry generation for drone {drone_id}")
    
    def stop_drone_movement(self, drone_id: int):
        """Stop movement generation for a specific drone"""
        
        if drone_id in self.active_movements:
            del self.active_movements[drone_id]
        if drone_id in self.current_positions:
            del self.current_positions[drone_id]
        
        logger.info(f"Stopped movement for drone {drone_id}")
