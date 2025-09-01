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
from agents.output_formatting_agent import OutputFormattingAgent
from utils.profile_manager import UserProfileManager, print_profile_summary
from agents.knowledge_graph_agent import KnowledgeGraphAgent


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
        self.output_agent = OutputFormattingAgent()
        
        # Build the graph
        self.graph = self._build_graph()
        
        print("🧠 Product Search Orchestrator initialized with Knowledge Graph integration")
    
    def _build_graph(self) -> StateGraph:
        """Build the Langraph workflow"""
        graph_builder = StateGraph(ApplicationState)
        
        # Add nodes
        graph_builder.add_node("extract_keywords", self._extract_keywords_node)
        graph_builder.add_node("acquire_data", self._acquire_data_node)
        graph_builder.add_node("personalize", self._personalize_node)
        graph_builder.add_node("format_output", self._format_output_node)
        
        # Add edges
        graph_builder.add_edge(START, "extract_keywords")
        graph_builder.add_edge("extract_keywords", "acquire_data")
        graph_builder.add_edge("acquire_data", "personalize")
        graph_builder.add_edge("personalize", "format_output")
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
        """Node for data acquisition using tool calling with knowledge graph enhancement"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Data Acquisition - Processing keywords: {state.get('keywords', [])}")
        
        keywords = state.get("keywords", [])
        if not keywords:
            return {"product_data": {}, "processing_stage": "data_acquisition_failed"}
        
        # Data acquisition now includes knowledge graph enhancement
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
        
        # Flatten all items from all keywords
        all_items = []
        for keyword_items in product_data.values():
            all_items.extend(keyword_items)
        
        # Personalize items
        personalized_items, personalization_summary = self.personalization_agent.personalize_items(all_items)
        
        # Group personalized items back by keywords (best effort)
        personalized_data = {}
        for keyword in product_data.keys():
            # Find items that match this keyword
            keyword_items = [
                item for item in personalized_items 
                if keyword.lower() in item.get('title', '').lower()
            ]
            personalized_data[keyword] = keyword_items
        
        # Add any remaining items to the first keyword
        assigned_items = set()
        for items in personalized_data.values():
            for item in items:
                assigned_items.add(item.get('title', ''))
        
        remaining_items = [
            item for item in personalized_items 
            if item.get('title', '') not in assigned_items
        ]
        
        if remaining_items and personalized_data:
            first_keyword = list(personalized_data.keys())[0]
            personalized_data[first_keyword].extend(remaining_items)
        
        return {
            "personalized_data": personalized_data,
            "personalization_summary": personalization_summary,
            "processing_stage": "personalization_complete"
        }
    
    def _format_output_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for output formatting"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Format Output - Processing personalized results")
        
        # Use personalized data if available, otherwise fall back to original product data
        data_to_format = state.get("personalized_data", state.get("product_data", {}))
        personalization_summary = state.get("personalization_summary", {})
        
        formatted_output = self.output_agent.format_results(data_to_format)
        
        # Add personalization summary to output
        if personalization_summary and not personalization_summary.get("error"):
            summary_text = "\n" + "="*60 + "\n"
            summary_text += "PERSONALIZATION SUMMARY\n"
            summary_text += "="*60 + "\n"
            summary_text += f"User Profile: {personalization_summary.get('user_profile_applied', 'Unknown')}\n"
            summary_text += f"Original Items: {personalization_summary.get('original_items_count', 0)}\n"
            summary_text += f"Final Items: {personalization_summary.get('final_items_count', 0)}\n"
            
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
            "formatted_output": "",
            "processing_stage": "initialized"
        }
        
        if Config.DEBUG_MODE:
            print(f"[ORCHESTRATOR] Processing query with personalization: '{user_query}'")
        
        result = self.graph.invoke(initial_state)
        return result
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return {"total_nodes": 0, "total_relations": 0, "categories": {}}
    
    def add_custom_knowledge(self, node_data: Dict[str, Any], relations: list = None):
        """Add custom knowledge to the graph"""
        pass  # Placeholder for knowledge graph functionality


def main():
    """Main entry point with knowledge graph features"""
    print("� Product Search Assistant with Knowledge Graph")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator()
    
    # Show knowledge graph stats
    kg_stats = orchestrator.get_knowledge_stats()
    print(f"📊 Knowledge Graph: {kg_stats['total_nodes']} nodes, {kg_stats['total_relations']} relations")
    print("💡 The system uses AI + Knowledge Graph for enhanced product discovery")
    print("-" * 60)
    
    while True:
        try:
            print("\nOptions:")
            print("1. 🔍 Search for products")
            print("2. 🧠 Manage Knowledge Graph")
            print("3. 📊 Show KG Statistics")
            print("4. 🚪 Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                user_input = input("\nEnter your product search query: ")
                if user_input.strip():
                    # Process the query
                    result = orchestrator.process_query(user_input)
                    
                    if Config.DEBUG_MODE:
                        print(f"\n[DEBUG] Final processing stage: {result.get('processing_stage')}")
            
            elif choice == "2":
                print("🧠 Launching Knowledge Graph Manager...")
                from kg_manager import KnowledgeGraphManager
                kg_manager = KnowledgeGraphManager()
                kg_manager.interactive_menu()
            
            elif choice == "3":
                stats = orchestrator.get_knowledge_stats()
                print(f"\n📊 Knowledge Graph Statistics:")
                print(f"   Nodes: {stats['total_nodes']}")
                print(f"   Relations: {stats['total_relations']}")
                print(f"   Categories: {list(stats['categories'].keys())}")
            
            elif choice == "4":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid option. Please select 1-4.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
