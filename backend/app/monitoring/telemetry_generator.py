#!/usr/bin/env python3
"""
Drone Telemetry Test Generator for UTM System
Generates realistic drone telemetry data for testing the monitoring system
"""

import asyncio
import aiohttp
import random
import math
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DroneStatus(Enum):
    AIRBORNE = "airborne"
    HOVERING = "hovering"
    LANDING = "landing"
    LANDED = "landed"
    EMERGENCY = "emergency"


@dataclass
class SimulatedDrone:
    """Represents a simulated drone with flight characteristics"""
    drone_id: int
    flight_request_id: int
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    cruise_altitude: float
    cruise_speed: float  # m/s
    battery_drain_rate: float  # % per minute
    current_lat: float
    current_lng: float
    current_altitude: float
    current_speed: float
    current_heading: float
    current_battery: float
    status: DroneStatus
    start_time: datetime
    waypoints: List[Tuple[float, float, float]]  # lat, lng, alt
    current_waypoint_index: int = 0


class TelemetryGenerator:
    def __init__(self, base_url: str = "http://127.0.0.1:8010/", auth_token: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ4MTY4NTkwfQ.KHdYpq8WMMK05yY7D134Z_GkL-WE0-dbcFdr5V9LOV4'):
        self.base_url = 'http://127.0.0.1:8010'
        self.auth_token = auth_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.drones: Dict[int, SimulatedDrone] = {}
        self.running = False

        # Kazakhstan bounds (approximate)
        self.bounds = {
            "min_lat": 51.066347,
            "max_lat": 51.068808,
            "min_lng": 71.427624,
            "max_lng": 71.456996
        }

        # Test scenarios
        self.scenarios = {
            "normal_flight": self.generate_normal_flight,
            "restricted_zone_violation": self.generate_restricted_zone_violation,
            "low_battery": self.generate_low_battery_scenario,
            "emergency_landing": self.generate_emergency_landing,
            "hover_test": self.generate_hover_test,
            "multi_drone_swarm": self.generate_swarm_scenario
        }

    async def __aenter__(self):
        """Async context manager entry"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing between two points in degrees"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)

        dlon = lon2_rad - lon1_rad

        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    def generate_waypoints(self, start: Tuple[float, float], end: Tuple[float, float],
                           num_waypoints: int = 5, altitude: float = 100.0) -> List[Tuple[float, float, float]]:
        """Generate waypoints between start and end points"""
        waypoints = []

        # Add takeoff point
        waypoints.append((start[0], start[1], 0))

        # Generate intermediate waypoints with some randomness
        for i in range(1, num_waypoints + 1):
            progress = i / (num_waypoints + 1)

            # Linear interpolation with some random offset
            lat = start[0] + (end[0] - start[0]) * progress + random.uniform(-0.001, 0.001)
            lng = start[1] + (end[1] - start[1]) * progress + random.uniform(-0.001, 0.001)

            # Vary altitude slightly
            alt = altitude + random.uniform(-10, 10)

            waypoints.append((lat, lng, alt))

        # Add landing point
        waypoints.append((end[0], end[1], 0))

        return waypoints

    async def send_telemetry(self, drone: SimulatedDrone) -> bool:
        """Send telemetry data to the server"""
        telemetry_data = {
            "drone_id": drone.drone_id,
            "flight_request_id": drone.flight_request_id,
            "latitude": drone.current_lat,
            "longitude": drone.current_lng,
            "altitude": drone.current_altitude,
            "speed": drone.current_speed,
            "heading": drone.current_heading,
            "battery_level": drone.current_battery,
            "status": drone.status.value
        }

        print(telemetry_data)
        try:
            print(f"Sending telemetry data to server - {self.base_url}/monitoring/telemetry/process")
            async with self.session.post(
                    f"{self.base_url}/monitoring/telemetry/process",
                    json=telemetry_data
            ) as response:
                if response.status == 200:
                    return True
                else:
                    print(f"Failed to send telemetry for drone {drone.drone_id}: {response.status}")
                    return False
        except Exception as e:
            print(f"Error sending telemetry: {e}")
            return False

    def update_drone_position(self, drone: SimulatedDrone, dt: float):
        """Update drone position based on current state"""
        if drone.status == DroneStatus.LANDED:
            return

        # Update battery
        drone.current_battery -= drone.battery_drain_rate * (dt / 60)
        if drone.current_battery <= 0:
            drone.current_battery = 0
            drone.status = DroneStatus.EMERGENCY
            drone.current_altitude = max(0, drone.current_altitude - 5 * dt)
            return

        # Check if we've reached current waypoint
        if drone.current_waypoint_index < len(drone.waypoints):
            target_lat, target_lng, target_alt = drone.waypoints[drone.current_waypoint_index]

            distance_to_target = self.calculate_distance(
                drone.current_lat, drone.current_lng,
                target_lat, target_lng
            )

            if distance_to_target < 10:  # Within 10 meters
                drone.current_waypoint_index += 1
                if drone.current_waypoint_index >= len(drone.waypoints):
                    drone.status = DroneStatus.LANDING
                    return

            # Move towards target
            drone.current_heading = self.calculate_bearing(
                drone.current_lat, drone.current_lng,
                target_lat, target_lng
            )

            # Calculate movement
            distance_to_move = min(drone.current_speed * dt, distance_to_target)

            # Update position
            lat_change = (distance_to_move / 111000) * math.cos(math.radians(drone.current_heading))
            lng_change = (distance_to_move / (111000 * math.cos(math.radians(drone.current_lat)))) * math.sin(
                math.radians(drone.current_heading))

            drone.current_lat += lat_change
            drone.current_lng += lng_change

            # Update altitude
            altitude_diff = target_alt - drone.current_altitude
            altitude_change = min(abs(altitude_diff), 2 * dt) * (1 if altitude_diff > 0 else -1)
            drone.current_altitude += altitude_change

            # Update speed (gradual acceleration/deceleration)
            if distance_to_target < 100:  # Slow down near waypoint
                drone.current_speed = max(2, drone.current_speed - dt)
            else:
                drone.current_speed = min(drone.cruise_speed, drone.current_speed + dt)

        # Handle landing
        if drone.status == DroneStatus.LANDING:
            drone.current_altitude = max(0, drone.current_altitude - 2 * dt)
            drone.current_speed = max(0, drone.current_speed - dt)

            if drone.current_altitude <= 0:
                drone.current_altitude = 0
                drone.current_speed = 0
                drone.status = DroneStatus.LANDED

    async def generate_normal_flight(self, drone_id: int, flight_request_id: int):
        """Generate a normal flight scenario"""
        # Random start and end points within bounds
        start_lat = random.uniform(self.bounds["min_lat"], self.bounds["max_lat"])
        start_lng = random.uniform(self.bounds["min_lng"], self.bounds["max_lng"])

        # End point 5-20 km away
        distance = random.uniform(5000, 20000)
        angle = random.uniform(0, 2 * math.pi)

        end_lat = start_lat + (distance / 111000) * math.cos(angle)
        end_lng = start_lng + (distance / (111000 * math.cos(math.radians(start_lat)))) * math.sin(angle)

        # Clamp to bounds
        end_lat = max(self.bounds["min_lat"], min(self.bounds["max_lat"], end_lat))
        end_lng = max(self.bounds["min_lng"], min(self.bounds["max_lng"], end_lng))

        waypoints = self.generate_waypoints(
            (start_lat, start_lng),
            (end_lat, end_lng),
            num_waypoints=random.randint(3, 8),
            altitude=random.uniform(50, 120)
        )

        drone = SimulatedDrone(
            drone_id=drone_id,
            flight_request_id=flight_request_id,
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=end_lat,
            end_lng=end_lng,
            cruise_altitude=random.uniform(50, 120),
            cruise_speed=random.uniform(10, 20),
            battery_drain_rate=random.uniform(0.5, 1.5),
            current_lat=start_lat,
            current_lng=start_lng,
            current_altitude=0,
            current_speed=0,
            current_heading=0,
            current_battery=random.uniform(80, 100),
            status=DroneStatus.AIRBORNE,
            start_time=datetime.utcnow(),
            waypoints=waypoints
        )

        self.drones[drone_id] = drone

        # Simulate flight
        last_telemetry = datetime.utcnow()
        while drone.status != DroneStatus.LANDED and self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()

            self.update_drone_position(drone, dt)

            # Send telemetry every 1-2 seconds
            if dt >= random.uniform(1, 2):
                await self.send_telemetry(drone)
                last_telemetry = current_time

            await asyncio.sleep(0.1)

        # Send final telemetry
        await self.send_telemetry(drone)
        del self.drones[drone_id]

    async def generate_restricted_zone_violation(self, drone_id: int, flight_request_id: int):
        """Generate a scenario where drone enters restricted zone"""
        # This assumes you have a restricted zone at a known location
        # Adjust these coordinates to match your test restricted zones
        restricted_zone_center = (43.238949, 76.889709)  # Almaty
        restricted_zone_radius = 5000  # 5km

        # Start outside the zone
        angle = random.uniform(0, 2 * math.pi)
        start_distance = restricted_zone_radius + random.uniform(2000, 5000)

        start_lat = restricted_zone_center[0] + (start_distance / 111000) * math.cos(angle)
        start_lng = restricted_zone_center[1] + (
                    start_distance / (111000 * math.cos(math.radians(restricted_zone_center[0])))) * math.sin(angle)

        # End point on opposite side, going through the zone
        end_lat = restricted_zone_center[0] - (start_distance / 111000) * math.cos(angle)
        end_lng = restricted_zone_center[1] - (
                    start_distance / (111000 * math.cos(math.radians(restricted_zone_center[0])))) * math.sin(angle)

        # Generate waypoints that go through the restricted zone
        waypoints = [
            (start_lat, start_lng, 0),
            (start_lat, start_lng, 150),  # High altitude violation
            (restricted_zone_center[0], restricted_zone_center[1], 150),  # Center of zone
            (end_lat, end_lng, 50),
            (end_lat, end_lng, 0)
        ]

        drone = SimulatedDrone(
            drone_id=drone_id,
            flight_request_id=flight_request_id,
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=end_lat,
            end_lng=end_lng,
            cruise_altitude=150,
            cruise_speed=15,
            battery_drain_rate=1.0,
            current_lat=start_lat,
            current_lng=start_lng,
            current_altitude=0,
            current_speed=0,
            current_heading=0,
            current_battery=90,
            status=DroneStatus.AIRBORNE,
            start_time=datetime.utcnow(),
            waypoints=waypoints
        )

        self.drones[drone_id] = drone

        # Simulate flight
        last_telemetry = datetime.utcnow()
        while drone.status != DroneStatus.LANDED and self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()

            self.update_drone_position(drone, dt)

            if dt >= 1:
                await self.send_telemetry(drone)
                last_telemetry = current_time

            await asyncio.sleep(0.1)

        await self.send_telemetry(drone)
        del self.drones[drone_id]

    async def generate_low_battery_scenario(self, drone_id: int, flight_request_id: int):
        """Generate a low battery scenario"""
        # Start with low battery
        start_lat = random.uniform(self.bounds["min_lat"], self.bounds["max_lat"])
        start_lng = random.uniform(self.bounds["min_lng"], self.bounds["max_lng"])

        # Short flight due to low battery
        end_lat = start_lat + random.uniform(-0.01, 0.01)
        end_lng = start_lng + random.uniform(-0.01, 0.01)

        waypoints = self.generate_waypoints(
            (start_lat, start_lng),
            (end_lat, end_lng),
            num_waypoints=2,
            altitude=50
        )

        drone = SimulatedDrone(
            drone_id=drone_id,
            flight_request_id=flight_request_id,
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=end_lat,
            end_lng=end_lng,
            cruise_altitude=50,
            cruise_speed=10,
            battery_drain_rate=3.0,  # Fast drain
            current_lat=start_lat,
            current_lng=start_lng,
            current_altitude=0,
            current_speed=0,
            current_heading=0,
            current_battery=25,  # Start with low battery
            status=DroneStatus.AIRBORNE,
            start_time=datetime.utcnow(),
            waypoints=waypoints
        )

        self.drones[drone_id] = drone

        # Simulate flight
        last_telemetry = datetime.utcnow()
        while drone.status != DroneStatus.LANDED and self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()

            self.update_drone_position(drone, dt)

            # Emergency landing if battery critically low
            if drone.current_battery < 10 and drone.status != DroneStatus.EMERGENCY:
                drone.status = DroneStatus.EMERGENCY
                print(f"Drone {drone_id} entering emergency landing due to low battery!")

            if dt >= 1:
                await self.send_telemetry(drone)
                last_telemetry = current_time

            await asyncio.sleep(0.1)

        await self.send_telemetry(drone)
        del self.drones[drone_id]

    async def generate_emergency_landing(self, drone_id: int, flight_request_id: int):
        """Generate an emergency landing scenario"""
        start_lat = random.uniform(self.bounds["min_lat"], self.bounds["max_lat"])
        start_lng = random.uniform(self.bounds["min_lng"], self.bounds["max_lng"])

        waypoints = [(start_lat, start_lng, 0), (start_lat, start_lng, 100)]

        drone = SimulatedDrone(
            drone_id=drone_id,
            flight_request_id=flight_request_id,
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=start_lat,
            end_lng=start_lng,
            cruise_altitude=100,
            cruise_speed=15,
            battery_drain_rate=1.0,
            current_lat=start_lat,
            current_lng=start_lng,
            current_altitude=0,
            current_speed=0,
            current_heading=0,
            current_battery=80,
            status=DroneStatus.AIRBORNE,
            start_time=datetime.utcnow(),
            waypoints=waypoints
        )

        self.drones[drone_id] = drone

        # Simulate flight for 30 seconds then emergency
        flight_duration = 30
        start_time = datetime.utcnow()
        last_telemetry = start_time

        while self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()
            elapsed = (current_time - start_time).total_seconds()

            if elapsed > flight_duration and drone.status != DroneStatus.EMERGENCY:
                drone.status = DroneStatus.EMERGENCY
                print(f"Drone {drone_id} declaring emergency!")

            self.update_drone_position(drone, dt)

            if dt >= 1:
                await self.send_telemetry(drone)
                last_telemetry = current_time

            if drone.status == DroneStatus.LANDED:
                break

            await asyncio.sleep(0.1)

        await self.send_telemetry(drone)
        del self.drones[drone_id]

    async def generate_hover_test(self, drone_id: int, flight_request_id: int):
        """Generate a hovering drone scenario"""
        hover_lat = random.uniform(self.bounds["min_lat"], self.bounds["max_lat"])
        hover_lng = random.uniform(self.bounds["min_lng"], self.bounds["max_lng"])
        hover_alt = random.uniform(50, 100)

        drone = SimulatedDrone(
            drone_id=drone_id,
            flight_request_id=flight_request_id,
            start_lat=hover_lat,
            start_lng=hover_lng,
            end_lat=hover_lat,
            end_lng=hover_lng,
            cruise_altitude=hover_alt,
            cruise_speed=0,
            battery_drain_rate=0.5,  # Lower drain while hovering
            current_lat=hover_lat,
            current_lng=hover_lng,
            current_altitude=hover_alt,
            current_speed=0,
            current_heading=0,
            current_battery=90,
            status=DroneStatus.HOVERING,
            start_time=datetime.utcnow(),
            waypoints=[]
        )

        self.drones[drone_id] = drone

        # Hover for 2 minutes
        hover_duration = 120
        start_time = datetime.utcnow()
        last_telemetry = start_time

        while self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()
            elapsed = (current_time - start_time).total_seconds()

            # Small position variations to simulate hover
            drone.current_lat += random.uniform(-0.00001, 0.00001)
            drone.current_lng += random.uniform(-0.00001, 0.00001)
            drone.current_altitude += random.uniform(-0.5, 0.5)

            # Update battery
            drone.current_battery -= drone.battery_drain_rate * (dt / 60)

            if dt >= 1:
                await self.send_telemetry(drone)
                last_telemetry = current_time

            if elapsed > hover_duration:
                break

            await asyncio.sleep(0.1)

        # Land
        drone.status = DroneStatus.LANDING
        while drone.current_altitude > 0 and self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()

            drone.current_altitude = max(0, drone.current_altitude - 2 * dt)
            if drone.current_altitude <= 0:
                drone.status = DroneStatus.LANDED

            if dt >= 1:
                await self.send_telemetry(drone)
                last_telemetry = current_time

            await asyncio.sleep(0.1)

        await self.send_telemetry(drone)
        del self.drones[drone_id]

    async def generate_swarm_scenario(self, base_drone_id: int, base_flight_id: int):
        """Generate multiple drones flying in formation"""
        num_drones = 5
        formation_spacing = 50  # meters

        # Leader drone path
        leader_start_lat = random.uniform(self.bounds["min_lat"], self.bounds["max_lat"])
        leader_start_lng = random.uniform(self.bounds["min_lng"], self.bounds["max_lng"])

        distance = 10000  # 10km flight
        angle = random.uniform(0, 2 * math.pi)

        leader_end_lat = leader_start_lat + (distance / 111000) * math.cos(angle)
        leader_end_lng = leader_start_lng + (distance / (111000 * math.cos(math.radians(leader_start_lat)))) * math.sin(
            angle)

        # Create swarm tasks
        tasks = []
        for i in range(num_drones):
            # Offset each drone slightly
            offset_angle = (2 * math.pi / num_drones) * i
            offset_distance = formation_spacing

            start_lat = leader_start_lat + (offset_distance / 111000) * math.cos(offset_angle)
            start_lng = leader_start_lng + (
                        offset_distance / (111000 * math.cos(math.radians(leader_start_lat)))) * math.sin(offset_angle)

            end_lat = leader_end_lat + (offset_distance / 111000) * math.cos(offset_angle)
            end_lng = leader_end_lng + (offset_distance / (111000 * math.cos(math.radians(leader_end_lat)))) * math.sin(
                offset_angle)

            drone_id = base_drone_id + i
            flight_id = base_flight_id + i

            # Create waypoints for this drone
            waypoints = self.generate_waypoints(
                (start_lat, start_lng),
                (end_lat, end_lng),
                num_waypoints=5,
                altitude=80 + i * 5  # Stagger altitudes
            )

            drone = SimulatedDrone(
                drone_id=drone_id,
                flight_request_id=flight_id,
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                cruise_altitude=80 + i * 5,
                cruise_speed=15,
                battery_drain_rate=1.0,
                current_lat=start_lat,
                current_lng=start_lng,
                current_altitude=0,
                current_speed=0,
                current_heading=0,
                current_battery=95,
                status=DroneStatus.AIRBORNE,
                start_time=datetime.utcnow(),
                waypoints=waypoints
            )

            self.drones[drone_id] = drone
            tasks.append(self.simulate_swarm_drone(drone))

        # Run all drones concurrently
        await asyncio.gather(*tasks)

    async def simulate_swarm_drone(self, drone: SimulatedDrone):
        """Simulate a single drone in the swarm"""
        last_telemetry = datetime.utcnow()

        while drone.status != DroneStatus.LANDED and self.running:
            current_time = datetime.utcnow()
            dt = (current_time - last_telemetry).total_seconds()

            self.update_drone_position(drone, dt)

            if dt >= random.uniform(0.8, 1.2):  # Slight variation in telemetry timing
                await self.send_telemetry(drone)
                last_telemetry = current_time

            await asyncio.sleep(0.1)

        await self.send_telemetry(drone)
        del self.drones[drone.drone_id]

    async def run_scenario(self, scenario: str, num_drones: int = 1, **kwargs):
        """Run a specific scenario"""
        if scenario not in self.scenarios:
            print(f"Unknown scenario: {scenario}")
            print(f"Available scenarios: {list(self.scenarios.keys())}")
            return

        print(f"Starting scenario: {scenario} with {num_drones} drone(s)")
        self.running = True

        tasks = []
        base_drone_id = kwargs.get('base_drone_id', 1)
        base_flight_id = kwargs.get('base_flight_id', 1)

        if scenario == "multi_drone_swarm":
            # Special handling for swarm scenario
            await self.scenarios[scenario](base_drone_id, base_flight_id)
        else:
            # Run multiple instances of the same scenario
            for i in range(num_drones):
                drone_id = base_drone_id + i
                flight_id = base_flight_id + i
                task = asyncio.create_task(
                    self.scenarios[scenario](drone_id, flight_id)
                )
                tasks.append(task)

                # Stagger drone starts
                await asyncio.sleep(random.uniform(1, 3))

            # Wait for all drones to complete
            await asyncio.gather(*tasks)

        print(f"Scenario {scenario} completed")

    async def run_continuous_test(self, duration_minutes: int = 60,
                                  drones_per_minute: int = 2):
        """Run continuous random scenarios for load testing"""
        print(f"Starting continuous test for {duration_minutes} minutes")
        print(f"Generating {drones_per_minute} drones per minute")

        self.running = True
        start_time = datetime.utcnow()
        drone_counter = 1
        flight_counter = 1

        active_tasks = []

        while self.running:
            current_time = datetime.utcnow()
            elapsed_minutes = (current_time - start_time).total_seconds() / 60

            if elapsed_minutes >= duration_minutes:
                break

            # Start new drones
            for _ in range(drones_per_minute):
                # Random scenario (excluding swarm for continuous test)
                scenario = random.choice([
                    "normal_flight",
                    "restricted_zone_violation",
                    "low_battery",
                    "emergency_landing",
                    "hover_test"
                ])

                task = asyncio.create_task(
                    self.scenarios[scenario](drone_counter, flight_counter)
                )
                active_tasks.append(task)

                drone_counter += 1
                flight_counter += 1

                # Small delay between drone starts
                await asyncio.sleep(60 / drones_per_minute / 2)

            # Clean up completed tasks
            active_tasks = [t for t in active_tasks if not t.done()]

            # Status update
            print(f"Time: {elapsed_minutes:.1f}/{duration_minutes} min, "
                  f"Active drones: {len(self.drones)}, "
                  f"Total launched: {drone_counter - 1}")

            await asyncio.sleep(30)  # Check every 30 seconds

        # Wait for remaining drones to complete
        print("Waiting for remaining drones to complete...")
        if active_tasks:
            await asyncio.gather(*active_tasks)

        print(f"Continuous test completed. Total drones: {drone_counter - 1}")

    def stop(self):
        """Stop all running simulations"""
        print("Stopping all simulations...")
        self.running = False


async def main():
    """Main function to run the telemetry generator"""
    import argparse

    parser = argparse.ArgumentParser(description="Drone Telemetry Test Generator")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="Base URL of the UTM API")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--scenario", choices=[
        "normal_flight", "restricted_zone_violation", "low_battery",
        "emergency_landing", "hover_test", "multi_drone_swarm", "continuous"
    ], default="normal_flight", help="Scenario to run")
    parser.add_argument("--num-drones", type=int, default=1,
                        help="Number of drones to simulate")
    parser.add_argument("--duration", type=int, default=60,
                        help="Duration in minutes (for continuous test)")
    parser.add_argument("--rate", type=int, default=2,
                        help="Drones per minute (for continuous test)")
    parser.add_argument("--drone-id-start", type=int, default=1,
                        help="Starting drone ID")
    parser.add_argument("--flight-id-start", type=int, default=1,
                        help="Starting flight request ID")

    args = parser.parse_args()

    # Create generator
    async with TelemetryGenerator(args.url, args.token) as generator:
        try:
            if args.scenario == "continuous":
                await generator.run_continuous_test(
                    duration_minutes=args.duration,
                    drones_per_minute=args.rate
                )
            else:
                await generator.run_scenario(
                    args.scenario,
                    num_drones=args.num_drones,
                    base_drone_id=args.drone_id_start,
                    base_flight_id=args.flight_id_start
                )
        except KeyboardInterrupt:
            generator.stop()
            print("\nSimulation interrupted by user")
        except Exception as e:
            print(f"Error during simulation: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())