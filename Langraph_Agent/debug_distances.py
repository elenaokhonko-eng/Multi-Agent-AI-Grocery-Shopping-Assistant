#!/usr/bin/env python3
"""
Debug script to check store distances from Galle
"""
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.logistics_agent import haversine_distance
from data.store_locations import STORE_LOCATIONS
from utils.location_utils import parse_user_location

def debug_distances():
    """Debug store distances from Galle"""
    print("🧪 DEBUGGING STORE DISTANCES FROM GALLE")
    print("=" * 60)
    
    # Parse Galle location
    galle_location = parse_user_location("Galle, Sri Lanka")
    print(f"📍 User Location: {galle_location.city}")
    print(f"   Coordinates: {galle_location.latitude:.4f}, {galle_location.longitude:.4f}")
    print()
    
    # Calculate distances to all stores
    store_distances = []
    
    for store in STORE_LOCATIONS:
        distance = haversine_distance(
            galle_location.latitude, 
            galle_location.longitude,
            store.latitude, 
            store.longitude
        )
        
        store_distances.append({
            "store": store.name,
            "brand": store.brand,
            "city": store.city,
            "distance_km": round(distance, 2),
            "within_100km": distance <= 100.0,
            "within_50km": distance <= 50.0,
            "within_25km": distance <= 25.0
        })
    
    # Sort by distance
    store_distances.sort(key=lambda x: x['distance_km'])
    
    print("📊 STORE DISTANCES FROM GALLE:")
    print("-" * 60)
    for i, store_info in enumerate(store_distances[:10], 1):  # Show top 10 closest
        status = "✅" if store_info['within_25km'] else "⚠️" if store_info['within_50km'] else "❌"
        print(f"{i:2d}. {status} {store_info['store']} ({store_info['brand']})")
        print(f"      📍 {store_info['city']} - {store_info['distance_km']}km")
        print()
    
    # Summary
    within_25km = sum(1 for s in store_distances if s['within_25km'])
    within_50km = sum(1 for s in store_distances if s['within_50km'])
    within_100km = sum(1 for s in store_distances if s['within_100km'])
    
    print("📈 DISTANCE SUMMARY:")
    print(f"   Within 25km: {within_25km} stores")
    print(f"   Within 50km: {within_50km} stores")  
    print(f"   Within 100km: {within_100km} stores")
    print(f"   Total stores: {len(store_distances)}")
    
    # Test with a more restrictive threshold
    print("\n🔬 TESTING WITH 25KM THRESHOLD:")
    print("-" * 40)
    
    # Group stores by brand within 25km
    brands_within_25km = {}
    for store_info in store_distances:
        if store_info['within_25km']:
            brand = store_info['brand']
            if brand not in brands_within_25km:
                brands_within_25km[brand] = []
            brands_within_25km[brand].append(store_info)
    
    print("Available brands within 25km:")
    for brand, stores in brands_within_25km.items():
        print(f"  • {brand}: {len(stores)} stores")
        for store in stores:
            print(f"    - {store['store']} ({store['distance_km']}km)")
    
    return store_distances

if __name__ == "__main__":
    debug_distances()
