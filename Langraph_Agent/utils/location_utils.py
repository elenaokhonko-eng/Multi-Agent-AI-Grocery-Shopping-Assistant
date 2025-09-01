"""
Location utilities for handling user addresses and coordinates
"""
import re
from typing import Optional, Dict, Any, Tuple

from dataclasses import dataclass
from agents.logistics_agent import UserLocation


# Sri Lankan major cities with approximate coordinates
MAJOR_CITIES = {
    "colombo": {"lat": 6.9271, "lon": 79.8612, "district": "Colombo", "province": "Western"},
    "kandy": {"lat": 7.2906, "lon": 80.6337, "district": "Kandy", "province": "Central"},
    "galle": {"lat": 6.0535, "lon": 80.2210, "district": "Galle", "province": "Southern"},
    "jaffna": {"lat": 9.6615, "lon": 80.0255, "district": "Jaffna", "province": "Northern"},
    "batticaloa": {"lat": 7.7302, "lon": 81.7001, "district": "Batticaloa", "province": "Eastern"},
    "anuradhapura": {"lat": 8.3114, "lon": 80.4037, "district": "Anuradhapura", "province": "North Central"},
    "kurunegala": {"lat": 7.4863, "lon": 80.3647, "district": "Kurunegala", "province": "North Western"},
    "ratnapura": {"lat": 6.6828, "lon": 80.4036, "district": "Ratnapura", "province": "Sabaragamuwa"},
    "badulla": {"lat": 6.9934, "lon": 81.0550, "district": "Badulla", "province": "Uva"},
    "trincomalee": {"lat": 8.5874, "lon": 81.2152, "district": "Trincomalee", "province": "Eastern"},
    "matara": {"lat": 5.9549, "lon": 80.5550, "district": "Matara", "province": "Southern"},
    "puttalam": {"lat": 8.0362, "lon": 79.8283, "district": "Puttalam", "province": "North Western"},
    "kalmunai": {"lat": 7.4078, "lon": 81.8344, "district": "Ampara", "province": "Eastern"},
    "vavuniya": {"lat": 8.7514, "lon": 80.4971, "district": "Vavuniya", "province": "Northern"},
    "kilinochchi": {"lat": 9.3850, "lon": 80.4037, "district": "Kilinochchi", "province": "Northern"},
    "mannar": {"lat": 8.9810, "lon": 79.9041, "district": "Mannar", "province": "Northern"},
    "hambantota": {"lat": 6.1241, "lon": 81.1185, "district": "Hambantota", "province": "Southern"},
    "negombo": {"lat": 7.2083, "lon": 79.8358, "district": "Gampaha", "province": "Western"},
    "gampaha": {"lat": 7.0916, "lon": 79.9999, "district": "Gampaha", "province": "Western"},
    "kalutara": {"lat": 6.5854, "lon": 79.9607, "district": "Kalutara", "province": "Western"},
    "panadura": {"lat": 6.7132, "lon": 79.9026, "district": "Kalutara", "province": "Western"},
    "moratuwa": {"lat": 6.7730, "lon": 79.8816, "district": "Colombo", "province": "Western"},
    "mount_lavinia": {"lat": 6.8344, "lon": 79.8633, "district": "Colombo", "province": "Western"},
    "dehiwala": {"lat": 6.8563, "lon": 79.8632, "district": "Colombo", "province": "Western"},
    "kotte": {"lat": 6.8905, "lon": 79.9015, "district": "Colombo", "province": "Western"},
    "maharagama": {"lat": 6.8480, "lon": 79.9267, "district": "Colombo", "province": "Western"}
}

# District to province mapping
DISTRICT_PROVINCE_MAP = {
    "Colombo": "Western", "Gampaha": "Western", "Kalutara": "Western",
    "Kandy": "Central", "Matale": "Central", "Nuwara Eliya": "Central",
    "Galle": "Southern", "Matara": "Southern", "Hambantota": "Southern",
    "Jaffna": "Northern", "Kilinochchi": "Northern", "Mannar": "Northern", "Vavuniya": "Northern",
    "Batticaloa": "Eastern", "Ampara": "Eastern", "Trincomalee": "Eastern",
    "Kurunegala": "North Western", "Puttalam": "North Western",
    "Anuradhapura": "North Central", "Polonnaruwa": "North Central",
    "Badulla": "Uva", "Monaragala": "Uva",
    "Ratnapura": "Sabaragamuwa", "Kegalle": "Sabaragamuwa"
}


def normalize_city_name(city_name: str) -> str:
    """Normalize city name for lookup"""
    return city_name.lower().strip().replace(" ", "_").replace("-", "_")


def parse_coordinates_from_text(text: str) -> Optional[Tuple[float, float]]:
    """
    Parse latitude and longitude from text input
    Supports formats like:
    - "6.9271, 79.8612"
    - "lat: 6.9271, lon: 79.8612"
    - "6.9271°N, 79.8612°E"
    """
    # Remove common prefixes and suffixes
    text = text.lower().replace("lat:", "").replace("lon:", "").replace("latitude:", "").replace("longitude:", "")
    text = text.replace("°n", "").replace("°e", "").replace("°", "").replace("n", "").replace("e", "")
    
    # Extract numbers (positive floats)
    numbers = re.findall(r'\d+\.?\d*', text)
    
    if len(numbers) >= 2:
        try:
            lat = float(numbers[0])
            lon = float(numbers[1])
            
            # Basic validation for Sri Lankan coordinates
            if 5.5 <= lat <= 10.0 and 79.0 <= lon <= 82.0:
                return lat, lon
        except ValueError:
            pass
    
    return None


def get_province_from_district(district: str) -> str:
    """Get province name from district"""
    return DISTRICT_PROVINCE_MAP.get(district, "Unknown")


def parse_user_location(address_input: str) -> Optional[UserLocation]:
    """
    Parse user location from various input formats:
    1. City name (e.g., "Colombo", "Kandy")
    2. Coordinates (e.g., "6.9271, 79.8612")
    3. Full address with city (e.g., "123 Main St, Colombo")
    4. District name (e.g., "Colombo District")
    
    Returns UserLocation object or None if parsing fails
    """
    if not address_input or not isinstance(address_input, str):
        return None
    
    address_input = address_input.strip()
    
    # Try to parse coordinates first
    coords = parse_coordinates_from_text(address_input)
    if coords:
        lat, lon = coords
        return UserLocation(
            latitude=lat,
            longitude=lon,
            address=address_input,
            city="Custom Location",
            district="Unknown",
            province="Unknown"
        )
    
    # Extract city from address
    city_found = None
    original_city = None
    
    # Check for exact city matches in the input
    for city_key, city_data in MAJOR_CITIES.items():
        city_variations = [
            city_key,
            city_key.replace("_", " "),
            city_key.replace("_", "-"),
            city_key.title().replace("_", " ")
        ]
        
        for variation in city_variations:
            if variation.lower() in address_input.lower():
                city_found = city_data
                original_city = variation.title().replace("_", " ")
                break
        
        if city_found:
            break
    
    if city_found:
        return UserLocation(
            latitude=city_found["lat"],
            longitude=city_found["lon"],
            address=address_input,
            city=original_city,
            district=city_found["district"],
            province=city_found["province"]
        )
    
    # If no city found, try to extract district
    for district, province in DISTRICT_PROVINCE_MAP.items():
        if district.lower() in address_input.lower():
            # Use the district's main city coordinates (approximation)
            district_city = district.lower().replace(" ", "_")
            if district_city in MAJOR_CITIES:
                city_data = MAJOR_CITIES[district_city]
                return UserLocation(
                    latitude=city_data["lat"],
                    longitude=city_data["lon"],
                    address=address_input,
                    city=district,
                    district=district,
                    province=province
                )
    
    return None


def validate_sri_lankan_coordinates(lat: float, lon: float) -> bool:
    """Validate if coordinates are within Sri Lankan boundaries"""
    return 5.5 <= lat <= 10.0 and 79.0 <= lon <= 82.0


def get_nearest_major_city(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Find the nearest major city to given coordinates"""
    if not validate_sri_lankan_coordinates(lat, lon):
        return None
    
    min_distance = float('inf')
    nearest_city = None
    
    for city_name, city_data in MAJOR_CITIES.items():
        # Simple distance calculation (not accurate but good for approximation)
        distance = ((lat - city_data["lat"]) ** 2 + (lon - city_data["lon"]) ** 2) ** 0.5
        
        if distance < min_distance:
            min_distance = distance
            nearest_city = {
                "name": city_name.replace("_", " ").title(),
                "distance_approx": distance,
                **city_data
            }
    
    return nearest_city


def create_user_location_interactive() -> Optional[UserLocation]:
    """
    Interactive function to help users input their location
    Useful for testing and development
    """
    print("\n=== Location Input Helper ===")
    print("Please provide your location in one of these formats:")
    print("1. City name (e.g., 'Colombo', 'Kandy')")
    print("2. Coordinates (e.g., '6.9271, 79.8612')")
    print("3. Full address (e.g., '123 Main St, Colombo')")
    
    while True:
        address_input = input("\nEnter your location: ").strip()
        
        if not address_input:
            print("Please enter a valid location.")
            continue
        
        location = parse_user_location(address_input)
        
        if location:
            print(f"\n✅ Location parsed successfully:")
            print(f"   Address: {location.address}")
            print(f"   City: {location.city}")
            print(f"   District: {location.district}")
            print(f"   Province: {location.province}")
            print(f"   Coordinates: {location.latitude:.4f}, {location.longitude:.4f}")
            
            confirm = input("\nIs this correct? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                return location
            else:
                print("Let's try again...")
                continue
        else:
            print("❌ Could not parse location. Please try again with a different format.")
            print("Available cities:", ", ".join([city.replace("_", " ").title() for city in list(MAJOR_CITIES.keys())[:10]]))


# Example usage and testing
if __name__ == "__main__":
    # Test parsing
    test_inputs = [
        "Colombo",
        "6.9271, 79.8612",
        "123 Main Street, Kandy",
        "Galle District",
        "Mount Lavinia",
        "lat: 7.2906, lon: 80.6337"
    ]
    
    print("Testing location parsing:")
    for test_input in test_inputs:
        location = parse_user_location(test_input)
        if location:
            print(f"✅ '{test_input}' -> {location.city} ({location.latitude:.4f}, {location.longitude:.4f})")
        else:
            print(f"❌ '{test_input}' -> Could not parse")
