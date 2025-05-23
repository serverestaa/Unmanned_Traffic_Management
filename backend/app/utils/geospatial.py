# app/utils/geospatial.py
import math
from typing import List, Tuple
from shapely.geometry import Point, LineString
from shapely.ops import transform
import pyproj
from ..utils.logger import setup_logger

logger = setup_logger("utm.geospatial")

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in meters
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        
    Returns:
        float: Distance in meters
        
    Raises:
        ValueError: If coordinates are invalid
    """
    # Validate coordinates
    if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
        raise ValueError("Latitude must be between -90 and 90 degrees")
    if not (-180 <= lon1 <= 180) or not (-180 <= lon2 <= 180):
        raise ValueError("Longitude must be between -180 and 180 degrees")
    
    # Create a geodesic calculator
    geod = pyproj.Geod(ellps='WGS84')
    
    # Calculate the distance
    distance = geod.inv(lon1, lat1, lon2, lat2)[2]  # Returns (forward_azimuth, back_azimuth, distance)
    
    logger.debug(f"Distance calculation: ({lat1}, {lon1}) to ({lat2}, {lon2}) = {distance:.2f}m")
    return distance


def point_in_circle(point_lat: float, point_lon: float,
                    center_lat: float, center_lon: float, radius: float) -> bool:
    """
    Check if a point is within a circular area
    
    Args:
        point_lat: Latitude of the point to check
        point_lon: Longitude of the point to check
        center_lat: Latitude of the circle center
        center_lon: Longitude of the circle center
        radius: Radius of the circle in meters
        
    Returns:
        bool: True if the point is within the circle, False otherwise
    """
    print(f"Point in circle check - Point: ({point_lat}, {point_lon}), Center: ({center_lat}, {center_lon}), Radius: {radius}m")
    distance = calculate_distance(point_lat, point_lon, center_lat, center_lon)
    logger.info(f"Point in circle check - Distance: {distance:.2f}m, Radius: {radius}m")

    return distance <= radius


def route_intersects_zone(waypoints: List[Tuple[float, float]],
                          center_lat: float, center_lon: float, radius: float) -> bool:
    """
    Check if a route (series of waypoints) intersects with a circular restricted zone
    
    Args:
        waypoints: List of (latitude, longitude) tuples
        center_lat: Latitude of the zone center
        center_lon: Longitude of the zone center
        radius: Radius of the zone in meters
        
    Returns:
        bool: True if the route intersects the zone, False otherwise
    """
    logger.debug(f"Checking route intersection with zone - Center: ({center_lat}, {center_lon}), Radius: {radius}m")
    
    # Check each waypoint
    for lat, lon in waypoints:
        if point_in_circle(lat, lon, center_lat, center_lon, radius):
            logger.debug(f"Waypoint ({lat}, {lon}) is inside the zone")
            return True

    # Check line segments between waypoints
    for i in range(len(waypoints) - 1):
        if line_intersects_circle(waypoints[i], waypoints[i + 1],
                                  center_lat, center_lon, radius):
            logger.debug(f"Line segment {i} intersects the zone")
            return True

    return False


def line_intersects_circle(p1: Tuple[float, float], p2: Tuple[float, float],
                           center_lat: float, center_lon: float, radius: float) -> bool:
    """
    Check if a line segment intersects with a circle using geodesic calculations
    
    Args:
        p1: First point (latitude, longitude)
        p2: Second point (latitude, longitude)
        center_lat: Latitude of the circle center
        center_lon: Longitude of the circle center
        radius: Radius of the circle in meters
        
    Returns:
        bool: True if the line segment intersects the circle, False otherwise
    """
    # Create a geodesic calculator
    geod = pyproj.Geod(ellps='WGS84')
    
    # Calculate the distance from center to line segment
    # First, calculate the distance from center to both endpoints
    dist1 = calculate_distance(p1[0], p1[1], center_lat, center_lon)
    dist2 = calculate_distance(p2[0], p2[1], center_lat, center_lon)
    
    # If either endpoint is within the circle, we have an intersection
    if dist1 <= radius or dist2 <= radius:
        return True
    
    # Calculate the azimuth and distance of the line segment
    az12, az21, dist = geod.inv(p1[1], p1[0], p2[1], p2[0])
    
    # Calculate the azimuth from center to both endpoints
    az1, _, _ = geod.inv(center_lon, center_lat, p1[1], p1[0])
    az2, _, _ = geod.inv(center_lon, center_lat, p2[1], p2[0])
    
    # Calculate the minimum distance from center to line segment
    # This is the perpendicular distance
    min_dist = min(dist1, dist2) * math.sin(math.radians(abs(az1 - az12)))
    
    return min_dist <= radius


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
    
    Args:
        waypoints: List of (latitude, longitude) tuples
        
    Returns:
        str: WKT LineString representation
        
    Raises:
        ValueError: If less than 2 waypoints are provided
    """
    if len(waypoints) < 2:
        raise ValueError("At least 2 waypoints required for a route")

    points = [f"{lon} {lat}" for lat, lon in waypoints]
    return f"LINESTRING({', '.join(points)})"