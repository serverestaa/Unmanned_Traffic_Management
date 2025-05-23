# app/utils/geospatial.py
import math
from typing import List, Tuple
from shapely.geometry import Point, LineString
from shapely.ops import transform
import pyproj


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in meters
    r = 6371000
    return c * r


def point_in_circle(point_lat: float, point_lon: float,
                    center_lat: float, center_lon: float, radius: float) -> bool:
    """
    Check if a point is within a circular area
    """
    distance = calculate_distance(point_lat, point_lon, center_lat, center_lon)
    return distance <= radius


def route_intersects_zone(waypoints: List[Tuple[float, float]],
                          center_lat: float, center_lon: float, radius: float) -> bool:
    """
    Check if a route (series of waypoints) intersects with a circular restricted zone
    """
    # Check each waypoint
    for lat, lon in waypoints:
        if point_in_circle(lat, lon, center_lat, center_lon, radius):
            return True

    # Check line segments between waypoints
    for i in range(len(waypoints) - 1):
        if line_intersects_circle(waypoints[i], waypoints[i + 1],
                                  center_lat, center_lon, radius):
            return True

    return False


def line_intersects_circle(p1: Tuple[float, float], p2: Tuple[float, float],
                           center_lat: float, center_lon: float, radius: float) -> bool:
    """
    Check if a line segment intersects with a circle
    Using approximate method for lat/lon coordinates
    """
    # Convert to approximate Cartesian coordinates (good enough for small distances)
    x1, y1 = lon_lat_to_meters(p1[1], p1[0], center_lon, center_lat)
    x2, y2 = lon_lat_to_meters(p2[1], p2[0], center_lon, center_lat)
    cx, cy = 0, 0  # Center is at origin in this coordinate system

    # Vector from p1 to p2
    dx = x2 - x1
    dy = y2 - y1

    # Vector from p1 to circle center
    fx = x1 - cx
    fy = y1 - cy

    # Quadratic equation coefficients
    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = (fx * fx + fy * fy) - radius * radius

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return False  # No intersection

    # Check if intersection points are within the line segment
    discriminant = math.sqrt(discriminant)
    t1 = (-b - discriminant) / (2 * a)
    t2 = (-b + discriminant) / (2 * a)

    return (0 <= t1 <= 1) or (0 <= t2 <= 1)


def lon_lat_to_meters(lon: float, lat: float, ref_lon: float, ref_lat: float) -> Tuple[float, float]:
    """
    Convert lon/lat to approximate meters relative to reference point
    """
    # Approximate conversion (good enough for small distances)
    lat_rad = math.radians(ref_lat)

    x = (lon - ref_lon) * 111320 * math.cos(lat_rad)
    y = (lat - ref_lat) * 110540

    return x, y


def create_linestring_from_waypoints(waypoints: List[Tuple[float, float]]) -> str:
    """
    Create a WKT LineString from waypoints
    """
    if len(waypoints) < 2:
        raise ValueError("At least 2 waypoints required for a route")

    points = [f"{lon} {lat}" for lat, lon in waypoints]
    return f"LINESTRING({', '.join(points)})"