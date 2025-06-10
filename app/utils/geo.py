import math
from typing import Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r

def get_bounding_box(center_lat: float, center_lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box coordinates for a given center point and radius.
    
    Args:
        center_lat: Center latitude in decimal degrees
        center_lon: Center longitude in decimal degrees  
        radius_km: Radius in kilometers
    
    Returns:
        Tuple of (lat_min, lat_max, lon_min, lon_max)
    """
    # Approximate degrees per kilometer
    # 1 degree latitude ≈ 111 km
    lat_degree_km = 111.0
    
    # 1 degree longitude varies by latitude
    lon_degree_km = 111.0 * math.cos(math.radians(center_lat))
    
    lat_delta = radius_km / lat_degree_km
    lon_delta = radius_km / lon_degree_km
    
    return (
        center_lat - lat_delta,  # lat_min
        center_lat + lat_delta,  # lat_max
        center_lon - lon_delta,  # lon_min
        center_lon + lon_delta   # lon_max
    ) 