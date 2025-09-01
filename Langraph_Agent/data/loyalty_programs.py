"""
Loyalty Programs Database for Sri Lankan Supermarkets
"""
from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class DiscountType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BUY_X_GET_Y = "buy_x_get_y"
    CASHBACK = "cashback"

@dataclass
class LoyaltyProgram:
    store_name: str
    program_name: str
    membership_tiers: List[str]
    points_per_lkr: float
    redemption_rate: float  # points per LKR
    current_points: int
    tier_benefits: Dict[str, Dict[str, Any]]
    active_promotions: List[Dict[str, Any]]

@dataclass
class BankDiscount:
    bank_name: str
    card_type: str
    discount_percentage: float
    min_purchase: float
    max_discount: float
    applicable_stores: List[str]
    applicable_categories: List[str]

@dataclass
class Promotion:
    promotion_id: str
    store_name: str
    title: str
    discount_type: DiscountType
    discount_value: float
    min_purchase: float
    max_discount: float
    applicable_categories: List[str]
    valid_until: str
    conditions: str

# Sri Lankan Supermarket Loyalty Programs
LOYALTY_PROGRAMS = {
    "keells": LoyaltyProgram(
        store_name="Keells Super",
        program_name="Keells Nexus",
        membership_tiers=["Silver", "Gold", "Platinum"],
        points_per_lkr=1.0,
        redemption_rate=100,  # 100 points = 1 LKR
        current_points=2500,
        tier_benefits={
            "Silver": {"discount_percentage": 2, "free_delivery": False},
            "Gold": {"discount_percentage": 3, "free_delivery": True},
            "Platinum": {"discount_percentage": 5, "free_delivery": True, "priority_service": True}
        },
        active_promotions=[
            {
                "title": "Weekend Grocery Bonus",
                "discount": 10,
                "min_purchase": 5000,
                "categories": ["groceries", "household"]
            }
        ]
    ),
    
    "cargills": LoyaltyProgram(
        store_name="Cargills Food City",
        program_name="Cargills Rewards",
        membership_tiers=["Basic", "Premium", "Elite"],
        points_per_lkr=0.8,
        redemption_rate=80,
        current_points=1800,
        tier_benefits={
            "Basic": {"discount_percentage": 1.5, "birthday_bonus": 5},
            "Premium": {"discount_percentage": 2.5, "birthday_bonus": 10, "early_access": True},
            "Elite": {"discount_percentage": 4, "birthday_bonus": 15, "early_access": True, "concierge": True}
        },
        active_promotions=[
            {
                "title": "Fresh Produce Friday",
                "discount": 15,
                "min_purchase": 2000,
                "categories": ["fruits", "vegetables"]
            }
        ]
    ),
    
    "arpico": LoyaltyProgram(
        store_name="Arpico Supercenter",
        program_name="Arpico Plus",
        membership_tiers=["Member", "VIP"],
        points_per_lkr=1.2,
        redemption_rate=120,
        current_points=3200,
        tier_benefits={
            "Member": {"discount_percentage": 2, "special_offers": True},
            "VIP": {"discount_percentage": 4, "special_offers": True, "express_checkout": True}
        },
        active_promotions=[
            {
                "title": "Electronics Mega Sale",
                "discount": 20,
                "min_purchase": 10000,
                "categories": ["electronics", "appliances"]
            }
        ]
    )
}

# Bank Credit/Debit Card Discounts
BANK_DISCOUNTS = [
    BankDiscount(
        bank_name="Commercial Bank",
        card_type="Visa Credit",
        discount_percentage=5,
        min_purchase=3000,
        max_discount=500,
        applicable_stores=["keells", "cargills", "arpico"],
        applicable_categories=["groceries", "household", "personal_care"]
    ),
    
    BankDiscount(
        bank_name="Sampath Bank",
        card_type="Mastercard Debit",
        discount_percentage=3,
        min_purchase=2000,
        max_discount=300,
        applicable_stores=["cargills", "glowmark"],
        applicable_categories=["groceries", "health", "beauty"]
    ),
    
    BankDiscount(
        bank_name="HNB",
        card_type="Visa Debit",
        discount_percentage=4,
        min_purchase=2500,
        max_discount=400,
        applicable_stores=["keells", "arpico", "kapruka"],
        applicable_categories=["all"]
    ),
    
    BankDiscount(
        bank_name="BOC",
        card_type="Mastercard Credit",
        discount_percentage=6,
        min_purchase=5000,
        max_discount=1000,
        applicable_stores=["arpico", "onlinekade"],
        applicable_categories=["electronics", "appliances", "clothing"]
    )
]

# Current Active Promotions
ACTIVE_PROMOTIONS = [
    Promotion(
        promotion_id="PROMO001",
        store_name="keells",
        title="Back to School Special",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=15,
        min_purchase=4000,
        max_discount=600,
        applicable_categories=["stationery", "snacks", "beverages"],
        valid_until="2025-09-30",
        conditions="Valid for purchases above LKR 4000"
    ),
    
    Promotion(
        promotion_id="PROMO002",
        store_name="cargills",
        title="Healthy Living Week",
        discount_type=DiscountType.BUY_X_GET_Y,
        discount_value=2,  # Buy 2 Get 1
        min_purchase=1500,
        max_discount=0,
        applicable_categories=["health", "organic", "supplements"],
        valid_until="2025-09-15",
        conditions="Buy 2 Get 1 Free on health products"
    ),
    
    Promotion(
        promotion_id="PROMO003",
        store_name="arpico",
        title="Home Essentials Bundle",
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=500,
        min_purchase=8000,
        max_discount=500,
        applicable_categories=["household", "cleaning", "personal_care"],
        valid_until="2025-09-20",
        conditions="LKR 500 off on purchases above LKR 8000"
    ),
    
    Promotion(
        promotion_id="PROMO004",
        store_name="glowmark",
        title="Beauty Bonanza",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=20,
        min_purchase=3000,
        max_discount=800,
        applicable_categories=["beauty", "cosmetics", "skincare"],
        valid_until="2025-09-25",
        conditions="20% off on beauty products, max LKR 800"
    ),
    
    Promotion(
        promotion_id="PROMO005",
        store_name="kapruka",
        title="Tech Tuesday",
        discount_type=DiscountType.CASHBACK,
        discount_value=10,  # 10% cashback
        min_purchase=15000,
        max_discount=2000,
        applicable_categories=["electronics", "gadgets", "computers"],
        valid_until="2025-09-30",
        conditions="10% cashback on electronics, credited within 7 days"
    )
]

def get_loyalty_program(store_name: str) -> LoyaltyProgram:
    """Get loyalty program for a specific store"""
    store_key = store_name.lower().replace(" ", "").replace("super", "").replace("supercenter", "")
    return LOYALTY_PROGRAMS.get(store_key)

def get_applicable_bank_discounts(store_name: str, categories: List[str]) -> List[BankDiscount]:
    """Get applicable bank discounts for store and categories"""
    store_key = store_name.lower().replace(" ", "").replace("super", "").replace("supercenter", "")
    
    applicable_discounts = []
    for discount in BANK_DISCOUNTS:
        # Check if store is applicable
        if store_key in discount.applicable_stores or "all" in discount.applicable_stores:
            # Check if categories match
            if "all" in discount.applicable_categories or any(cat in discount.applicable_categories for cat in categories):
                applicable_discounts.append(discount)
    
    return applicable_discounts

def get_store_promotions(store_name: str) -> List[Promotion]:
    """Get active promotions for a specific store"""
    store_key = store_name.lower().replace(" ", "").replace("super", "").replace("supercenter", "")
    
    return [promo for promo in ACTIVE_PROMOTIONS if promo.store_name == store_key]
