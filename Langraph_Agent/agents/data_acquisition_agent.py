"""
Data Acquisition Agent with Knowledge Graph integration
"""
import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from agents.knowledge_graph_agent import KnowledgeGraphAgent


# Initialize Knowledge Graph Agent globally
kg_agent = KnowledgeGraphAgent()


@tool
def retrieve_product_data(keywords: List[str], max_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve product data for given keywords from e-commerce databases with knowledge graph enhancement.
    
    Args:
        keywords: List of product keywords to search for
        max_results: Maximum number of results per keyword
        
    Returns:
        Dictionary mapping keywords to product information
    """
    print(f"[TOOL] Data Acquisition Agent retrieving data for keywords: {keywords}")
    
    # Step 1: Enhance keywords using knowledge graph
    enhanced_keywords = kg_agent.enhance_keywords(keywords)
    print(f"[TOOL] Enhanced keywords using knowledge graph: {enhanced_keywords}")
    
    results = {}
    
    try:
        # TODO: Replace with actual Web_scraper integration
        # from retrieval.item_retriever import find_best_items_sync
        
        for original_kw in keywords:
            print(f"[TOOL] Processing keyword: {original_kw}")
            all_search_terms = enhanced_keywords.get(original_kw, [original_kw])
            
            # Search for all enhanced terms
            combined_items = []
            
            for search_term in all_search_terms:
                print(f"[TOOL] Retrieving items for enhanced term: {search_term}")
                
                # Mock data - replace with actual retrieval
                mock_items = [
                    {
                        "title": f"Premium {search_term.title()}", 
                        "price_lkr": 250.0,
                        "website": "glowmark.lk",
                        "source_url": f"https://glowmark.lk/product/premium-{search_term}",
                        "collection": "glowmark",
                        "similarity_score": 0.95,
                        "kg_enhanced": search_term != original_kw,  # Mark if enhanced by KG
                        "original_query": original_kw
                    },
                    {
                        "title": f"Organic {search_term.title()}", 
                        "price_lkr": 180.0,
                        "website": "kapruka.com",
                        "source_url": f"https://kapruka.com/product/organic-{search_term}",
                        "collection": "kapruka",
                        "similarity_score": 0.87,
                        "kg_enhanced": search_term != original_kw,
                        "original_query": original_kw
                    },
                    {
                        "title": f"Fresh {search_term.title()}", 
                        "price_lkr": 320.0,
                        "website": "onlinekade.lk",
                        "source_url": f"https://onlinekade.lk/product/fresh-{search_term}",
                        "collection": "onlinekade",
                        "similarity_score": 0.92,
                        "kg_enhanced": search_term != original_kw,
                        "original_query": original_kw
                    }
                ]
                
                combined_items.extend(mock_items)
            
            # Remove duplicates and sort by relevance
            unique_items = {}
            for item in combined_items:
                key = item["title"].lower()
                if key not in unique_items or unique_items[key]["similarity_score"] < item["similarity_score"]:
                    unique_items[key] = item
            
            # Sort by similarity score and limit results
            sorted_items = sorted(unique_items.values(), key=lambda x: x["similarity_score"], reverse=True)
            results[original_kw] = sorted_items[:max_results]
            
            print(f"[TOOL] Retrieved {len(results[original_kw])} items for '{original_kw}' (including KG enhancements)")
            
    except Exception as e:
        print(f"[TOOL] Error during data acquisition: {e}")
        results = {kw: [{"title": f"Error retrieving {kw}", "error": str(e)}] for kw in keywords}
    
    return results


@tool
def get_product_substitutes(product_name: str) -> List[Dict[str, Any]]:
    """
    Get product substitutes when an item is out of stock using knowledge graph.
    
    Args:
        product_name: Name of the product to find substitutes for
        
    Returns:
        List of substitute products with details
    """
    print(f"[TOOL] Finding substitutes for: {product_name}")
    
    substitutes = kg_agent.get_substitutes(product_name)
    substitute_details = []
    
    for substitute_name, similarity_score in substitutes:
        substitute_details.append({
            "title": substitute_name,
            "similarity_score": similarity_score,
            "substitute_for": product_name,
            "reason": "Knowledge graph recommendation"
        })
    
    return substitute_details


class DataAcquisitionAgent:
    """Agent responsible for acquiring product data using tool calls and knowledge graph"""
    
    def __init__(self, llm: ChatGroq):
        # Create a separate LLM instance without JSON mode for tool calling
        self.llm_for_tools = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0
            # No JSON mode for tool calling
        )
        self.tools = [retrieve_product_data, get_product_substitutes]
        # Bind tools to the LLM
        self.llm_with_tools = self.llm_for_tools.bind_tools(self.tools)
        self.kg_agent = kg_agent
    
    def acquire_data(self, keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Use LLM with tool calling to acquire product data with knowledge graph enhancement
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Dictionary mapping keywords to product data
        """
        print(f"[AGENT] Data Acquisition Agent processing keywords: {keywords}")
        
        # Create a prompt for the LLM to use the tool
        prompt = f"""
        You are a Data Acquisition Agent with knowledge graph capabilities. Use the retrieve_product_data tool to get enhanced product information for these keywords: {keywords}
        
        The system will automatically enhance the search using a knowledge graph to find related products, substitutes, and variations.
        
        Call the tool with the keywords and return the comprehensive results.
        """
        
        try:
            # Get response from LLM with tools
            response = self.llm_with_tools.invoke([{"role": "user", "content": prompt}])
            
            # Check if the LLM made tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                print(f"[AGENT] LLM called tool: {tool_name} with args: {tool_args}")
                
                # Execute the tool
                if tool_name == "retrieve_product_data":
                    return retrieve_product_data.invoke(tool_args)
                elif tool_name == "get_product_substitutes":
                    # Handle substitute requests
                    substitutes = get_product_substitutes.invoke(tool_args)
                    return {"substitutes": substitutes}
            else:
                # Fallback: call tool directly
                print("[AGENT] No tool calls detected, calling tool directly")
                return retrieve_product_data.invoke({"keywords": keywords})
                
        except Exception as e:
            print(f"[AGENT] Error in data acquisition: {e}")
            return {}
    
    def add_knowledge(self, node_data: Dict[str, Any], relations: List[Dict[str, Any]] = None):
        """Add custom knowledge to the knowledge graph"""
        self.kg_agent.add_custom_knowledge(node_data, relations)
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return self.kg_agent.get_knowledge_stats()
