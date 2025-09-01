"""
Budget Optimization Agent - Selects optimal single item per category
Combines mathematical optimization with LLM-powered decision making
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
try:
    import pulp  # Linear programming solver
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False
    print("⚠️ PuLP not installed. Install with: pip install pulp")

import numpy as np
from groq import Groq

# Import config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config.settings import Config
except ImportError:
    class Config:
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL = "llama-3.3-70b-versatile"
        DEBUG_MODE = True

@dataclass
class OptimizationConstraints:
    """Constraints for budget optimization"""
    max_budget: float
    max_delivery_time_hours: Optional[float] = None
    preferred_stores: List[str] = None
    avoid_stores: List[str] = None
    priority_weights: Dict[str, float] = None  # price, time, quality, loyalty
    
    def __post_init__(self):
        if self.priority_weights is None:
            self.priority_weights = {
                "price": 0.4,      # 40% weight on price
                "delivery_time": 0.25,  # 25% weight on delivery speed
                "quality": 0.20,   # 20% weight on product quality
                "loyalty_savings": 0.15  # 15% weight on loyalty benefits
            }

@dataclass
class StoreConfig:
    """Store configuration with delivery times and characteristics"""
    name: str
    average_delivery_hours: float
    reliability_score: float  # 0-1, based on historical data
    quality_rating: float     # 0-5, average product quality
    processing_time_hours: float  # Order processing time
    delivery_fee: float
    minimum_order: float
    
class BudgetOptimizationAgent:
    """
    Advanced Budget Optimization Agent
    Uses Linear Programming + LLM for optimal item selection per category
    """
    
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.store_configs = self._load_store_configs()
        self.optimization_tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculate_optimization_score",
                    "description": "Calculate multi-criteria optimization score for an item",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_data": {
                                "type": "object",
                                "description": "Item data including price, store, loyalty savings"
                            },
                            "constraints": {
                                "type": "object", 
                                "description": "User constraints and preferences"
                            }
                        },
                        "required": ["item_data", "constraints"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "solve_linear_program",
                    "description": "Solve linear programming problem for optimal selection",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "categories": {
                                "type": "object",
                                "description": "Items per category with scores"
                            },
                            "budget_limit": {
                                "type": "number",
                                "description": "Maximum budget constraint"
                            }
                        },
                        "required": ["categories", "budget_limit"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "generate_recommendation_reasoning",
                    "description": "Generate human-readable reasoning for recommendations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selected_items": {
                                "type": "array",
                                "description": "Final selected items per category"
                            },
                            "trade_offs": {
                                "type": "object",
                                "description": "Trade-offs made in optimization"
                            }
                        },
                        "required": ["selected_items", "trade_offs"]
                    }
                }
            }
        ]
    
    def _load_store_configs(self) -> Dict[str, StoreConfig]:
        """Load store configurations with delivery times from config file"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "config", 
                "store_config.json"
            )
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            store_configs = {}
            for store_id, config in config_data["stores"].items():
                store_configs[store_id] = StoreConfig(
                    name=config["name"],
                    average_delivery_hours=config["average_delivery_hours"],
                    reliability_score=config["reliability_score"],
                    quality_rating=config["quality_rating"],
                    processing_time_hours=config["processing_time_hours"],
                    delivery_fee=config["delivery_fee"],
                    minimum_order=config["minimum_order"]
                )
            
            return store_configs
            
        except Exception as e:
            print(f"⚠️ Could not load store config: {e}")
            # Fallback to hardcoded configs
            return {
                "kapruka.com": StoreConfig(
                    name="Kapruka",
                    average_delivery_hours=24.0,
                    reliability_score=0.92,
                    quality_rating=4.2,
                    processing_time_hours=2.0,
                    delivery_fee=200.0,
                    minimum_order=500.0
                ),
                "glowmark.lk": StoreConfig(
                    name="Glowmark", 
                    average_delivery_hours=18.0,
                    reliability_score=0.88,
                    quality_rating=4.0,
                    processing_time_hours=1.5,
                    delivery_fee=150.0,
                    minimum_order=300.0
                ),
                "onlinekade.lk": StoreConfig(
                    name="Online Kade",
                    average_delivery_hours=12.0,
                    reliability_score=0.85,
                    quality_rating=3.8,
                    processing_time_hours=1.0,
                    delivery_fee=100.0,
                    minimum_order=200.0
                )
            }
    
    def optimize_item_selection(
        self, 
        loyalty_optimized_data: Dict[str, List[Dict]], 
        constraints: OptimizationConstraints,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Main optimization function - selects best item per category
        
        Args:
            loyalty_optimized_data: Items organized by category after loyalty optimization
            constraints: Budget and preference constraints
            user_query: Original user query for context
            
        Returns:
            Optimized selection with one item per category
        """
        if Config.DEBUG_MODE:
            print(f"[AGENT] Budget Optimization Agent processing {len(loyalty_optimized_data)} categories")
        
        try:
            # Step 1: Calculate optimization scores for all items
            scored_categories = self._calculate_item_scores(loyalty_optimized_data, constraints)
            
            # Step 2: Use LLM to analyze and solve optimization problem
            optimization_result = self._llm_optimize_selection(
                scored_categories, constraints, user_query
            )
            
            # Step 3: Apply linear programming for mathematical optimization
            lp_solution = self._solve_linear_program(scored_categories, constraints)
            
            # Step 4: Combine LLM insights with mathematical solution
            final_selection = self._combine_solutions(
                optimization_result, lp_solution, scored_categories, constraints
            )
            
            # Step 5: Generate detailed reasoning
            reasoning = self._generate_optimization_reasoning(
                final_selection, constraints, scored_categories
            )
            
            return {
                "optimized_selection": final_selection,
                "optimization_summary": reasoning,
                "total_cost": sum(item["price_lkr"] for item in final_selection.values()),
                "total_delivery_time": max(
                    self.store_configs[item["website"]].average_delivery_hours 
                    for item in final_selection.values()
                ),
                "optimization_method": "hybrid_llm_linear_programming",
                "constraints_satisfied": self._validate_constraints(final_selection, constraints)
            }
            
        except Exception as e:
            print(f"❌ Budget optimization failed: {e}")
            return {"error": str(e)}
    
    def _calculate_item_scores(
        self, 
        categories: Dict[str, List[Dict]], 
        constraints: OptimizationConstraints
    ) -> Dict[str, List[Dict]]:
        """Calculate multi-criteria optimization scores for all items"""
        scored_categories = {}
        
        for category, items in categories.items():
            scored_items = []
            for item in items:
                score = self._calculate_optimization_score(item, constraints)
                item_with_score = {**item, "optimization_score": score}
                scored_items.append(item_with_score)
            
            # Sort by optimization score (higher is better)
            scored_items.sort(key=lambda x: x["optimization_score"], reverse=True)
            scored_categories[category] = scored_items
            
        return scored_categories
    
    def _calculate_optimization_score(
        self, 
        item: Dict, 
        constraints: OptimizationConstraints
    ) -> float:
        """Calculate multi-criteria optimization score for a single item"""
        weights = constraints.priority_weights
        store_config = self.store_configs.get(item["website"])
        
        if not store_config:
            return 0.0
        
        # Normalize scores (0-1 range)
        price_score = self._normalize_price_score(item["price_lkr"], constraints.max_budget)
        time_score = self._normalize_time_score(store_config.average_delivery_hours)
        quality_score = store_config.quality_rating / 5.0
        loyalty_score = self._normalize_loyalty_score(item.get("loyalty_savings", 0))
        
        # Weighted combination
        total_score = (
            weights["price"] * price_score +
            weights["delivery_time"] * time_score +
            weights["quality"] * quality_score +
            weights["loyalty_savings"] * loyalty_score
        )
        
        return total_score
    
    def _normalize_price_score(self, price: float, max_budget: float) -> float:
        """Normalize price score (lower price = higher score)"""
        if max_budget <= 0:
            return 0.5
        return max(0, 1 - (price / max_budget))
    
    def _normalize_time_score(self, delivery_hours: float) -> float:
        """Normalize delivery time score (faster = higher score)"""
        max_reasonable_time = 72.0  # 3 days
        return max(0, 1 - (delivery_hours / max_reasonable_time))
    
    def _normalize_loyalty_score(self, savings: float) -> float:
        """Normalize loyalty savings score"""
        max_reasonable_savings = 500.0  # LKR
        return min(1.0, savings / max_reasonable_savings)
    
    def _llm_optimize_selection(
        self, 
        scored_categories: Dict[str, List[Dict]], 
        constraints: OptimizationConstraints,
        user_query: str
    ) -> Dict[str, Any]:
        """Use LLM to analyze optimization problem and suggest solutions"""
        
        prompt = f"""
        You are a Budget Optimization Expert analyzing product selection for a Sri Lankan customer.

        USER QUERY: "{user_query}"
        BUDGET LIMIT: LKR {constraints.max_budget}
        CATEGORIES: {list(scored_categories.keys())}
        
        TASK: Select the BEST single item from each category considering:
        1. Total cost within budget
        2. Delivery time optimization  
        3. Quality and reliability
        4. Loyalty savings
        5. Store preferences
        
        DATA:
        {json.dumps(scored_categories, indent=2)}
        
        CONSTRAINTS:
        - Maximum budget: LKR {constraints.max_budget}
        - Maximum delivery time: {constraints.max_delivery_time_hours or 'No limit'} hours
        - Preferred stores: {constraints.preferred_stores or 'None'}
        - Avoid stores: {constraints.avoid_stores or 'None'}
        
        PROVIDE:
        1. Selected item ID for each category
        2. Reasoning for each selection
        3. Trade-offs analysis
        4. Total cost calculation
        5. Alternative recommendations if budget exceeded
        
        Use the available tools to calculate scores and solve the optimization problem.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                tools=self.optimization_tools,
                tool_choice="auto",
                temperature=0.1
            )
            
            # Process tool calls if any
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    if tool_call.function.name == "solve_linear_program":
                        args = json.loads(tool_call.function.arguments)
                        return self._solve_linear_program_tool(args)
            
            return {"llm_analysis": response.choices[0].message.content}
            
        except Exception as e:
            print(f"❌ LLM optimization failed: {e}")
            return {"error": str(e)}
    
    def _solve_linear_program(
        self, 
        scored_categories: Dict[str, List[Dict]], 
        constraints: OptimizationConstraints
    ) -> Dict[str, Any]:
        """Solve linear programming problem for optimal selection"""
        
        try:
            # Create the linear programming problem
            prob = pulp.LpProblem("Budget_Optimization", pulp.LpMaximize)
            
            # Decision variables: x[category][item_index] = 1 if selected, 0 otherwise
            variables = {}
            
            for category, items in scored_categories.items():
                variables[category] = []
                for i, item in enumerate(items):
                    var = pulp.LpVariable(
                        f"select_{category}_{i}", 
                        cat='Binary'
                    )
                    variables[category].append(var)
            
            # Objective function: maximize total optimization score
            objective = []
            for category, items in scored_categories.items():
                for i, item in enumerate(items):
                    objective.append(
                        item["optimization_score"] * variables[category][i]
                    )
            
            prob += pulp.lpSum(objective)
            
            # Constraints
            
            # 1. Select exactly one item per category
            for category, vars_list in variables.items():
                prob += pulp.lpSum(vars_list) == 1
            
            # 2. Budget constraint
            budget_constraint = []
            for category, items in scored_categories.items():
                for i, item in enumerate(items):
                    budget_constraint.append(
                        item["price_lkr"] * variables[category][i]
                    )
            prob += pulp.lpSum(budget_constraint) <= constraints.max_budget
            
            # 3. Delivery time constraint (if specified)
            if constraints.max_delivery_time_hours:
                for category, items in scored_categories.items():
                    for i, item in enumerate(items):
                        store_config = self.store_configs[item["website"]]
                        prob += (
                            store_config.average_delivery_hours * variables[category][i] 
                            <= constraints.max_delivery_time_hours
                        )
            
            # Solve the problem
            prob.solve(pulp.PULP_CBC_CMD(msg=0))
            
            # Extract solution
            solution = {}
            total_cost = 0
            max_delivery_time = 0
            
            for category, items in scored_categories.items():
                for i, item in enumerate(items):
                    if variables[category][i].varValue == 1:
                        solution[category] = item
                        total_cost += item["price_lkr"]
                        store_config = self.store_configs[item["website"]]
                        max_delivery_time = max(max_delivery_time, store_config.average_delivery_hours)
            
            return {
                "lp_solution": solution,
                "total_cost": total_cost,
                "max_delivery_time": max_delivery_time,
                "optimization_status": pulp.LpStatus[prob.status]
            }
            
        except Exception as e:
            print(f"❌ Linear programming failed: {e}")
            return {"error": str(e)}
    
    def _combine_solutions(
        self, 
        llm_result: Dict[str, Any], 
        lp_result: Dict[str, Any], 
        scored_categories: Dict[str, List[Dict]],
        constraints: OptimizationConstraints
    ) -> Dict[str, Dict]:
        """Combine LLM insights with mathematical optimization results"""
        
        # Prioritize LP solution if available and valid
        if "lp_solution" in lp_result and lp_result["lp_solution"]:
            return lp_result["lp_solution"]
        
        # Fallback to greedy selection based on scores
        selection = {}
        remaining_budget = constraints.max_budget
        
        for category, items in scored_categories.items():
            for item in items:  # Items are already sorted by score
                if item["price_lkr"] <= remaining_budget:
                    selection[category] = item
                    remaining_budget -= item["price_lkr"]
                    break
        
        return selection
    
    def _generate_optimization_reasoning(
        self, 
        selection: Dict[str, Dict], 
        constraints: OptimizationConstraints,
        scored_categories: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """Generate detailed reasoning for the optimization decisions"""
        
        total_cost = sum(item["price_lkr"] for item in selection.values())
        total_savings = sum(item.get("loyalty_savings", 0) for item in selection.values())
        
        store_distribution = {}
        for item in selection.values():
            store = item["website"]
            store_distribution[store] = store_distribution.get(store, 0) + 1
        
        max_delivery_time = max(
            self.store_configs[item["website"]].average_delivery_hours 
            for item in selection.values()
        ) if selection else 0
        
        alternatives_considered = sum(len(items) for items in scored_categories.values())
        
        return {
            "selection_summary": {
                "categories_optimized": len(selection),
                "total_cost": total_cost,
                "total_loyalty_savings": total_savings,
                "budget_utilization": (total_cost / constraints.max_budget) * 100,
                "estimated_delivery_time": max_delivery_time
            },
            "store_distribution": store_distribution,
            "optimization_metrics": {
                "alternatives_considered": alternatives_considered,
                "average_optimization_score": np.mean([
                    item["optimization_score"] for item in selection.values()
                ]),
                "constraints_satisfied": self._validate_constraints(selection, constraints)
            },
            "recommendations": self._generate_improvement_suggestions(selection, constraints)
        }
    
    def _validate_constraints(
        self, 
        selection: Dict[str, Dict], 
        constraints: OptimizationConstraints
    ) -> Dict[str, bool]:
        """Validate that the selection satisfies all constraints"""
        
        total_cost = sum(item["price_lkr"] for item in selection.values())
        max_delivery = max(
            self.store_configs[item["website"]].average_delivery_hours 
            for item in selection.values()
        ) if selection else 0
        
        return {
            "budget_satisfied": total_cost <= constraints.max_budget,
            "delivery_time_satisfied": (
                constraints.max_delivery_time_hours is None or 
                max_delivery <= constraints.max_delivery_time_hours
            ),
            "store_preferences_satisfied": self._check_store_preferences(selection, constraints),
            "one_per_category": len(selection) > 0
        }
    
    def _check_store_preferences(
        self, 
        selection: Dict[str, Dict], 
        constraints: OptimizationConstraints
    ) -> bool:
        """Check if store preferences are satisfied"""
        
        selected_stores = {item["website"] for item in selection.values()}
        
        # Check avoided stores
        if constraints.avoid_stores:
            if any(store in selected_stores for store in constraints.avoid_stores):
                return False
        
        # Check preferred stores (soft constraint)
        if constraints.preferred_stores:
            preferred_count = sum(
                1 for store in selected_stores 
                if store in constraints.preferred_stores
            )
            return preferred_count > 0
        
        return True
    
    def _generate_improvement_suggestions(
        self, 
        selection: Dict[str, Dict], 
        constraints: OptimizationConstraints
    ) -> List[str]:
        """Generate suggestions for improvement"""
        
        suggestions = []
        total_cost = sum(item["price_lkr"] for item in selection.values())
        
        if total_cost < constraints.max_budget * 0.8:
            suggestions.append(
                f"Budget underutilized by LKR {constraints.max_budget - total_cost:.2f}. "
                "Consider upgrading to premium options."
            )
        
        store_count = len({item["website"] for item in selection.values()})
        if store_count > 2:
            suggestions.append(
                "Multiple stores selected. Consider consolidating orders to reduce delivery fees."
            )
        
        return suggestions
