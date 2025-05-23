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


class TelemetryGenerator:
    def __init__(self):
        self.active_flights: Dict[int, dict] = {}  # flight_request_id -> flight_data
        self.is_running = False

    async def start(self):
        """Start the telemetry generation loop"""
        self.is_running = True
        while self.is_running:
            await self.update_active_flights()
            await self.generate_telemetry()
            await asyncio.sleep(1)  # Update every second

    def stop(self):
        """Stop the telemetry generation"""
        self.is_running = False

    async def update_active_flights(self):
        """Update the list of active flights"""
        async with AsyncSessionLocal() as db:
            # Get approved flights that should be active now
            now = datetime.utcnow()
            result = await db.execute(
                select(FlightRequest).filter(
                    and_(
                        FlightRequest.status == "approved",
                        FlightRequest.planned_start_time <= now,
                        FlightRequest.planned_end_time >= now
                    )
                )
            )
            active_requests = result.scalars().all()

            # Initialize new flights
            for request in active_requests:
                if request.id not in self.active_flights:
                    # Get waypoints for this flight
                    waypoints_result = await db.execute(
                        select(Waypoint)
                        .filter(Waypoint.flight_request_id == request.id)
                        .order_by(Waypoint.sequence)
                    )
                    waypoints = waypoints_result.scalars().all()

                    if waypoints:
                        self.active_flights[request.id] = {
                            "flight_request": request,
                            "waypoints": waypoints,
                            "current_waypoint": 0,
                            "progress": 0.0,  # Progress to next waypoint (0-1)
                            "current_position": {
                                "latitude": waypoints[0].latitude,
                                "longitude": waypoints[0].longitude,
                                "altitude": waypoints[0].altitude
                            },
                            "speed": random.uniform(5, 12),  # m/s
                            "heading": 0,
                            "battery_level": 100.0,
                            "status": "airborne"
                        }

            # Remove completed flights
            completed_flights = []
            for flight_id, flight_data in self.active_flights.items():
                if flight_data["flight_request"].planned_end_time < now:
                    completed_flights.append(flight_id)

            for flight_id in completed_flights:
                # Update flight request status to completed
                result = await db.execute(
                    select(FlightRequest).filter(FlightRequest.id == flight_id)
                )
                request = result.scalar_one_or_none()
                if request:
                    request.status = "completed"
                    await db.commit()

                del self.active_flights[flight_id]

    async def generate_telemetry(self):
        """Generate telemetry data for all active flights"""
        if not self.active_flights:
            return

        async with AsyncSessionLocal() as db:
            for flight_id, flight_data in self.active_flights.items():
                try:
                    # Update drone position
                    self._update_drone_position(flight_data)

                    # Create telemetry record
                    telemetry = TelemetryData(
                        drone_id=flight_data["flight_request"].drone_id,
                        flight_request_id=flight_id,
                        latitude=flight_data["current_position"]["latitude"],
                        longitude=flight_data["current_position"]["longitude"],
                        altitude=flight_data["current_position"]["altitude"],
                        speed=flight_data["speed"],
                        heading=flight_data["heading"],
                        battery_level=flight_data["battery_level"],
                        status=flight_data["status"]
                    )
                    db.add(telemetry)

                    # Check for violations and generate alerts
                    await self._check_violations(db, flight_data, telemetry)

                    # Decrease battery
                    flight_data["battery_level"] -= random.uniform(0.1, 0.3)
                    if flight_data["battery_level"] < 0:
                        flight_data["battery_level"] = 0

                    # Check for low battery alert
                    if flight_data["battery_level"] < 20 and flight_data["battery_level"] > 19:
                        await self._create_alert(
                            db, telemetry, "low_battery", "medium",
                            f"Low battery warning: {flight_data['battery_level']:.1f}%"
                        )

                except Exception as e:
                    print(f"Error generating telemetry for flight {flight_id}: {e}")

            await db.commit()

    def _update_drone_position(self, flight_data: dict):
        """Update drone position along the flight path"""
        waypoints = flight_data["waypoints"]
        current_wp_idx = flight_data["current_waypoint"]

        if current_wp_idx >= len(waypoints) - 1:
            return  # Reached final waypoint

        current_wp = waypoints[current_wp_idx]
        next_wp = waypoints[current_wp_idx + 1]

        # Calculate distance to next waypoint
        distance = calculate_distance(
            current_wp.latitude, current_wp.longitude,
            next_wp.latitude, next_wp.longitude
        )

        # Calculate how much distance to cover this update (speed in m/s)
        speed = flight_data["speed"]
        distance_step = speed * 1.0  # 1 second update interval

        # Update progress
        if distance > 0:
            progress_step = distance_step / distance
            flight_data["progress"] += progress_step

            if flight_data["progress"] >= 1.0:
                # Reached next waypoint
                flight_data["current_waypoint"] += 1
                flight_data["progress"] = 0.0
                flight_data["current_position"] = {
                    "latitude": next_wp.latitude,
                    "longitude": next_wp.longitude,
                    "altitude": next_wp.altitude
                }
            else:
                # Interpolate position
                progress = flight_data["progress"]
                flight_data["current_position"] = {
                    "latitude": current_wp.latitude + (next_wp.latitude - current_wp.latitude) * progress,
                    "longitude": current_wp.longitude + (next_wp.longitude - current_wp.longitude) * progress,
                    "altitude": current_wp.altitude + (next_wp.altitude - current_wp.altitude) * progress
                }

            # Calculate heading
            lat_diff = next_wp.latitude - current_wp.latitude
            lon_diff = next_wp.longitude - current_wp.longitude
            flight_data["heading"] = math.degrees(math.atan2(lon_diff, lat_diff)) % 360

    async def _check_violations(self, db: AsyncSession, flight_data: dict, telemetry: TelemetryData):
        """Check for geofence and altitude violations"""
        from ..flights.models import RestrictedZone

        # Get restricted zones
        result = await db.execute(
            select(RestrictedZone).filter(RestrictedZone.is_active == True)
        )
        restricted_zones = result.scalars().all()

        current_pos = flight_data["current_position"]

        for zone in restricted_zones:
            # Check if drone is in restricted zone
            if point_in_circle(
                    current_pos["latitude"], current_pos["longitude"],
                    zone.center_lat, zone.center_lng, zone.radius
            ):
                # Check altitude violation
                if current_pos["altitude"] > zone.max_altitude:
                    await self._create_alert(
                        db, telemetry, "altitude_violation", "high",
                        f"Altitude violation in {zone.name}: {current_pos['altitude']:.1f}m > {zone.max_altitude}m"
                    )

                # Check if unauthorized entry
                await self._create_alert(
                    db, telemetry, "geofence_violation", "high",
                    f"Unauthorized entry into restricted zone: {zone.name}"
                )

    async def _create_alert(self, db: AsyncSession, telemetry: TelemetryData,
                            alert_type: str, severity: str, message: str):
        """Create an alert"""
        # Check if similar alert already exists (to avoid spam)
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        result = await db.execute(
            select(Alert).filter(
                and_(
                    Alert.drone_id == telemetry.drone_id,
                    Alert.alert_type == alert_type,
                    Alert.created_at > recent_time,
                    Alert.is_resolved == False
                )
            )
        )
        existing_alert = result.scalar_one_or_none()

        if not existing_alert:
            alert = Alert(
                drone_id=telemetry.drone_id,
                flight_request_id=telemetry.flight_request_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                latitude=telemetry.latitude,
                longitude=telemetry.longitude,
                altitude=telemetry.altitude
            )
            db.add(alert)


# Global instance
telemetry_generator = TelemetryGenerator()