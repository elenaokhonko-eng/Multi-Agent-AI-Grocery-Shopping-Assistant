"""
Store location data for Sri Lanka e-commerce platforms
"""
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class StoreLocation:
    """Store location with coordinates and delivery info"""
    store_id: str
    name: str
    brand: str  # glowmark, kapruka, onlinekade
    address: str
    city: str
    district: str
    province: str
    latitude: float
    longitude: float
    delivery_charge_lkr: float
    max_delivery_radius_km: float
    average_delivery_hours: float
    operating_hours: str
    phone: str
    is_warehouse: bool = False

# Store location data for major cities in Sri Lanka
STORE_LOCATIONS: List[StoreLocation] = [
    # Glowmark Stores
    StoreLocation(
        store_id="GLW_COL_001",
        name="Glowmark Colombo Main",
        brand="glowmark",
        address="123 Galle Road, Colombo 03",
        city="Colombo",
        district="Colombo",
        province="Western",
        latitude=6.9271,
        longitude=79.8612,
        delivery_charge_lkr=300.0,
        max_delivery_radius_km=25.0,
        average_delivery_hours=2.0,
        operating_hours="8:00 AM - 10:00 PM",
        phone="+94112123456",
        is_warehouse=True
    ),
    StoreLocation(
        store_id="GLW_KAN_001",
        name="Glowmark Kandy",
        brand="glowmark",
        address="456 Peradeniya Road, Kandy",
        city="Kandy",
        district="Kandy",
        province="Central",
        latitude=7.2906,
        longitude=80.6337,
        delivery_charge_lkr=250.0,
        max_delivery_radius_km=20.0,
        average_delivery_hours=2.5,
        operating_hours="8:00 AM - 9:00 PM",
        phone="+94812345678"
    ),
    StoreLocation(
        store_id="GLW_GAL_001",
        name="Glowmark Galle",
        brand="glowmark",
        address="789 Matara Road, Galle",
        city="Galle",
        district="Galle",
        province="Southern",
        latitude=6.0535,
        longitude=80.2210,
        delivery_charge_lkr=350.0,
        max_delivery_radius_km=15.0,
        average_delivery_hours=3.0,
        operating_hours="8:00 AM - 8:00 PM",
        phone="+94912345678"
    ),
    StoreLocation(
        store_id="GLW_JAF_001",
        name="Glowmark Jaffna",
        brand="glowmark",
        address="321 Hospital Road, Jaffna",
        city="Jaffna",
        district="Jaffna",
        province="Northern",
        latitude=9.6615,
        longitude=80.0255,
        delivery_charge_lkr=400.0,
        max_delivery_radius_km=18.0,
        average_delivery_hours=4.0,
        operating_hours="8:00 AM - 8:00 PM",
        phone="+94212345678"
    ),
    
    # Kapruka Stores
    StoreLocation(
        store_id="KAP_COL_001",
        name="Kapruka Colombo Hub",
        brand="kapruka",
        address="567 Duplication Road, Colombo 04",
        city="Colombo",
        district="Colombo",
        province="Western",
        latitude=6.8905,
        longitude=79.8563,
        delivery_charge_lkr=280.0,
        max_delivery_radius_km=30.0,
        average_delivery_hours=1.5,
        operating_hours="24/7",
        phone="+94112987654",
        is_warehouse=True
    ),
    StoreLocation(
        store_id="KAP_DEH_001",
        name="Kapruka Dehiwala",
        brand="kapruka",
        address="890 Galle Road, Dehiwala",
        city="Dehiwala",
        district="Colombo",
        province="Western",
        latitude=6.8519,
        longitude=79.8721,
        delivery_charge_lkr=250.0,
        max_delivery_radius_km=20.0,
        average_delivery_hours=1.5,
        operating_hours="7:00 AM - 11:00 PM",
        phone="+94112876543"
    ),
    StoreLocation(
        store_id="KAP_KAN_001",
        name="Kapruka Kandy Center",
        brand="kapruka",
        address="234 Dalada Veediya, Kandy",
        city="Kandy",
        district="Kandy",
        province="Central",
        latitude=7.2937,
        longitude=80.6349,
        delivery_charge_lkr=300.0,
        max_delivery_radius_km=22.0,
        average_delivery_hours=2.0,
        operating_hours="8:00 AM - 10:00 PM",
        phone="+94812876543"
    ),
    StoreLocation(
        store_id="KAP_NEG_001",
        name="Kapruka Negombo",
        brand="kapruka",
        address="456 Main Street, Negombo",
        city="Negombo",
        district="Gampaha",
        province="Western",
        latitude=7.2084,
        longitude=79.8405,
        delivery_charge_lkr=320.0,
        max_delivery_radius_km=25.0,
        average_delivery_hours=2.5,
        operating_hours="8:00 AM - 9:00 PM",
        phone="+94312876543"
    ),
    
    # OnlineKade Stores  
    StoreLocation(
        store_id="OLK_COL_001",
        name="OnlineKade Colombo Warehouse",
        brand="onlinekade",
        address="789 Baseline Road, Colombo 09",
        city="Colombo",
        district="Colombo",
        province="Western",
        latitude=6.9034,
        longitude=79.8597,
        delivery_charge_lkr=320.0,
        max_delivery_radius_km=28.0,
        average_delivery_hours=2.0,
        operating_hours="6:00 AM - 12:00 AM",
        phone="+94112765432",
        is_warehouse=True
    ),
    StoreLocation(
        store_id="OLK_KOT_001",
        name="OnlineKade Kottawa",
        brand="onlinekade",
        address="345 High Level Road, Kottawa",
        city="Kottawa",
        district="Colombo",
        province="Western",
        latitude=6.8176,
        longitude=79.9733,
        delivery_charge_lkr=280.0,
        max_delivery_radius_km=20.0,
        average_delivery_hours=2.0,
        operating_hours="8:00 AM - 10:00 PM",
        phone="+94112654321"
    ),
    StoreLocation(
        store_id="OLK_GAM_001",
        name="OnlineKade Gampaha",
        brand="onlinekade",
        address="678 Colombo Road, Gampaha",
        city="Gampaha",
        district="Gampaha",
        province="Western",
        latitude=7.0873,
        longitude=79.9990,
        delivery_charge_lkr=300.0,
        max_delivery_radius_km=18.0,
        average_delivery_hours=2.5,
        operating_hours="8:00 AM - 9:00 PM",
        phone="+94332654321"
    ),
    StoreLocation(
        store_id="OLK_KUR_001",
        name="OnlineKade Kurunegala",
        brand="onlinekade",
        address="901 Kandy Road, Kurunegala",
        city="Kurunegala",
        district="Kurunegala",
        province="North Western",
        latitude=7.4818,
        longitude=80.3609,
        delivery_charge_lkr=350.0,
        max_delivery_radius_km=22.0,
        average_delivery_hours=3.0,
        operating_hours="8:00 AM - 8:00 PM",
        phone="+94372654321"
    ),
    StoreLocation(
        store_id="OLK_MAT_001",
        name="OnlineKade Matara",
        brand="onlinekade",
        address="234 Anagarika Dharmapala Mawatha, Matara",
        city="Matara",
        district="Matara",
        province="Southern",
        latitude=5.9549,
        longitude=80.5550,
        delivery_charge_lkr=380.0,
        max_delivery_radius_km=16.0,
        average_delivery_hours=3.5,
        operating_hours="8:00 AM - 8:00 PM",
        phone="+94412654321"
    )
]

# Helper functions to work with store data
def get_stores_by_brand(brand: str) -> List[StoreLocation]:
    """Get all stores for a specific brand"""
    return [store for store in STORE_LOCATIONS if store.brand == brand]

def get_stores_by_city(city: str) -> List[StoreLocation]:
    """Get all stores in a specific city"""
    return [store for store in STORE_LOCATIONS if store.city.lower() == city.lower()]

def get_stores_by_province(province: str) -> List[StoreLocation]:
    """Get all stores in a specific province"""
    return [store for store in STORE_LOCATIONS if store.province.lower() == province.lower()]

def get_warehouses() -> List[StoreLocation]:
    """Get all warehouse locations"""
    return [store for store in STORE_LOCATIONS if store.is_warehouse]

def get_store_by_id(store_id: str) -> StoreLocation:
    """Get a specific store by ID"""
    for store in STORE_LOCATIONS:
        if store.store_id == store_id:
            return store
    raise ValueError(f"Store with ID {store_id} not found")

# Store brand mapping for easy access
BRAND_STORES = {
    "glowmark": get_stores_by_brand("glowmark"),
    "kapruka": get_stores_by_brand("kapruka"), 
    "onlinekade": get_stores_by_brand("onlinekade")
}
