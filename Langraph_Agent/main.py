"""
Refactored Langraph Application for Product Search
with Agent-based Architecture, Tool Calling, and Personalization
"""
import os
from typing import Dict, Any

# Set up environment
from core.config import Config
os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY

from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

# Import custom agents and state
from core.state import ApplicationState
from core.user_profile import get_default_profile
from agents.keyword_extraction_agent import KeywordExtractionAgent
from agents.data_acquisition_agent import DataAcquisitionAgent
from agents.personalization_agent import PersonalizationAgent
from agents.loyalty_aggregator_agent import LoyaltyAggregatorAgent
from agents.output_formatting_agent import OutputFormattingAgent
from agents.logistics_agent import LogisticsAgent, UserLocation
from utils.profile_manager import UserProfileManager, print_profile_summary, interactive_profile_setup
from utils.location_utils import parse_user_location


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
        
        # Initialize agents
        self.keyword_agent = KeywordExtractionAgent(self.llm)
        self.data_agent = DataAcquisitionAgent(self.llm)
        self.personalization_agent = PersonalizationAgent(self.llm, self.user_profile)
        self.loyalty_agent = LoyaltyAggregatorAgent(self.llm)
        self.output_agent = OutputFormattingAgent()
        self.logistics_agent = LogisticsAgent(self.llm)
        
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
        graph_builder.add_node("format_output", self._format_output_node)
        
        # Add edges
        graph_builder.add_edge(START, "extract_keywords")
        graph_builder.add_edge("extract_keywords", "acquire_data")
        graph_builder.add_edge("acquire_data", "personalize")
        graph_builder.add_edge("personalize", "optimize_logistics")
        graph_builder.add_edge("optimize_logistics", "optimize_loyalty")
        graph_builder.add_edge("optimize_loyalty", "format_output")
        graph_builder.add_edge("format_output", END)
        
        return graph_builder.compile()
    
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
        
        return {
            "user_input": user_input,
            "keywords": keywords,
            "processing_stage": "keyword_extraction_complete"
        }
    
    def _acquire_data_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for data acquisition using tool calling"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Data Acquisition - Processing keywords: {state.get('keywords', [])}")
        
        keywords = state.get("keywords", [])
        if not keywords:
            return {"product_data": {}, "processing_stage": "data_acquisition_failed"}
        
        # Data acquisition with Web_scraper integration
        product_data = self.data_agent.acquire_data(keywords)
        
        return {
            "product_data": product_data,
            "processing_stage": "data_acquisition_complete"
        }
    
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
        
        return {
            "personalized_data": personalized_data,
            "personalization_summary": personalization_summary,
            "processing_stage": "personalization_complete"
        }
    
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
    
    def _format_output_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for output formatting"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Format Output - Processing results with loyalty optimization")
        
        # Use the best available data
        data_to_format = (
            state.get("loyalty_optimized_data") or 
            state.get("personalized_data") or 
            state.get("product_data", {})
        )
        
        personalization_summary = state.get("personalization_summary", {})
        loyalty_summary = state.get("loyalty_summary", {})
        logistics_summary = state.get("logistics_summary", {})
        logistics_optimization = state.get("logistics_optimization")
        user_location = state.get("user_location")
        
        formatted_output = self.output_agent.format_results(data_to_format)
        
        
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
            llm_recommendations = loyalty_summary.get("llm_recommendations", "")
            if llm_recommendations and not llm_recommendations.startswith("Unable"):
                loyalty_text += f"\n🎯 AI RECOMMENDATIONS:\n{llm_recommendations}\n"
            
            loyalty_text += "="*60 + "\n"
            formatted_output = formatted_output + loyalty_text
        elif loyalty_summary.get("error"):
            formatted_output = formatted_output + f"\n⚠️ Loyalty optimization failed: {loyalty_summary['error']}\n"
        
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
            "logistics_optimization": None,
            "logistics_summary": {},
            "formatted_output": "",
            "processing_stage": "initialized"
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
