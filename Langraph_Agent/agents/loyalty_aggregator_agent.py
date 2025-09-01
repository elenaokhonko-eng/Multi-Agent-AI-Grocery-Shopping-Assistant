"""
Loyalty Aggregator Agent with LLM-based discount optimization
"""
import json
from typing import List, Dict, Any, Tuple
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from data.loyalty_programs import (
    get_loyalty_program, get_applicable_bank_discounts, 
    get_store_promotions, DiscountType, LOYALTY_PROGRAMS, BANK_DISCOUNTS
)


@tool
def calculate_loyalty_points(items: List[Dict[str, Any]], store_name: str) -> Dict[str, Any]:
    """
    Calculate loyalty points earned from purchase.
    
    Args:
        items: List of product items
        store_name: Name of the store
        
    Returns:
        Dictionary with loyalty points calculation
    """
    print(f"[TOOL] Loyalty Points Calculator - Processing {len(items)} items for {store_name}")
    
    loyalty_program = get_loyalty_program(store_name)
    if not loyalty_program:
        return {"points_earned": 0, "program": None, "message": f"No loyalty program found for {store_name}"}
    
    total_cost = sum(item.get('price_lkr', 0) for item in items)
    points_earned = int(total_cost * loyalty_program.points_per_lkr)
    potential_redemption = points_earned // loyalty_program.redemption_rate
    
    result = {
        "points_earned": points_earned,
        "total_purchase": total_cost,
        "program_name": loyalty_program.program_name,
        "points_per_lkr": loyalty_program.points_per_lkr,
        "potential_redemption_lkr": potential_redemption,
        "current_total_points": loyalty_program.current_points + points_earned
    }
    
    print(f"[TOOL] Points calculated: {points_earned} points for LKR {total_cost}")
    return result


@tool
def calculate_bank_discounts(items: List[Dict[str, Any]], store_name: str) -> List[Dict[str, Any]]:
    """
    Calculate available bank card discounts.
    
    Args:
        items: List of product items
        store_name: Name of the store
        
    Returns:
        List of applicable bank discount calculations
    """
    print(f"[TOOL] Bank Discount Calculator - Processing {len(items)} items for {store_name}")
    
    # Extract categories from items
    categories = set()
    for item in items:
        # Simple category extraction from title
        title = item.get('title', '').lower()
        if any(word in title for word in ['rice', 'bread', 'milk', 'tea', 'coffee', 'sugar']):
            categories.add('groceries')
        if any(word in title for word in ['soap', 'shampoo', 'toothpaste', 'detergent']):
            categories.add('personal_care')
        if any(word in title for word in ['tablet', 'medicine', 'vitamin', 'supplement']):
            categories.add('health')
    
    categories = list(categories) if categories else ['groceries']
    total_cost = sum(item.get('price_lkr', 0) for item in items)
    
    applicable_discounts = get_applicable_bank_discounts(store_name, categories)
    
    discount_calculations = []
    for discount in applicable_discounts:
        if total_cost >= discount.min_purchase:
            discount_amount = min(
                total_cost * (discount.discount_percentage / 100),
                discount.max_discount
            )
            
            discount_calculations.append({
                "bank_name": discount.bank_name,
                "card_type": discount.card_type,
                "discount_percentage": discount.discount_percentage,
                "discount_amount": discount_amount,
                "final_cost": total_cost - discount_amount,
                "savings": discount_amount,
                "min_purchase": discount.min_purchase,
                "eligible": True
            })
        else:
            discount_calculations.append({
                "bank_name": discount.bank_name,
                "card_type": discount.card_type,
                "discount_percentage": discount.discount_percentage,
                "discount_amount": 0,
                "final_cost": total_cost,
                "savings": 0,
                "min_purchase": discount.min_purchase,
                "eligible": False,
                "shortfall": discount.min_purchase - total_cost
            })
    
    print(f"[TOOL] Bank discounts: {len([d for d in discount_calculations if d['eligible']])} eligible discounts")
    return discount_calculations


@tool
def calculate_store_promotions(items: List[Dict[str, Any]], store_name: str) -> List[Dict[str, Any]]:
    """
    Calculate savings from store-specific promotions.
    
    Args:
        items: List of product items
        store_name: Name of the store
        
    Returns:
        List of applicable promotion calculations
    """
    print(f"[TOOL] Store Promotions Calculator - Processing {len(items)} items for {store_name}")
    
    promotions = get_store_promotions(store_name)
    if not promotions:
        return []
    
    total_cost = sum(item.get('price_lkr', 0) for item in items)
    promotion_calculations = []
    
    for promo in promotions:
        # Check if promotion is applicable
        applicable_items = []
        for item in items:
            title = item.get('title', '').lower()
            # Simple category matching
            if any(cat in title for cat in promo.applicable_categories):
                applicable_items.append(item)
        
        if not applicable_items:
            continue
        
        applicable_cost = sum(item.get('price_lkr', 0) for item in applicable_items)
        
        if applicable_cost >= promo.min_purchase:
            if promo.discount_type == DiscountType.PERCENTAGE:
                discount_amount = min(
                    applicable_cost * (promo.discount_value / 100),
                    promo.max_discount if promo.max_discount > 0 else applicable_cost
                )
            elif promo.discount_type == DiscountType.FIXED_AMOUNT:
                discount_amount = min(promo.discount_value, applicable_cost)
            elif promo.discount_type == DiscountType.CASHBACK:
                discount_amount = min(
                    applicable_cost * (promo.discount_value / 100),
                    promo.max_discount if promo.max_discount > 0 else applicable_cost
                )
            else:  # BUY_X_GET_Y
                discount_amount = applicable_cost * 0.33  # Approximate 33% savings for buy 2 get 1
            
            promotion_calculations.append({
                "promotion_id": promo.promotion_id,
                "title": promo.title,
                "discount_type": promo.discount_type.value,
                "discount_amount": discount_amount,
                "applicable_items_count": len(applicable_items),
                "applicable_cost": applicable_cost,
                "final_cost": applicable_cost - discount_amount,
                "savings": discount_amount,
                "eligible": True,
                "conditions": promo.conditions
            })
    
    print(f"[TOOL] Store promotions: {len(promotion_calculations)} applicable promotions")
    return promotion_calculations


@tool
def optimize_discount_combination(
    loyalty_points: Dict[str, Any],
    bank_discounts: List[Dict[str, Any]],
    store_promotions: List[Dict[str, Any]],
    total_cost: float
) -> Dict[str, Any]:
    """
    Find the optimal combination of discounts to maximize savings.
    
    Args:
        loyalty_points: Loyalty points calculation
        bank_discounts: List of bank discount options
        store_promotions: List of store promotion options
        total_cost: Total purchase cost
        
    Returns:
        Optimal discount combination strategy
    """
    print(f"[TOOL] Discount Optimizer - Finding best combination for LKR {total_cost}")
    
    # Find best bank discount
    eligible_bank_discounts = [d for d in bank_discounts if d.get('eligible', False)]
    best_bank_discount = max(eligible_bank_discounts, key=lambda x: x['savings'], default=None)
    
    # Find best store promotion
    best_store_promotion = max(store_promotions, key=lambda x: x['savings'], default=None)
    
    # Calculate total savings (assuming they can be combined)
    total_savings = 0
    used_discounts = []
    
    if best_bank_discount:
        total_savings += best_bank_discount['savings']
        used_discounts.append({
            "type": "bank_discount",
            "description": f"{best_bank_discount['bank_name']} {best_bank_discount['card_type']}",
            "savings": best_bank_discount['savings']
        })
    
    if best_store_promotion:
        total_savings += best_store_promotion['savings']
        used_discounts.append({
            "type": "store_promotion",
            "description": best_store_promotion['title'],
            "savings": best_store_promotion['savings']
        })
    
    # Add loyalty points value
    loyalty_value = loyalty_points.get('potential_redemption_lkr', 0)
    if loyalty_value > 0:
        used_discounts.append({
            "type": "loyalty_redemption",
            "description": f"Redeem {loyalty_points.get('points_earned', 0)} points",
            "savings": loyalty_value
        })
    
    final_cost = total_cost - total_savings
    savings_percentage = (total_savings / total_cost * 100) if total_cost > 0 else 0
    
    optimization_result = {
        "original_cost": total_cost,
        "total_savings": total_savings,
        "final_cost": final_cost,
        "savings_percentage": round(savings_percentage, 2),
        "used_discounts": used_discounts,
        "loyalty_points_earned": loyalty_points.get('points_earned', 0),
        "recommendation": "optimal" if total_savings > total_cost * 0.1 else "moderate"
    }
    
    print(f"[TOOL] Optimization complete: LKR {total_savings} savings ({savings_percentage:.1f}%)")
    return optimization_result


class LoyaltyAggregatorAgent:
    """Agent responsible for optimizing discounts and loyalty benefits"""
    
    def __init__(self, llm: ChatGroq):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        # Available tools
        self.tools = [
            calculate_loyalty_points,
            calculate_bank_discounts,
            calculate_store_promotions,
            optimize_discount_combination
        ]
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    def optimize_loyalty_benefits(self, items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Optimize items selection based on loyalty benefits and discounts
        
        Args:
            items: List of product items to optimize
            
        Returns:
            Tuple of (optimized_items, loyalty_summary)
        """
        print(f"[AGENT] Loyalty Aggregator Agent processing {len(items)} items")
        
        if not items:
            return items, {"message": "No items to process"}
        
        # Group items by store for optimization
        items_by_store = {}
        for item in items:
            store = item.get('website', 'unknown').lower()
            if store not in items_by_store:
                items_by_store[store] = []
            items_by_store[store].append(item)
        
        store_optimizations = []
        total_original_cost = 0
        total_optimized_cost = 0
        total_savings = 0
        
        for store_name, store_items in items_by_store.items():
            try:
                # Calculate loyalty points
                loyalty_calc = calculate_loyalty_points.invoke({
                    "items": store_items,
                    "store_name": store_name
                })
                
                # Calculate bank discounts
                bank_discounts = calculate_bank_discounts.invoke({
                    "items": store_items,
                    "store_name": store_name
                })
                
                # Calculate store promotions
                store_promotions = calculate_store_promotions.invoke({
                    "items": store_items,
                    "store_name": store_name
                })
                
                # Optimize discount combination
                store_cost = sum(item.get('price_lkr', 0) for item in store_items)
                optimization = optimize_discount_combination.invoke({
                    "loyalty_points": loyalty_calc,
                    "bank_discounts": bank_discounts,
                    "store_promotions": store_promotions,
                    "total_cost": store_cost
                })
                
                store_optimizations.append({
                    "store_name": store_name,
                    "items_count": len(store_items),
                    "original_cost": store_cost,
                    "optimized_cost": optimization["final_cost"],
                    "savings": optimization["total_savings"],
                    "loyalty_points": loyalty_calc,
                    "best_discounts": optimization["used_discounts"],
                    "optimization": optimization
                })
                
                total_original_cost += store_cost
                total_optimized_cost += optimization["final_cost"]
                total_savings += optimization["total_savings"]
                
            except Exception as e:
                print(f"[AGENT] Error processing {store_name}: {e}")
                store_cost = sum(item.get('price_lkr', 0) for item in store_items)
                store_optimizations.append({
                    "store_name": store_name,
                    "items_count": len(store_items),
                    "original_cost": store_cost,
                    "optimized_cost": store_cost,
                    "savings": 0,
                    "error": str(e)
                })
                total_original_cost += store_cost
                total_optimized_cost += store_cost
        
        # Create LLM-powered recommendation
        prompt = f"""
        You are a Loyalty Optimization Expert. Analyze the discount calculations and provide strategic recommendations.
        
        Store Optimizations Summary:
        {json.dumps(store_optimizations, indent=2)}
        
        Total Original Cost: LKR {total_original_cost}
        Total Optimized Cost: LKR {total_optimized_cost}
        Total Savings: LKR {total_savings}
        Savings Percentage: {(total_savings/total_original_cost*100) if total_original_cost > 0 else 0:.1f}%
        
        Provide:
        1. Strategic recommendations for maximizing savings
        2. Alternative shopping strategies if applicable
        3. Long-term loyalty optimization advice
        4. Priority ranking of stores based on value
        """
        
        try:
            response = self.llm.invoke(prompt)
            llm_recommendations = response.content
        except Exception as e:
            llm_recommendations = f"Unable to generate LLM recommendations: {e}"
        
        loyalty_summary = {
            "total_original_cost": total_original_cost,
            "total_optimized_cost": total_optimized_cost,
            "total_savings": total_savings,
            "savings_percentage": round((total_savings/total_original_cost*100) if total_original_cost > 0 else 0, 2),
            "stores_analyzed": len(store_optimizations),
            "store_optimizations": store_optimizations,
            "llm_recommendations": llm_recommendations,
            "optimization_summary": {
                "best_store_for_savings": max(store_optimizations, key=lambda x: x.get('savings', 0), default={}).get('store_name', 'N/A'),
                "total_loyalty_points": sum(opt.get('loyalty_points', {}).get('points_earned', 0) for opt in store_optimizations),
                "recommended_action": "optimize" if total_savings > total_original_cost * 0.05 else "proceed"
            }
        }
        
        print(f"[AGENT] Loyalty optimization completed: LKR {total_savings} total savings")
        return items, loyalty_summary
    
    def get_loyalty_summary(self) -> Dict[str, Any]:
        """Get summary of available loyalty programs and discounts"""
        return {
            "available_loyalty_programs": len(LOYALTY_PROGRAMS),
            "available_bank_discounts": len(BANK_DISCOUNTS),
            "loyalty_programs": list(LOYALTY_PROGRAMS.keys()),
            "bank_partners": list(set(d.bank_name for d in BANK_DISCOUNTS))
        }
