"""
Data Acquisition Agent with tool calling capabilities
"""
import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_groq import ChatGroq


@tool
def retrieve_product_data(keywords: List[str], max_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve product data for given keywords from e-commerce databases.
    
    Args:
        keywords: List of product keywords to search for
        max_results: Maximum number of results per keyword
        
    Returns:
        Dictionary mapping keywords to product information
    """
    print(f"[TOOL] Data Acquisition Agent retrieving data for keywords: {keywords}")
    
    results = {}
    
    try:
        # TODO: Replace with actual Web_scraper integration
        # from retrieval.item_retriever import find_best_items_sync
        
        for kw in keywords:
            print(f"[TOOL] Retrieving items for keyword: {kw}")
            
            # Mock data - replace with actual retrieval
            mock_items = [
                {
                    "title": f"Premium {kw.title()}", 
                    "price_lkr": 250.0,
                    "website": "glowmark.lk",
                    "source_url": f"https://glowmark.lk/product/premium-{kw}",
                    "collection": "glowmark",
                    "similarity_score": 0.95
                },
                {
                    "title": f"Organic {kw.title()}", 
                    "price_lkr": 180.0,
                    "website": "kapruka.com",
                    "source_url": f"https://kapruka.com/product/organic-{kw}",
                    "collection": "kapruka",
                    "similarity_score": 0.87
                },
                {
                    "title": f"Fresh {kw.title()}", 
                    "price_lkr": 320.0,
                    "website": "onlinekade.lk",
                    "source_url": f"https://onlinekade.lk/product/fresh-{kw}",
                    "collection": "onlinekade",
                    "similarity_score": 0.92
                }
            ]
            
            results[kw] = mock_items[:max_results]
            print(f"[TOOL] Retrieved {len(results[kw])} items for '{kw}'")
            
    except Exception as e:
        print(f"[TOOL] Error during data acquisition: {e}")
        results = {kw: [{"title": f"Error retrieving {kw}", "error": str(e)}] for kw in keywords}
    
    return results


class DataAcquisitionAgent:
    """Agent responsible for acquiring product data using tool calls"""
    
    def __init__(self, llm: ChatGroq):
        # Create a separate LLM instance without JSON mode for tool calling
        self.llm_for_tools = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0
            # No JSON mode for tool calling
        )
        self.tools = [retrieve_product_data]
        # Bind tools to the LLM
        self.llm_with_tools = self.llm_for_tools.bind_tools(self.tools)
    
    def acquire_data(self, keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Use LLM with tool calling to acquire product data
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Dictionary mapping keywords to product data
        """
        print(f"[AGENT] Data Acquisition Agent processing keywords: {keywords}")
        
        # Create a prompt for the LLM to use the tool
        prompt = f"""
        You are a Data Acquisition Agent. Use the retrieve_product_data tool to get product information 
        for these keywords: {keywords}
        
        Call the tool with the keywords and return the results.
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
            else:
                # Fallback: call tool directly
                print("[AGENT] No tool calls detected, calling tool directly")
                return retrieve_product_data.invoke({"keywords": keywords})
                
        except Exception as e:
            print(f"[AGENT] Error in data acquisition: {e}")
            return {}
