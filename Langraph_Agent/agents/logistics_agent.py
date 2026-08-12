"""
Logistics Agent for optimizing delivery times, costs, and service availability
"""
import math
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from langchain.tools import tool
from langchain_ollama import ChatOllama

from core.config import Config
from data.store_locations import STORE_LOCATIONS, StoreLocation, get_store_by_id


@dataclass
class UserLocation:
    """User location for delivery calculations"""
    latitude: float
    longitude: float
    address: str
    city: str
    district: str
    province: str


@dataclass
class DeliveryOption:
    """Delivery option with cost and time estimates"""
    store: StoreLocation
    distance_km: float
    delivery_charge_lkr: float
    estimated_delivery_hours: float
    is_available: bool
    delivery_speed: str  # "fast", "standard", "slow"
    total_cost_with_delivery: float


@dataclass
class LogisticsOptimization:
    """Complete logistics optimization result"""
    user_location: UserLocation
    delivery_options: List[DeliveryOption]
    recommended_option: Optional[DeliveryOption]
    total_stores_checked: int
    optimization_time_seconds: float


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers
    using the Haversine formula
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371.0
    
    return c * r


def estimate_delivery_time(distance_km: float, base_hours: float, traffic_factor: float = 1.2) -> float:
    """
    Estimate delivery time based on distance and traffic conditions
    """
    # Base delivery time + distance factor + traffic factor
    time_hours = base_hours + (distance_km * 0.1) * traffic_factor
    return round(time_hours, 1)


def calculate_delivery_cost(base_charge: float, distance_km: float, distance_threshold: float = 10.0) -> float:
    """
    Calculate delivery cost with distance-based pricing
    """
    if distance_km <= distance_threshold:
        return base_charge
    else:
        # Add extra charge for longer distances
        extra_distance = distance_km - distance_threshold
        extra_charge = extra_distance * 15.0  # LKR 15 per extra km
        return base_charge + extra_charge


@tool
def calculate_distance_to_stores(user_location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate distances from user location to all available stores
    
    Args:
        user_location: Dictionary with latitude, longitude, and address info
        
    Returns:
        Dictionary with distance calculations for all stores
    """
    print(f"[TOOL] Calculating distances from user location: {user_location.get('city', 'Unknown')}")
    
    user_lat = user_location.get('latitude')
    user_lon = user_location.get('longitude')
    
    if not user_lat or not user_lon:
        return {"error": "User location coordinates required"}
    
    distances = []
    
    for store in STORE_LOCATIONS:
        distance = haversine_distance(user_lat, user_lon, store.latitude, store.longitude)
        
        distances.append({
            "store_id": store.store_id,
            "store_name": store.name,
            "brand": store.brand,
            "city": store.city,
            "distance_km": round(distance, 2),
            "within_delivery_radius": distance <= store.max_delivery_radius_km
        })
    
    # Sort by distance
    distances.sort(key=lambda x: x['distance_km'])
    
    print(f"[TOOL] Calculated distances to {len(distances)} stores")
    return {
        "user_location": user_location,
        "store_distances": distances,
        "nearest_store": distances[0] if distances else None
    }


@tool
def optimize_delivery_options(user_location: Dict[str, Any], product_prices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Optimize delivery options based on cost, time, and availability
    
    Args:
        user_location: User's location information
        product_prices: List of products with prices and store info
        
    Returns:
        Optimized delivery options with recommendations
    """
    print(f"[TOOL] Optimizing delivery for {len(product_prices)} products")
    
    user_lat = user_location.get('latitude')
    user_lon = user_location.get('longitude')
    
    if not user_lat or not user_lon:
        return {"error": "User location coordinates required"}
    
    # Group products by store/brand
    store_products = {}
    for product in product_prices:
        brand = product.get('collection', product.get('website', 'unknown'))
        if brand not in store_products:
            store_products[brand] = []
        store_products[brand].append(product)
    
    delivery_options = []
    
    for brand, products in store_products.items():
        # Find stores for this brand
        brand_stores = [s for s in STORE_LOCATIONS if s.brand == brand]
        
        if not brand_stores:
            continue
        
        # Calculate total product cost for this brand
        total_product_cost = sum(float(p.get('price', 0)) for p in products)
        
        for store in brand_stores:
            distance = haversine_distance(user_lat, user_lon, store.latitude, store.longitude)
            
            # Check if delivery is available
            is_available = distance <= store.max_delivery_radius_km
            
            if is_available:
                # Calculate delivery cost and time
                delivery_charge = calculate_delivery_cost(store.delivery_charge_lkr, distance)
                delivery_time = estimate_delivery_time(distance, store.average_delivery_hours)
                
                # Determine delivery speed category
                if delivery_time <= 2.0:
                    speed = "fast"
                elif delivery_time <= 4.0:
                    speed = "standard"
                else:
                    speed = "slow"
                
                delivery_options.append({
                    "store_id": store.store_id,
                    "store_name": store.name,
                    "brand": brand,
                    "city": store.city,
                    "distance_km": round(distance, 2),
                    "delivery_charge_lkr": round(delivery_charge, 2),
                    "estimated_delivery_hours": delivery_time,
                    "delivery_speed": speed,
                    "total_product_cost": total_product_cost,
                    "total_with_delivery": round(total_product_cost + delivery_charge, 2),
                    "is_available": True,
                    "product_count": len(products)
                })
    
    # Sort by total cost (product + delivery)
    delivery_options.sort(key=lambda x: x['total_with_delivery'])
    
    # Find best recommendation (balance of cost and speed)
    recommended = None
    if delivery_options:
        # Prefer fast delivery if cost difference is reasonable
        fast_options = [opt for opt in delivery_options if opt['delivery_speed'] == 'fast']
        cheapest_option = delivery_options[0]
        
        if fast_options:
            fast_option = fast_options[0]
            cost_difference = fast_option['total_with_delivery'] - cheapest_option['total_with_delivery']
            
            # Recommend fast option if cost difference is less than 20% or LKR 200
            if cost_difference <= max(cheapest_option['total_with_delivery'] * 0.2, 200):
                recommended = fast_option
            else:
                recommended = cheapest_option
        else:
            recommended = cheapest_option
    
    print(f"[TOOL] Found {len(delivery_options)} delivery options")
    
    return {
        "user_location": user_location,
        "delivery_options": delivery_options,
        "recommended_option": recommended,
        "total_options": len(delivery_options),
        "optimization_summary": {
            "cheapest_total": delivery_options[0]['total_with_delivery'] if delivery_options else 0,
            "fastest_delivery": min(opt['estimated_delivery_hours'] for opt in delivery_options) if delivery_options else 0,
            "brands_available": list(set(opt['brand'] for opt in delivery_options))
        }
    }


@tool
def calculate_multi_store_delivery(user_location: Dict[str, Any], items_by_store: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate delivery options when items come from multiple stores
    
    Args:
        user_location: User's location information
        items_by_store: Dictionary mapping store brands to their items
        
    Returns:
        Multi-store delivery optimization
    """
    print(f"[TOOL] Calculating multi-store delivery for {len(items_by_store)} stores")
    
    user_lat = user_location.get('latitude')
    user_lon = user_location.get('longitude')
    
    if not user_lat or not user_lon:
        return {"error": "User location coordinates required"}
    
    store_deliveries = []
    total_product_cost = 0
    total_delivery_cost = 0
    max_delivery_time = 0
    
    for brand, items in items_by_store.items():
        # Find nearest store for this brand
        brand_stores = [s for s in STORE_LOCATIONS if s.brand == brand]
        
        if not brand_stores:
            continue
        
        # Find nearest available store
        nearest_store = None
        min_distance = float('inf')
        
        for store in brand_stores:
            distance = haversine_distance(user_lat, user_lon, store.latitude, store.longitude)
            within_radius = distance <= store.max_delivery_radius_km
            
            if distance <= store.max_delivery_radius_km and distance < min_distance:
                min_distance = distance
                nearest_store = store
        
        if nearest_store:
            item_cost = sum(float(item.get('price', 0)) for item in items)
            delivery_charge = calculate_delivery_cost(nearest_store.delivery_charge_lkr, min_distance)
            delivery_time = estimate_delivery_time(min_distance, nearest_store.average_delivery_hours)
            
            store_deliveries.append({
                "brand": brand,
                "store_name": nearest_store.name,
                "store_id": nearest_store.store_id,
                "distance_km": round(min_distance, 2),
                "item_count": len(items),
                "item_cost_lkr": round(item_cost, 2),
                "delivery_charge_lkr": round(delivery_charge, 2),
                "estimated_delivery_hours": delivery_time
            })
            
            total_product_cost += item_cost
            total_delivery_cost += delivery_charge
            max_delivery_time = max(max_delivery_time, delivery_time)
    
    print(f"[TOOL] Multi-store delivery calculated for {len(store_deliveries)} stores")
    
    return {
        "user_location": user_location,
        "store_deliveries": store_deliveries,
        "summary": {
            "total_stores": len(store_deliveries),
            "total_product_cost_lkr": round(total_product_cost, 2),
            "total_delivery_cost_lkr": round(total_delivery_cost, 2),
            "grand_total_lkr": round(total_product_cost + total_delivery_cost, 2),
            "estimated_delivery_hours": max_delivery_time,
            "delivery_coordination": "Items will arrive separately from different stores"
        }
    }


@tool
def filter_items_by_distance(user_location: Dict[str, Any], personalized_data: Dict[str, List[Dict[str, Any]]], max_distance_km: float = 100.0) -> Dict[str, Any]:
    """
    Filter out items from stores that are too far away from user location.
    Keep at least one item per category even if it's far away.
    
    Args:
        user_location: User's location information
        personalized_data: Dictionary mapping keywords to their personalized items
        max_distance_km: Maximum acceptable distance in kilometers
        
    Returns:
        Filtered personalized data with distance-based filtering applied
    """
    print(f"[TOOL] Filtering items by distance (max: {max_distance_km}km) for {len(personalized_data)} categories")
    
    user_lat = user_location.get('latitude')
    user_lon = user_location.get('longitude')
    
    if not user_lat or not user_lon:
        return {"error": "User location coordinates required"}
    
    filtered_data = {}
    filtering_summary = {
        "total_categories": len(personalized_data),
        "categories_filtered": 0,
        "items_before_filtering": 0,
        "items_after_filtering": 0,
        "items_removed": 0,
        "single_item_categories_kept": 0,
        "distance_threshold_km": max_distance_km
    }
    
    for keyword, items in personalized_data.items():
        if not items:
            filtered_data[keyword] = items
            continue
        
        filtering_summary["items_before_filtering"] += len(items)
        
        # If only one item in category, keep it regardless of distance
        if len(items) == 1:
            filtered_data[keyword] = items
            filtering_summary["items_after_filtering"] += len(items)
            filtering_summary["single_item_categories_kept"] += 1
            print(f"[TOOL] Keeping single item in '{keyword}' category regardless of distance")
            continue
        
        # Multiple items - filter by distance
        items_with_distance = []
        
        for item in items:
            # Get item's store/brand
            brand = item.get('collection', item.get('website', 'unknown'))
            
            # Find nearest store for this brand
            nearest_distance = float('inf')
            nearest_store = None
            
            for store in STORE_LOCATIONS:
                if store.brand == brand:
                    distance = haversine_distance(user_lat, user_lon, store.latitude, store.longitude)
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_store = store
            
            # Add distance info to item
            item_with_distance = item.copy()
            item_with_distance['_logistics_distance_km'] = round(nearest_distance, 2)
            item_with_distance['_logistics_store'] = nearest_store.name if nearest_store else 'Unknown'
            item_with_distance['_logistics_within_threshold'] = nearest_distance <= max_distance_km
            
            items_with_distance.append(item_with_distance)
        
        # Filter items within distance threshold
        nearby_items = [item for item in items_with_distance if item['_logistics_within_threshold']]
        
        # If no items within threshold, keep the closest one
        if not nearby_items:
            closest_item = min(items_with_distance, key=lambda x: x['_logistics_distance_km'])
            filtered_items = [closest_item]
            print(f"[TOOL] No items within {max_distance_km}km for '{keyword}' - keeping closest item at {closest_item['_logistics_distance_km']}km")
        else:
            filtered_items = nearby_items
            removed_count = len(items) - len(filtered_items)
            if removed_count > 0:
                filtering_summary["categories_filtered"] += 1
                print(f"[TOOL] Filtered '{keyword}': {len(items)} → {len(filtered_items)} items (removed {removed_count} distant items)")
        
        # Clean up logistics metadata before storing
        clean_items = []
        for item in filtered_items:
            clean_item = {k: v for k, v in item.items() if not k.startswith('_logistics_')}
            clean_items.append(clean_item)
        
        filtered_data[keyword] = clean_items
        filtering_summary["items_after_filtering"] += len(clean_items)
    
    filtering_summary["items_removed"] = filtering_summary["items_before_filtering"] - filtering_summary["items_after_filtering"]
    
    print(f"[TOOL] Distance filtering complete: {filtering_summary['items_before_filtering']} → {filtering_summary['items_after_filtering']} items")
    
    return {
        "filtered_personalized_data": filtered_data,
        "filtering_summary": filtering_summary,
        "user_location": user_location
    }


class LogisticsAgent:
    """Logistics Agent for filtering items based on delivery distance"""
    
    def __init__(self, llm: ChatOllama):
        """Initialize the Logistics Agent"""
        self.llm = llm
        
        # Create LLM without JSON mode for tool calling
        self.tool_llm = ChatOllama(base_url=Config.OLLAMA_BASE_URL, 
            model=Config.GROQ_MODEL,
            temperature=Config.GROQ_TEMPERATURE
        )
        
        print("[AGENT] Logistics Agent initialized")
    
    def filter_by_distance(self, user_location: UserLocation, personalized_data: Dict[str, List[Dict[str, Any]]], max_distance_km: float = 100.0) -> Dict[str, Any]:
        """
        Main method to filter personalized items based on delivery distance
        
        Args:
            user_location: User's location information
            personalized_data: Dictionary mapping keywords to their personalized items
            max_distance_km: Maximum acceptable distance in kilometers
            
        Returns:
            Filtered personalized data with distance-based filtering applied
        """
        start_time = time.time()
        
        print(f"[AGENT] Logistics Agent filtering items within {max_distance_km}km of {user_location.city}")
        
        # Convert user location to dictionary for tools
        user_loc_dict = {
            "latitude": user_location.latitude,
            "longitude": user_location.longitude,
            "address": user_location.address,
            "city": user_location.city,
            "district": user_location.district,
            "province": user_location.province
        }
        
        # Apply distance-based filtering
        filtering_result = filter_items_by_distance.invoke({
            "user_location": user_loc_dict,
            "personalized_data": personalized_data,
            "max_distance_km": max_distance_km
        })
        
        filtering_time = time.time() - start_time
        
        if "error" in filtering_result:
            print(f"[AGENT] Filtering failed: {filtering_result['error']}")
            return {
                "filtered_personalized_data": personalized_data,  # Return original data on error
                "filtering_summary": {"error": filtering_result["error"]},
                "filtering_time_seconds": filtering_time
            }
        
        # Add timing information
        filtering_result["filtering_time_seconds"] = filtering_time
        
        summary = filtering_result.get("filtering_summary", {})
        print(f"[AGENT] Distance filtering completed in {filtering_time:.2f}s")
        print(f"[AGENT] Items: {summary.get('items_before_filtering', 0)} → {summary.get('items_after_filtering', 0)} (removed {summary.get('items_removed', 0)})")
        
        return filtering_result
    
    def get_available_stores_near_location(self, user_location: UserLocation, max_distance_km: float = 100.0) -> Dict[str, Any]:
        """
        Get information about stores available near the user's location
        
        Args:
            user_location: User's location information
            max_distance_km: Maximum distance to consider
            
        Returns:
            Information about nearby stores
        """
        user_lat = user_location.latitude
        user_lon = user_location.longitude
        
        nearby_stores = []
        
        for store in STORE_LOCATIONS:
            distance = haversine_distance(user_lat, user_lon, store.latitude, store.longitude)
            
            if distance <= max_distance_km:
                nearby_stores.append({
                    "store_id": store.store_id,
                    "name": store.name,
                    "brand": store.brand,
                    "city": store.city,
                    "distance_km": round(distance, 2),
                    "within_delivery_radius": distance <= store.max_delivery_radius_km,
                    "delivery_charge_lkr": store.delivery_charge_lkr,
                    "estimated_delivery_hours": estimate_delivery_time(distance, store.average_delivery_hours)
                })
        
        # Sort by distance
        nearby_stores.sort(key=lambda x: x['distance_km'])
        
        return {
            "user_location": {
                "city": user_location.city,
                "latitude": user_location.latitude,
                "longitude": user_location.longitude
            },
            "nearby_stores": nearby_stores,
            "total_stores_nearby": len(nearby_stores),
            "search_radius_km": max_distance_km
        }
