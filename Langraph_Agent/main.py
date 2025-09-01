"""
Refactored Langraph Application for Product Search
with Agent-based Architecture, Tool Calling, and Knowledge Graph Integration
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
from agents.keyword_extraction_agent import KeywordExtractionAgent
from agents.data_acquisition_agent import DataAcquisitionAgent
from agents.output_formatting_agent import OutputFormattingAgent
from agents.knowledge_graph_agent import KnowledgeGraphAgent


class ProductSearchOrchestrator:
    """Main orchestrator for the product search application with knowledge graph integration"""
    
    def __init__(self):
        """Initialize the orchestrator with LLM and agents"""
        self.llm = ChatGroq(
            model=Config.GROQ_MODEL,
            temperature=Config.GROQ_TEMPERATURE,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # Initialize agents
        self.keyword_agent = KeywordExtractionAgent(self.llm)
        self.data_agent = DataAcquisitionAgent(self.llm)
        self.output_agent = OutputFormattingAgent()
        self.kg_agent = KnowledgeGraphAgent()
        
        # Build the graph
        self.graph = self._build_graph()
        
        print("🧠 Product Search Orchestrator initialized with Knowledge Graph integration")
    
    def _build_graph(self) -> StateGraph:
        """Build the Langraph workflow"""
        graph_builder = StateGraph(ApplicationState)
        
        # Add nodes
        graph_builder.add_node("extract_keywords", self._extract_keywords_node)
        graph_builder.add_node("acquire_data", self._acquire_data_node)
        graph_builder.add_node("format_output", self._format_output_node)
        
        # Add edges
        graph_builder.add_edge(START, "extract_keywords")
        graph_builder.add_edge("extract_keywords", "acquire_data")
        graph_builder.add_edge("acquire_data", "format_output")
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
    
    def _format_output_node(self, state: ApplicationState) -> Dict[str, Any]:
        """Node for output formatting with knowledge graph awareness"""
        if Config.DEBUG_MODE:
            print(f"[NODE] Format Output - Processing {len(state.get('product_data', {}))} keyword results")
        
        product_data = state.get("product_data", {})
        formatted_output = self.output_agent.format_results(product_data)
        
        # Print the output
        print(formatted_output)
        
        return {
            "formatted_output": formatted_output,
            "processing_stage": "output_formatting_complete"
        }
    
    def process_query(self, user_query: str) -> ApplicationState:
        """
        Process a user query through the entire pipeline with knowledge graph enhancement
        
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
            "formatted_output": "",
            "processing_stage": "initialized"
        }
        
        if Config.DEBUG_MODE:
            print(f"[ORCHESTRATOR] Processing query with KG enhancement: '{user_query}'")
        
        result = self.graph.invoke(initial_state)
        return result
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return self.kg_agent.get_knowledge_stats()
    
    def add_custom_knowledge(self, node_data: Dict[str, Any], relations: list = None):
        """Add custom knowledge to the graph"""
        self.data_agent.add_knowledge(node_data, relations)


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
