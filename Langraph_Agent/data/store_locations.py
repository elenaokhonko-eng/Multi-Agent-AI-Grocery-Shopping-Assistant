"""
Store location data for Singapore e-grocery platforms
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class StoreLocation:
    """Store location with coordinates and delivery info"""
    store_id: str
    name: str
    brand: str  # littlefarms, fairprice, shengsiong, coldstorage, lazada
    address: str
    city: str
    district: str
    province: str
    latitude: float
    longitude: float
    delivery_charge_lkr: float  # Serves as SGD charge in Singapore mode
    max_delivery_radius_km: float
    average_delivery_hours: float
    operating_hours: str
    phone: str
    is_warehouse: bool = False

# Store location data for major hubs/outlets in Singapore
STORE_LOCATIONS: List[StoreLocation] = [
    # Little Farms Outlets
    StoreLocation(
        store_id="LTF_RVR_001",
        name="Little Farms River Valley",
        brand="littlefarms",
        address="491 River Valley Road, #01-20 Valley Point, Singapore 248371",
        city="Singapore",
        district="Central",
        province="Central",
        latitude=1.2925,
        longitude=103.8262,
        delivery_charge_lkr=12.0,  # SGD 12
        max_delivery_radius_km=30.0,
        average_delivery_hours=1.5,
        operating_hours="7:30 AM - 9:30 PM",
        phone="+65 6262 0616",
        is_warehouse=False
    ),
    StoreLocation(
        store_id="LTF_BKT_002",
        name="Little Farms Bukit Timah",
        brand="littlefarms",
        address="10 Jalan Serene, #01-04 Serene Centre, Singapore 258748",
        city="Singapore",
        district="Bukit Timah",
        province="West",
        latitude=1.3225,
        longitude=103.8080,
        delivery_charge_lkr=12.0,  # SGD 12
        max_delivery_radius_km=30.0,
        average_delivery_hours=1.5,
        operating_hours="7:30 AM - 9:30 PM",
        phone="+65 6262 0616",
        is_warehouse=False
    ),
    
    # FairPrice Hubs
    StoreLocation(
        store_id="FP_JK_001",
        name="FairPrice Hub Joo Koon",
        brand="fairprice",
        address="1 Joo Koon Circle, Singapore 629117",
        city="Singapore",
        district="Jurong",
        province="West",
        latitude=1.3275,
        longitude=103.6783,
        delivery_charge_lkr=7.0,  # SGD 7
        max_delivery_radius_km=40.0,
        average_delivery_hours=2.0,
        operating_hours="24/7",
        phone="+65 6552 2722",
        is_warehouse=True
    ),
    StoreLocation(
        store_id="FP_TP_002",
        name="FairPrice Tampines Hub",
        brand="fairprice",
        address="1 Tampines Walk, Singapore 528523",
        city="Singapore",
        district="Tampines",
        province="East",
        latitude=1.3525,
        longitude=103.9405,
        delivery_charge_lkr=7.0,  # SGD 7
        max_delivery_radius_km=40.0,
        average_delivery_hours=2.0,
        operating_hours="7:00 AM - 11:00 PM",
        phone="+65 6552 2722"
    ),

    # Sheng Siong Locations
    StoreLocation(
        store_id="SS_AMK_001",
        name="Sheng Siong Ang Mo Kio",
        brand="shengsiong",
        address="Block 122 Ang Mo Kio Avenue 3, Singapore 560122",
        city="Singapore",
        district="Ang Mo Kio",
        province="North-East",
        latitude=1.3683,
        longitude=103.8436,
        delivery_charge_lkr=6.0,  # SGD 6
        max_delivery_radius_km=30.0,
        average_delivery_hours=2.0,
        operating_hours="24/7",
        phone="+65 6456 8288"
    ),
    StoreLocation(
        store_id="SS_BDK_002",
        name="Sheng Siong Bedok",
        brand="shengsiong",
        address="Block 209 New Upper Changi Road, Singapore 460209",
        city="Singapore",
        district="Bedok",
        province="East",
        latitude=1.3245,
        longitude=103.9315,
        delivery_charge_lkr=6.0,  # SGD 6
        max_delivery_radius_km=30.0,
        average_delivery_hours=2.0,
        operating_hours="6:00 AM - 10:30 PM",
        phone="+65 6244 8288"
    ),

    # Cold Storage Outlets
    StoreLocation(
        store_id="CS_JEL_001",
        name="Cold Storage Jelita",
        brand="coldstorage",
        address="293 Holland Road, Jelita Shopping Centre, Singapore 278628",
        city="Singapore",
        district="Holland",
        province="West",
        latitude=1.3168,
        longitude=103.7845,
        delivery_charge_lkr=8.0,  # SGD 8
        max_delivery_radius_km=30.0,
        average_delivery_hours=1.5,
        operating_hours="8:00 AM - 10:00 PM",
        phone="+65 6469 3877",
        is_warehouse=False
    ),
    StoreLocation(
        store_id="CS_TNG_002",
        name="Cold Storage Tanglin Market Place",
        brand="coldstorage",
        address="19 Tanglin Road, #B1-01-19 Tanglin Shopping Centre, Singapore 247909",
        city="Singapore",
        district="Tanglin",
        province="Central",
        latitude=1.3048,
        longitude=103.8242,
        delivery_charge_lkr=8.0,  # SGD 8
        max_delivery_radius_km=35.0,
        average_delivery_hours=1.5,
        operating_hours="9:00 AM - 10:00 PM",
        phone="+65 6734 0105"
    ),

    # Lazada RedMart Warehouse
    StoreLocation(
        store_id="RED_TG_001",
        name="RedMart Toh Guan Warehouse",
        brand="lazada",
        address="Toh Guan Road East, Singapore 608829",
        city="Singapore",
        district="Jurong",
        province="West",
        latitude=1.3325,
        longitude=103.7485,
        delivery_charge_lkr=6.99,  # SGD 6.99
        max_delivery_radius_km=50.0,
        average_delivery_hours=2.0,
        operating_hours="24/7",
        phone="+65 6950 0950",
        is_warehouse=True
    )
]

def get_store_by_id(store_id: str) -> Optional[StoreLocation]:
    """Get store location details by ID"""
    for store in STORE_LOCATIONS:
        if store.store_id == store_id:
            return store
    return None
