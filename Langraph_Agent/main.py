"""
Langraph Application for Product Search with Multi Agent-based Architecture, Tool Calling, and Personalization
"""
import os
from typing import Dict, Any

# Set up environment
from core.config import Config
os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY
os.environ["LANGSMITH_API_KEY"] = Config.LANGSMITH_API_KEY
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

# Import custom agents and state
from core.state import ApplicationState
from core.user_profile import get_default_profile
from agents.keyword_extraction_agent import KeywordExtractionAgent
from agents.data_acquisition_agent import DataAcquisitionAgent
from agents.personalization_agent import PersonalizationAgent
from agents.loyalty_aggregator_agent import LoyaltyAggregatorAgent
from agents.budget_optimization_agent import BudgetOptimizationAgent, OptimizationConstraints
from agents.output_formatting_agent import OutputFormattingAgent
from agents.logistics_agent import LogisticsAgent, UserLocation
from utils.profile_manager import UserProfileManager, print_profile_summary, interactive_profile_setup
from utils.location_utils import parse_user_location

from langsmith import traceable
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")  # ok to keep

class ProductSearchOrchestrator:
    """Main orchestrator for the product search application"""
    
    def __init__(self, user_profile=None):
        """Initialize the orchestrator with LLM and agents"""
        self.llm = ChatGroq(
            model=Config.GROQ_MODEL,
            temperature=Config.GROQ_TEMPERATURE,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # Load user profile
        self.user_profile = user_profile or get_default_profile()
        self.profile_manager = UserProfileManager()
        
                # Initialize LLM
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model_name=Config.GROQ_MODEL,
            temperature=0.1
        )
        
        # Initialize agents
        self.keyword_agent = KeywordExtractionAgent(self.llm)
        self.data_agent = DataAcquisitionAgent(self.llm)
        self.personalization_agent = PersonalizationAgent(self.llm, user_profile)
        self.logistics_agent = LogisticsAgent(self.llm)
        self.loyalty_agent = LoyaltyAggregatorAgent(self.llm)
        self.budget_optimization_agent = BudgetOptimizationAgent()
        self.output_agent = OutputFormattingAgent()
        
        # Build the graph
        self.graph = self._build_graph()
        
        print("🛒 Product Search Orchestrator initialized with Personalization, Loyalty & Logistics")
    
    def _build_graph(self) -> StateGraph:
        """Build the Langraph workflow"""
        graph_builder = StateGraph(ApplicationState)
        
        # Add nodes
        graph_builder.add_node("extract_keywords", self._extract_keywords_node)
        graph_builder.add_node("acquire_data", self._acquire_data_node)
        graph_builder.add_node("personalize", self._personalize_node)
        graph_builder.add_node("optimize_loyalty", self._optimize_loyalty_node)
        graph_builder.add_node("optimize_logistics", self._optimize_logistics_node)
        graph_builder.add_node("optimize_budget", self._optimize_budget_node)
        graph_builder.add_node("format_output", self._format_output_node)
        
        # Add edges
        graph_builder.add_edge(START, "extract_keywords")
        graph_builder.add_edge("extract_keywords", "acquire_data")
        graph_builder.add_edge("acquire_data", "personalize")
        graph_builder.add_edge("personalize", "optimize_logistics")
        graph_builder.add_edge("optimize_logistics", "optimize_loyalty")
        graph_builder.add_edge("optimize_loyalty", "optimize_budget")
        graph_builder.add_edge("optimize_budget", "format_output")
        graph_builder.add_edge("format_output", END)
        
        return graph_builder.compile()

    @traceable(name="extract_keywords", tags=["titanstore", "node"])
    def _extract_keywords_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for keyword extraction"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Extract Keywords - Processing: '{state.get('user_input', '')}'")
        
        user_input = state.get("user_input", "")
        if not user_input and state.get("messages"):
            last_msg = state["messages"][-1]
            if hasattr(last_msg, "content"):
                user_input = last_msg.content
            elif isinstance(last_msg, dict) and "content" in last_msg:
                user_input = last_msg["content"]
            else:
                user_input = str(last_msg)
        
        keywords = self.keyword_agent.extract_keywords(user_input)
        
        # Print step details
        print(f"\n🔍 STEP 1: KEYWORD EXTRACTION")
        print(f"   User Query: '{user_input}'")
        print(f"   Extracted Keywords: {keywords}")
        print(f"   Keywords Count: {len(keywords)}")
        
        return {
            "user_input": user_input,
            "keywords": keywords,
            "processing_stage": "keyword_extraction_complete"
        }

    @traceable(name="acquire_data", tags=["titanstore", "node"])
    def _acquire_data_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for data acquisition using tool calling"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Data Acquisition - Processing keywords: {state.get('keywords', [])}")
        
        keywords = state.get("keywords", [])
        if not keywords:
            return {"product_data": {}, "processing_stage": "data_acquisition_failed"}
        
        # Data acquisition with Web_scraper integration
        product_data = self.data_agent.acquire_data(keywords)
        
        # Print step details
        print(f"\n📦 STEP 2: DATA ACQUISITION")
        print(f"   Keywords Processed: {keywords}")
        total_items = sum(len(items) for items in product_data.values())
        print(f"   Total Items Retrieved: {total_items}")
        print(f"   Items by Category:")
        for keyword, items in product_data.items():
            print(f"     • {keyword}: {len(items)} items")
            # Show first few items as examples
            for i, item in enumerate(items[:2]):  # Show first 2 items
                print(f"       {i+1}. {item.get('title', 'Unknown')} - LKR {item.get('price_lkr', 0)} ({item.get('website', 'Unknown')})")
            if len(items) > 2:
                print(f"       ... and {len(items) - 2} more items")
        
        return {
            "product_data": product_data,
            "processing_stage": "data_acquisition_complete"
        }

    @traceable(name="personalize", tags=["titanstore", "node"])
    def _personalize_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for personalizing items based on user preferences"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Personalization - Processing items for user: {self.user_profile.user_id}")
        
        product_data = state.get("product_data", {})
        if not product_data:
            return {
                "personalized_data": {},
                "personalization_summary": {"error": "No product data to personalize"},
                "processing_stage": "personalization_failed"
            }
        
        # NEW APPROACH: Personalize per keyword to ensure at least 1 item per category
        personalized_data = {}
        total_original_items = 0
        total_final_items = 0
        all_personalization_steps = []
        combined_budget_summary = {"total_cost": 0.0, "budget_limit": self.user_profile.budget_limit_lkr}
        
        for keyword, keyword_items in product_data.items():
            if not keyword_items:
                personalized_data[keyword] = []
                continue
                
            total_original_items += len(keyword_items)
            
            if Config.DEBUG_MODE:
                print(f"[PERSONALIZATION] Processing keyword '{keyword}' with {len(keyword_items)} items")
            
            # Personalize items for this specific keyword
            personalized_items, keyword_summary = self.personalization_agent.personalize_items(keyword_items)
            
            # GUARANTEE: Ensure at least 1 item remains for this keyword
            if not personalized_items and keyword_items:
                if Config.DEBUG_MODE:
                    print(f"[PERSONALIZATION] No items passed filters for '{keyword}' - keeping best item")
                # Keep the first item as fallback (could be enhanced with scoring later)
                personalized_items = [keyword_items[0]]
                keyword_summary["fallback_applied"] = True
                keyword_summary["fallback_reason"] = "Ensured minimum 1 item per keyword"
            
            personalized_data[keyword] = personalized_items
            total_final_items += len(personalized_items)
            
            # Accumulate personalization info
            if "personalization_steps" in keyword_summary:
                all_personalization_steps.extend([f"{keyword}: {step}" for step in keyword_summary["personalization_steps"]])
            
            if "budget_summary" in keyword_summary:
                combined_budget_summary["total_cost"] += keyword_summary["budget_summary"].get("total_cost", 0.0)
        
        # Calculate remaining budget
        combined_budget_summary["remaining_budget"] = (
            combined_budget_summary["budget_limit"] - combined_budget_summary["total_cost"]
        )
        
        # Create comprehensive personalization summary
        personalization_summary = {
            "original_items_count": total_original_items,
            "final_items_count": total_final_items,
            "personalization_steps": all_personalization_steps,
            "budget_summary": combined_budget_summary,
            "user_profile_applied": self.user_profile.user_id,
            "keywords_processed": list(product_data.keys()),
            "minimum_items_guaranteed": True
        }
        
        if Config.DEBUG_MODE:
            print(f"[PERSONALIZATION] Summary: {total_original_items} → {total_final_items} items across {len(product_data)} keywords")
        
        # Print step details
        print(f"\n👤 STEP 3: PERSONALIZATION")
        print(f"   User Profile: {self.user_profile.user_id}")
        print(f"   Budget Limit: LKR {self.user_profile.budget_limit_lkr}")
        print(f"   Original Items: {total_original_items}")
        print(f"   Final Items: {total_final_items}")
        print(f"   Items Removed: {total_original_items - total_final_items}")
        print(f"   Personalized Items by Category:")
        for keyword, items in personalized_data.items():
            print(f"     • {keyword}: {len(items)} items")
            # Show selected items
            for i, item in enumerate(items[:3]):  # Show first 3 items
                print(f"       {i+1}. {item.get('title', 'Unknown')} - LKR {item.get('price_lkr', 0)} ({item.get('website', 'Unknown')})")
            if len(items) > 3:
                print(f"       ... and {len(items) - 3} more items")
        
        return {
            "personalized_data": personalized_data,
            "personalization_summary": personalization_summary,
            "processing_stage": "personalization_complete"
        }

    @traceable(name="optimize_loyalty", tags=["titanstore", "node"])
    def _optimize_loyalty_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for optimizing loyalty benefits and discounts"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Loyalty Optimization - Processing discount optimization")
        
        # Use logistics optimized data if available, otherwise fall back to personalized data
        logistics_optimization = state.get("logistics_optimization")
        if logistics_optimization and hasattr(logistics_optimization, 'optimized_items_by_category'):
            # Use the logistics-filtered items
            optimized_items_by_category = logistics_optimization.optimized_items_by_category
            all_items = []
            for category, items in optimized_items_by_category.items():
                all_items.extend(items)
        else:
            # Fall back to personalized data
            personalized_data = state.get("personalized_data", {})
            if not personalized_data:
                return {
                    "loyalty_optimized_data": {},
                    "loyalty_summary": {"error": "No data available for loyalty optimization"},
                    "processing_stage": "loyalty_optimization_failed"
                }
            
            all_items = []
            for keyword, items in personalized_data.items():
                all_items.extend(items)
        
        if not all_items:
            return {
                "loyalty_optimized_data": state.get("personalized_data", {}),
                "loyalty_summary": {"message": "No items to optimize"},
                "processing_stage": "loyalty_optimization_skipped"
            }
        
        try:
            # Apply loyalty optimization to logistics-filtered items
            optimized_items, loyalty_summary = self.loyalty_agent.optimize_loyalty_benefits(all_items)
            
            if Config.DEBUG_MODE:
                total_savings = loyalty_summary.get("total_savings", 0)
                print(f"[LOYALTY] Optimization complete: LKR {total_savings:.2f} total savings")
            
            # Print step details
            print(f"\n💳 STEP 5: LOYALTY OPTIMIZATION")
            print(f"   Items Processed: {len(all_items)}")
            print(f"   Stores Analyzed: {loyalty_summary.get('stores_analyzed', 0)}")
            print(f"   Total Original Cost: LKR {loyalty_summary.get('total_original_cost', 0):.2f}")
            print(f"   Total Optimized Cost: LKR {loyalty_summary.get('total_optimized_cost', 0):.2f}")
            print(f"   Total Savings: LKR {loyalty_summary.get('total_savings', 0):.2f}")
            print(f"   Savings Percentage: {loyalty_summary.get('savings_percentage', 0)}%")
            
            # Show store-by-store breakdown
            store_optimizations = loyalty_summary.get("store_optimizations", [])
            if store_optimizations:
                print(f"   Store Breakdown:")
                for store_opt in store_optimizations:
                    store_name = store_opt.get("store_name", "Unknown")
                    store_savings = store_opt.get("savings", 0)
                    items_count = store_opt.get("items_count", 0)
                    print(f"     • {store_name}: {items_count} items, LKR {store_savings:.2f} savings")
            
            return {
                "loyalty_optimized_data": state.get("personalized_data", {}),  # Keep original structure for consistency
                "loyalty_summary": loyalty_summary,
                "processing_stage": "loyalty_optimization_complete"
            }
            
        except Exception as e:
            if Config.DEBUG_MODE:
                print(f"[LOYALTY] Error during optimization: {str(e)}")
            
            return {
                "loyalty_optimized_data": state.get("personalized_data", {}),
                "loyalty_summary": {"error": str(e)},
                "processing_stage": "loyalty_optimization_failed"
            }

    @traceable(name="optimize_logistics", tags=["titanstore", "node"])
    def _optimize_logistics_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for filtering items based on delivery distance"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Logistics Filtering - Processing distance-based filtering")
        
        # Use personalized data for logistics filtering
        personalized_data = state.get("personalized_data", {})
        if not personalized_data:
            return {
                "logistics_optimization": {"error": "No personalized data for logistics filtering"},
                "logistics_summary": {"error": "No personalized data for logistics filtering"},
                "processing_stage": "logistics_filtering_failed"
            }
        
        # Extract user location from profile or prompt for it
        user_location = None
        
        # Check if location is in user profile
        if hasattr(self.user_profile, 'location') and self.user_profile.location:
            user_location = parse_user_location(self.user_profile.location)
        
        # If no location in profile, use default Colombo location for demo
        if not user_location:
            if Config.DEBUG_MODE:
                print("[LOGISTICS] No user location found, using default Colombo location")
            user_location = UserLocation(
                latitude=6.9271,
                longitude=79.8612,
                address="Colombo, Sri Lanka (Default)",
                city="Colombo",
                district="Colombo",
                province="Western"
            )
        
        # Apply distance-based filtering using logistics agent
        try:
            # Set maximum distance threshold (can be made configurable)
            max_distance_km = 100.0  # 100km threshold
            
            filtering_result = self.logistics_agent.filter_by_distance(
                user_location, 
                personalized_data, 
                max_distance_km
            )
            
            if Config.DEBUG_MODE:
                summary = filtering_result.get("filtering_summary", {})
                print(f"[LOGISTICS] Filtering complete: {summary.get('items_before_filtering', 0)} → {summary.get('items_after_filtering', 0)} items")
            
            # Print step details
            logistics_optimization = filtering_result.get("logistics_optimization")
            logistics_summary = filtering_result.get("filtering_summary", {})
            
            print(f"\n🚚 STEP 4: LOGISTICS FILTERING")
            print(f"   User Location: {user_location.address}")
            print(f"   Distance Threshold: {max_distance_km}km")
            print(f"   Items Before: {logistics_summary.get('items_before_filtering', 0)}")
            print(f"   Items After: {logistics_summary.get('items_after_filtering', 0)}")
            print(f"   Items Removed: {logistics_summary.get('items_removed', 0)}")
            
            if logistics_optimization and hasattr(logistics_optimization, 'optimized_items_by_category'):
                print(f"   Logistics Filtered Items by Category:")
                for category, items in logistics_optimization.optimized_items_by_category.items():
                    print(f"     • {category}: {len(items)} items")
                    # Show selected items
                    for i, item in enumerate(items[:2]):  # Show first 2 items
                        print(f"       {i+1}. {item.get('title', 'Unknown')} - LKR {item.get('price_lkr', 0)} ({item.get('website', 'Unknown')})")
                    if len(items) > 2:
                        print(f"       ... and {len(items) - 2} more items")
            
            return {
                "logistics_optimization": filtering_result.get("logistics_optimization"),
                "logistics_summary": filtering_result.get("filtering_summary", {}),
                "user_location": user_location,
                "processing_stage": "logistics_filtering_complete"
            }
            
        except Exception as e:
            if Config.DEBUG_MODE:
                print(f"[LOGISTICS] Error during filtering: {str(e)}")
            
            return {
                "logistics_optimization": None,
                "logistics_summary": {"error": str(e)},
                "user_location": user_location,
                "processing_stage": "logistics_filtering_failed"
            }

    @traceable(name="optimize_budget", tags=["titanstore", "node"])
    def _optimize_budget_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for budget optimization - selects best item per category"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Budget Optimization - Selecting optimal items per category")
        
        loyalty_optimized_data = state.get("loyalty_optimized_data", {})
        
        if not loyalty_optimized_data:
            print("⚠️ No loyalty optimized data to process")
            return {
                "budget_optimized_data": {},
                "budget_optimization_summary": {"error": "No data to optimize"},
                "processing_stage": "budget_optimization_failed"
            }
        
        # Create optimization constraints from user profile
        user_profile = state.get('user_profile', {})
        constraints = OptimizationConstraints(
            max_budget=user_profile.get('budget_limit', 5000.0),
            max_delivery_time_hours=48.0,  # 2 days max
            preferred_stores=None,
            avoid_stores=None,
            priority_weights={
                "price": 0.4,
                "delivery_time": 0.25,
                "quality": 0.20,
                "loyalty_savings": 0.15
            }
        )
        
        # Get original user query for context
        user_query = state.get("user_input", "")
        
        try:
            # Run budget optimization
            optimization_result = self.budget_optimization_agent.optimize_item_selection(
                loyalty_optimized_data, constraints, user_query
            )
            
            if "error" in optimization_result:
                print(f"❌ Budget optimization failed: {optimization_result['error']}")
                return {
                    "budget_optimized_data": {},
                    "budget_optimization_summary": optimization_result,
                    "processing_stage": "budget_optimization_failed"
                }
            
            optimized_selection = optimization_result.get("optimized_selection", {})
            optimization_summary = optimization_result.get("optimization_summary", {})
            
            # Convert format: {category: item} -> {category: [item]} for output formatter
            budget_optimized_data = {}
            for category, item in optimized_selection.items():
                budget_optimized_data[category] = [item]  # Wrap single item in list
            
            if Config.DEBUG_MODE:
                print(f"[BUDGET] Optimization complete: {len(optimized_selection)} items selected")
                print(f"[BUDGET] Total cost: LKR {optimization_result.get('total_cost', 0):.2f}")
                print(f"[BUDGET] Delivery time: {optimization_result.get('total_delivery_time', 0):.1f}h")
            
            # Print step details
            print(f"\n🎯 STEP 6: BUDGET OPTIMIZATION")
            print(f"   Optimization Method: Linear Programming + Multi-Criteria")
            print(f"   Categories Input: {len(loyalty_optimized_data)}")
            print(f"   Categories Optimized: {len(optimized_selection)}")
            print(f"   Final Selection (One per category):")
            for category, item in optimized_selection.items():
                print(f"     • {category}: {item.get('title', 'Unknown')} - LKR {item.get('price_lkr', 0)} ({item.get('website', 'Unknown')})")
            print(f"   Total Cost: LKR {optimization_result.get('total_cost', 0):.2f}")
            print(f"   Budget Limit: LKR {constraints.max_budget:.2f}")
            print(f"   Budget Used: {(optimization_result.get('total_cost', 0) / constraints.max_budget * 100):.1f}%")
            print(f"   Estimated Delivery: {optimization_result.get('total_delivery_time', 0):.1f} hours")
            
            return {
                "budget_optimized_data": budget_optimized_data,
                "budget_optimization_summary": optimization_summary,
                "processing_stage": "budget_optimization_complete"
            }
            
        except Exception as e:
            print(f"❌ Budget optimization failed: {e}")
            return {
                "budget_optimized_data": {},
                "budget_optimization_summary": {"error": str(e)},
                "processing_stage": "budget_optimization_failed"
            }

    @traceable(name="format_output", tags=["titanstore", "node"])
    def _format_output_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for output formatting"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Format Output - Processing results with loyalty optimization")
        
        # Use the best available data - prioritize budget optimized
        data_to_format = (
            state.get("budget_optimized_data") or
            state.get("loyalty_optimized_data") or 
            state.get("personalized_data") or 
            state.get("product_data", {})
        )
        
        personalization_summary = state.get("personalization_summary", {})
        loyalty_summary = state.get("loyalty_summary", {})
        budget_optimization_summary = state.get("budget_optimization_summary", {})
        logistics_summary = state.get("logistics_summary", {})
        logistics_optimization = state.get("logistics_optimization")
        user_location = state.get("user_location")
        
        formatted_output = self.output_agent.format_results(data_to_format)
        
        # Print step details
        print(f"\n📋 STEP 7: OUTPUT FORMATTING")
        print(f"   Data Source: {type(data_to_format).__name__ if hasattr(type(data_to_format), '__name__') else 'Dictionary'}")
        print(f"   Categories in Final Output: {len(data_to_format) if data_to_format else 0}")
        if data_to_format:
            total_final_items = sum(len(items) if isinstance(items, list) else 1 for items in data_to_format.values())
            total_final_cost = 0
            print(f"   Final Items Summary:")
            for category, items in data_to_format.items():
                if isinstance(items, list):
                    if items:  # Non-empty list
                        item = items[0]  # Budget optimization should give single item per category
                        cost = item.get('price_lkr', 0)
                        total_final_cost += cost
                        print(f"     • {category}: {item.get('title', 'Unknown')} - LKR {cost}")
                else:  # Single item
                    cost = items.get('price_lkr', 0) if items else 0
                    total_final_cost += cost
                    print(f"     • {category}: {items.get('title', 'Unknown') if items else 'None'} - LKR {cost}")
            print(f"   Total Final Cost: LKR {total_final_cost:.2f}")
            print(f"   Total Final Items: {total_final_items}")
        
        # Add budget optimization final recommendations if available
        if state.get("budget_optimized_data"):
            budget_data = state.get("budget_optimized_data", {})
            budget_summary = state.get("budget_optimization_summary", {})
            
            recommendations_text = "\n" + "="*70 + "\n"
            recommendations_text += "🎯 FINAL RECOMMENDATIONS - OPTIMIZED SELECTION\n"
            recommendations_text += "="*70 + "\n"
            recommendations_text += "✅ **ORDER THESE ITEMS** (One optimal item per category):\n\n"
            
            total_cost = 0
            recommendation_count = 0
            
            for category, items in budget_data.items():
                if items:  # items is a list with one item
                    item = items[0]  # Get the single recommended item
                    recommendation_count += 1
                    total_cost += item.get('price_lkr', 0)
                    
                    recommendations_text += f"📦 **{category.upper()}**:\n"
                    recommendations_text += f"   🏆 {item.get('title', 'Unknown Item')}\n"
                    recommendations_text += f"   💰 Price: LKR {item.get('price_lkr', 0):.2f}\n"
                    recommendations_text += f"   🌐 Store: {item.get('website', 'Unknown')}\n"
                    recommendations_text += f"   🔗 URL: {item.get('url', 'N/A')}\n"
                    if item.get('kg_enhanced'):
                        recommendations_text += f"   🧠 Enhanced via Knowledge Graph\n"
                    recommendations_text += "\n"
            
            recommendations_text += "-" * 70 + "\n"
            recommendations_text += f"🛒 **TOTAL ORDER SUMMARY**:\n"
            recommendations_text += f"   • Items to Order: {recommendation_count}\n"
            recommendations_text += f"   • Total Cost: LKR {total_cost:.2f}\n"
            recommendations_text += f"   • Optimization Method: Linear Programming + Multi-Criteria\n"
            if budget_summary.get('total_delivery_time'):
                recommendations_text += f"   • Estimated Delivery: {budget_summary.get('total_delivery_time', 0):.1f} hours\n"
            recommendations_text += "="*70 + "\n"
            
            formatted_output = recommendations_text + formatted_output
        
        
        # Add personalization summary to output
        if personalization_summary and not personalization_summary.get("error"):
            summary_text = "\n" + "="*60 + "\n"
            summary_text += "PERSONALIZATION SUMMARY\n"
            summary_text += "="*60 + "\n"
            summary_text += f"User Profile: {personalization_summary.get('user_profile_applied', 'Unknown')}\n"
            summary_text += f"Original Items: {personalization_summary.get('original_items_count', 0)}\n"
            summary_text += f"Final Items: {personalization_summary.get('final_items_count', 0)}\n"
            summary_text += f"Keywords Processed: {len(personalization_summary.get('keywords_processed', []))}\n"
            summary_text += f"Minimum Items Guaranteed: {personalization_summary.get('minimum_items_guaranteed', False)}\n"
            
            if 'budget_summary' in personalization_summary:
                budget = personalization_summary['budget_summary']
                summary_text += f"Total Cost: LKR {budget.get('total_cost', 0):.2f}\n"
                summary_text += f"Budget Limit: LKR {budget.get('budget_limit', 0):.2f}\n"
                summary_text += f"Remaining Budget: LKR {budget.get('remaining_budget', 0):.2f}\n"
            
            if 'personalization_steps' in personalization_summary:
                summary_text += "\nPersonalization Steps:\n"
                for step in personalization_summary['personalization_steps']:
                    summary_text += f"  • {step}\n"
            
            summary_text += "="*60 + "\n"
            formatted_output = summary_text + formatted_output
        elif personalization_summary.get("error"):
            formatted_output = f"⚠️ Personalization failed: {personalization_summary['error']}\n\n" + formatted_output

        # Add logistics filtering summary to output FIRST (since it happens before loyalty)
        if logistics_optimization and logistics_summary and not logistics_summary.get("error"):
            logistics_text = "\n" + "="*60 + "\n"
            logistics_text += "� LOGISTICS OPTIMIZATION SUMMARY\n"
            logistics_text += "="*60 + "\n"
            
            if user_location:
                logistics_text += f"User Location: {user_location.address}\n"
                logistics_text += f"City: {user_location.city}, {user_location.district}\n"
                logistics_text += f"Province: {user_location.province}\n\n"
            
            # Add logistics optimization details
            if hasattr(logistics_optimization, 'optimization_summary'):
                summary = logistics_optimization.optimization_summary
                logistics_text += f"🏪 STORE OPTIMIZATION:\n"
                logistics_text += f"Stores Within Range: {summary.get('stores_within_range', 0)}\n"
                logistics_text += f"Average Distance: {summary.get('average_distance_km', 0):.1f}km\n"
                logistics_text += f"Fastest Delivery: {summary.get('fastest_delivery_hours', 0)}h\n"
                logistics_text += f"Total Delivery Cost: LKR {summary.get('total_delivery_cost', 0):.2f}\n"
            
            logistics_text += "="*60 + "\n"
            formatted_output = formatted_output + logistics_text
        elif logistics_summary.get("error"):
            formatted_output = formatted_output + f"\n⚠️ Logistics optimization failed: {logistics_summary['error']}\n"

        # Add loyalty optimization summary AFTER logistics (since loyalty happens after logistics)
        if loyalty_summary and not loyalty_summary.get("error"):
            loyalty_text = "\n" + "="*60 + "\n"
            loyalty_text += "💳 LOYALTY & DISCOUNT OPTIMIZATION\n"
            loyalty_text += "="*60 + "\n"
            
            total_savings = loyalty_summary.get("total_savings", 0)
            total_original = loyalty_summary.get("total_original_cost", 0)
            total_optimized = loyalty_summary.get("total_optimized_cost", 0)
            savings_percentage = loyalty_summary.get("savings_percentage", 0)
            
            loyalty_text += f"Original Total Cost: LKR {total_original:.2f}\n"
            loyalty_text += f"Optimized Total Cost: LKR {total_optimized:.2f}\n"
            loyalty_text += f"Total Savings: LKR {total_savings:.2f} ({savings_percentage}%)\n"
            loyalty_text += f"Stores Analyzed: {loyalty_summary.get('stores_analyzed', 0)}\n"
            
            # Add store optimizations
            store_optimizations = loyalty_summary.get("store_optimizations", [])
            if store_optimizations:
                loyalty_text += f"\n📊 STORE-BY-STORE BREAKDOWN:\n"
                for store_opt in store_optimizations:
                    store_name = store_opt.get("store_name", "Unknown")
                    store_savings = store_opt.get("savings", 0)
                    items_count = store_opt.get("items_count", 0)
                    loyalty_text += f"  • {store_name}: {items_count} items, LKR {store_savings:.2f} savings\n"
            
            # Add LLM recommendations if available
            llm_recommendations = loyalty_summary.get("llm_recommendations", {})
            if isinstance(llm_recommendations, dict) and llm_recommendations.get("strategic_recommendations"):
                loyalty_text += f"\n🎯 AI RECOMMENDATIONS:\n"
                
                # Strategic recommendations
                if llm_recommendations.get("strategic_recommendations"):
                    loyalty_text += "**Strategic Recommendations:**\n"
                    for rec in llm_recommendations["strategic_recommendations"]:
                        loyalty_text += f"• {rec}\n"
                
                # Alternative strategies
                if llm_recommendations.get("alternative_strategies"):
                    loyalty_text += "\n**Alternative Strategies:**\n"
                    for strategy in llm_recommendations["alternative_strategies"]:
                        loyalty_text += f"• {strategy}\n"
                
                # Store ranking
                if llm_recommendations.get("store_ranking"):
                    loyalty_text += "\n**Store Priority Ranking:**\n"
                    for store_info in llm_recommendations["store_ranking"]:
                        loyalty_text += f"{store_info['rank']}. {store_info['store']}: {store_info['reason']}\n"
                
                # Key insights
                if llm_recommendations.get("key_insights"):
                    loyalty_text += "\n**Key Insights:**\n"
                    for insight in llm_recommendations["key_insights"]:
                        loyalty_text += f"• {insight}\n"
                        
            elif isinstance(llm_recommendations, str) and llm_recommendations and not llm_recommendations.startswith("Unable"):
                loyalty_text += f"\n🎯 AI RECOMMENDATIONS:\n{llm_recommendations}\n"
            
            loyalty_text += "="*60 + "\n"
            formatted_output = formatted_output + loyalty_text
        elif loyalty_summary.get("error"):
            formatted_output = formatted_output + f"\n⚠️ Loyalty optimization failed: {loyalty_summary['error']}\n"

        # 4. Add budget optimization summary LAST (final selection)
        if budget_optimization_summary and not budget_optimization_summary.get("error"):
            budget_text = "\n" + "="*60 + "\n"
            budget_text += "🎯 FINAL BUDGET OPTIMIZATION\n"
            budget_text += "="*60 + "\n"
            
            selection_summary = budget_optimization_summary.get("selection_summary", {})
            optimization_metrics = budget_optimization_summary.get("optimization_metrics", {})
            
            budget_text += f"Categories Optimized: {selection_summary.get('categories_optimized', 0)}\n"
            budget_text += f"Final Total Cost: LKR {selection_summary.get('total_cost', 0):.2f}\n"
            budget_text += f"Budget Utilization: {selection_summary.get('budget_utilization', 0):.1f}%\n"
            budget_text += f"Estimated Delivery: {selection_summary.get('estimated_delivery_time', 0):.1f} hours\n"
            
            if selection_summary.get('total_loyalty_savings', 0) > 0:
                budget_text += f"Total Loyalty Savings: LKR {selection_summary['total_loyalty_savings']:.2f}\n"
            
            # Store distribution
            store_distribution = budget_optimization_summary.get("store_distribution", {})
            if store_distribution:
                budget_text += f"\n📊 FINAL STORE SELECTION:\n"
                for store, count in store_distribution.items():
                    budget_text += f"  • {store}: {count} item(s)\n"
            
            # Optimization metrics
            if optimization_metrics:
                budget_text += f"\n⚡ OPTIMIZATION PERFORMANCE:\n"
                budget_text += f"Alternatives Considered: {optimization_metrics.get('alternatives_considered', 0)}\n"
                budget_text += f"Average Score: {optimization_metrics.get('average_optimization_score', 0):.3f}\n"
                
                constraints_satisfied = optimization_metrics.get('constraints_satisfied', {})
                if constraints_satisfied:
                    budget_text += f"Budget Constraint: {'✅' if constraints_satisfied.get('budget_satisfied') else '❌'}\n"
                    budget_text += f"Delivery Time: {'✅' if constraints_satisfied.get('delivery_time_satisfied') else '❌'}\n"
            
            # Recommendations
            recommendations = budget_optimization_summary.get("recommendations", [])
            if recommendations:
                budget_text += f"\n💡 OPTIMIZATION SUGGESTIONS:\n"
                for rec in recommendations:
                    budget_text += f"  • {rec}\n"
            
            budget_text += "="*60 + "\n"
            formatted_output = formatted_output + budget_text
        elif budget_optimization_summary.get("error"):
            formatted_output = formatted_output + f"\n⚠️ Budget optimization failed: {budget_optimization_summary['error']}\n"

        
        # Add logistics filtering summary to output
        if logistics_summary and not logistics_summary.get("error"):
            logistics_text = "\n" + "="*60 + "\n"
            logistics_text += "LOGISTICS FILTERING SUMMARY\n"
            logistics_text += "="*60 + "\n"
            
            if user_location:
                logistics_text += f"User Location: {user_location.address}\n"
                logistics_text += f"City: {user_location.city}, {user_location.district}\n"
                logistics_text += f"Province: {user_location.province}\n\n"
            
            logistics_text += f"� DISTANCE-BASED FILTERING:\n"
            logistics_text += f"Categories Processed: {logistics_summary.get('total_categories', 0)}\n"
            logistics_text += f"Items Before Filtering: {logistics_summary.get('items_before_filtering', 0)}\n"
            logistics_text += f"Items After Filtering: {logistics_summary.get('items_after_filtering', 0)}\n"
            logistics_text += f"Items Removed (Too Far): {logistics_summary.get('items_removed', 0)}\n"
            logistics_text += f"Distance Threshold: {logistics_summary.get('distance_threshold_km', 100)}km\n"
            logistics_text += f"Single-Item Categories Kept: {logistics_summary.get('single_item_categories_kept', 0)}\n"
            logistics_text += f"Categories with Filtering Applied: {logistics_summary.get('categories_filtered', 0)}\n"

        
        # Print the output
        print(formatted_output)
        
        return {
            "formatted_output": formatted_output,
            "processing_stage": "output_formatting_complete"
        }
    
    def process_query(self, user_query: str) -> ApplicationState:
        """
        Process a user query through the entire pipeline with personalization
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Final application state
        """
        initial_state = {
            "messages": [{"role": "user", "content": user_query}],
            "user_input": user_query,
            "keywords": [],
            "product_data": {},
            "personalized_data": {},
            "personalization_summary": {},
            "loyalty_optimized_data": {},
            "loyalty_summary": {},
            "budget_optimized_data": {},
            "budget_optimization_summary": {},
            "logistics_optimization": None,
            "logistics_summary": {},
            "formatted_output": "",
            "processing_stage": "initialized",
            "user_profile": {
                "budget_limit": self.user_profile.budget_limit_lkr,
                "max_delivery_time": 48.0,
                "preferred_stores": getattr(self.user_profile.delivery_preferences, 'preferred_stores', [])
            }
        }
        
        if Config.DEBUG_MODE:
            print(f"[ORCHESTRATOR] Processing query with personalization and loyalty optimization: '{user_query}'")
        
        result = self.graph.invoke(initial_state)
        return result


def main():
    """Main entry point with personalization features"""
    print("🛒 Product Search Assistant with Personalization & Loyalty Optimization")
    print("=" * 70)
    
    # Initialize profile manager
    profile_manager = UserProfileManager()
    
    print("\nWelcome! Let's set up your personalized shopping experience.")
    print("1. 👤 Create/Load User Profile")
    print("2. 🔍 Start Search with Default Profile")
    
    choice = input("\nSelect option (1-2): ").strip()
    
    user_profile = None
    if choice == "1":
        user_profile = interactive_profile_setup()
        print_profile_summary(user_profile)
    else:
        user_profile = get_default_profile()
        print("Using default profile for demonstration...")
    
    # Initialize orchestrator with user profile
    orchestrator = ProductSearchOrchestrator(user_profile)
    
    print("\n" + "=" * 70)
    print("🛒 Personalized Product Search with Loyalty Optimization Ready!")
    print("Your preferences and loyalty benefits will be applied to all search results.")
    print("-" * 70)
    
    while True:
        try:
            print("\nOptions:")
            print("1. 🔍 Search for products")
            print("2. 👤 Update User Profile") 
            print("3. 📊 View Current Profile")
            print("4. 🚪 Exit")
            
            option = input("\nSelect option (1-4): ").strip()
            
            if option == "1":
                user_input = input("\nEnter your product search query: ")
                if user_input.strip():
                    # Process the query with personalization
                    result = orchestrator.process_query(user_input)
                    
                    if Config.DEBUG_MODE:
                        print(f"\n[DEBUG] Final processing stage: {result.get('processing_stage')}")
            
            elif option == "2":
                new_profile = profile_manager.interactive_profile_setup()
                if new_profile:
                    orchestrator.user_profile = new_profile
                    orchestrator.personalization_agent.user_profile = new_profile
                    print("✅ Profile updated successfully!")
            
            elif option == "3":
                print_profile_summary(orchestrator.user_profile)
            
            elif option == "4":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid option. Please select 1-4.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if Config.DEBUG_MODE:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
