"""
Data Acquisition Agent with Knowledge Graph integration and MongoDB text search
"""
import json
import os
import re
from typing import List, Dict, Any
from core.config import Config
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from agents.knowledge_graph_agent import KnowledgeGraphAgent

# MongoDB with simple text search (no PyTorch dependencies)
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
    print("[MONGODB] Basic MongoDB connection available")
except ImportError as e:
    print(f"[MONGODB] MongoDB not available: {e}")
    print("[MONGODB] Falling back to mock data")
    MONGODB_AVAILABLE = False
    MongoClient = None

# Initialize Knowledge Graph Agent globally
kg_agent = KnowledgeGraphAgent()

import sys
scraper_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Web_scraper", "utils", "mock_singapore_data.py")
import importlib.util
spec = importlib.util.spec_from_file_location("mock_singapore_data", scraper_file)
mock_singapore_data = importlib.util.module_from_spec(spec)
sys.modules["mock_singapore_data"] = mock_singapore_data
spec.loader.exec_module(mock_singapore_data)
search_mock_products = mock_singapore_data.search_mock_products
import random

class MongoDBTextSearcher:
    """MongoDB text search without semantic dependencies"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = ["LittleFarms", "FairPrice", "ShengSiong", "ColdStorage", "Lazada"]
        self.collection_mapping = {
            "LittleFarms": "littlefarms.com",
            "FairPrice": "fairprice.com.sg", 
            "ShengSiong": "shengsiong.com.sg",
            "ColdStorage": "coldstorage.com.sg",
            "Lazada": "lazada.sg"
        }
        
        if MONGODB_AVAILABLE:
            self._initialize()
        else:
            print("[MONGODB] Searcher not available, will use mock data")
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        try:
            print("[MONGODB] Connecting to MongoDB...")
            self.client = MongoClient("mongodb+srv://user:pass@cluster.mongodb.net/", serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client["ecommerce_db"]
            print("[MONGODB] Connected successfully")
        except Exception as e:
            print(f"[MONGODB] Connection failed: {e}")
            self.client = None
            self.db = None
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search products using text matching"""
        if self.db is None:
            print(f"[MONGODB] Database unavailable for query: {query}")
            return []
        
        try:
            results = []
            query_words = query.lower().split()
            
            for collection_name in self.collections:
                try:
                    collection = self.db[collection_name]
                    
                    # Create regex pattern for each word
                    search_conditions = []
                    for word in query_words:
                        word_pattern = {"$regex": re.escape(word), "$options": "i"}
                        search_conditions.append({
                            "$or": [
                                {"title": word_pattern},
                                {"name": word_pattern},
                                {"description": word_pattern},
                                {"category": word_pattern}
                            ]
                        })
                    
                    # Combine conditions with AND
                    if search_conditions:
                        if len(search_conditions) == 1:
                            query_filter = search_conditions[0]
                        else:
                            query_filter = {"$and": search_conditions}
                        
                        # Execute search
                        products = list(collection.find(query_filter, {"_id": 0}).limit(top_k))
                        
                        for product in products:
                            # Calculate text similarity score
                            similarity_score = self._calculate_similarity(query, product)
                            
                            # Standardize product format
                            price_val = self._extract_price(product)
                            standardized = {
                                "title": product.get('title', product.get('name', 'Unknown')),
                                "price_lkr": price_val,
                                "price_sgd": price_val,
                                "currency": "SGD",
                                "website": self.collection_mapping.get(collection_name, collection_name.lower()),
                                "source_url": product.get('source_url', product.get('url', '')),
                                "image_url": product.get('image_url', ''),
                                "collection": collection_name.lower(),
                                "similarity_score": similarity_score,
                                "kg_enhanced": False,
                                "original_query": query,
                                "search_type": "text_mongodb"
                            }
                            results.append(standardized)
                            
                except Exception as e:
                    print(f"[MONGODB] Error searching {collection_name}: {e}")
                    continue
            
            # Sort by similarity score and limit results
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"[MONGODB] Search error for '{query}': {e}")
            return []
    
    def _extract_price(self, product: Dict) -> float:
        """Extract and convert price to float"""
        # Try different price field names
        price = (product.get('price_LKR') or 
                product.get('price_lkr') or 
                product.get('price') or 
                0)
        
        if isinstance(price, (int, float)):
            return float(price) if price is not None else 250.0  # Default price for None values
        
        if isinstance(price, str):
            # Extract numbers from price string
            price_match = re.search(r'[\d,]+\.?\d*', price.replace(',', ''))
            if price_match:
                return float(price_match.group().replace(',', ''))
        
        return 250.0  # Default price when extraction fails
    
    def _calculate_similarity(self, query: str, product: Dict) -> float:
        """Calculate text similarity score"""
        query_words = set(query.lower().split())
        
        # Combine all text fields
        text_fields = [
            product.get('title', ''),
            product.get('name', ''),
            product.get('description', ''),
            product.get('category', '')
        ]
        product_text = ' '.join(str(field) for field in text_fields if field).lower()
        product_words = set(product_text.split())
        
        if not query_words or not product_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(product_words))
        union = len(query_words.union(product_words))
        
        return intersection / union if union > 0 else 0.0

# Initialize global searcher
mongodb_searcher = None
if MONGODB_AVAILABLE:
    try:
        mongodb_searcher = MongoDBTextSearcher()
    except Exception as e:
        print(f"[MONGODB] Failed to initialize searcher: {e}")
        mongodb_searcher = None
else:
    print("[MONGODB] Searcher not available, will use mock data")


@tool
def retrieve_product_data(keywords: List[str], max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve product data for given keywords from MongoDB with text search and knowledge graph enhancement.
    
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
        for original_kw in keywords:
            print(f"[TOOL] Processing keyword: {original_kw}")
            all_search_terms = enhanced_keywords.get(original_kw, [original_kw])
            
            # Search for all enhanced terms using MongoDB
            combined_items = []
            
            for search_term in all_search_terms:
                print(f"[TOOL] Retrieving items for enhanced term: {search_term}")
                
                if mongodb_searcher:
                    # Use MongoDB text search
                    search_results = mongodb_searcher.search(search_term, top_k=max_results)
                    
                    # Mark items as KG enhanced if they came from enhanced terms
                    for item in search_results:
                        item["kg_enhanced"] = (search_term != original_kw)
                        item["original_query"] = original_kw
                        if search_term != original_kw:
                            item["enhanced_from"] = search_term
                    
                    combined_items.extend(search_results)
                    print(f"[TOOL] Found {len(search_results)} items for '{search_term}' in MongoDB")
                    
                else:
                    # Fallback to mock data if MongoDB unavailable
                    print(f"[TOOL] MongoDB unavailable, using mock data for '{search_term}'")
                    # Search across all Singapore stores
                    mock_items = []
                    for store_domain in ["littlefarms.com", "fairprice.com.sg", "shengsiong.com.sg", "coldstorage.com.sg", "lazada.sg"]:
                        mock_products = search_mock_products(search_term, store_domain)
                        for mp in mock_products:
                            mock_items.append({
                                "title": mp["title"],
                                "price_lkr": mp["price_value"],
                                "price_sgd": mp["price_value"],
                                "currency": "SGD",
                                "website": store_domain,
                                "source_url": f"https://{store_domain}/search?q={search_term}",
                                "collection": store_domain.split('.')[0],
                                "similarity_score": 0.95 - (0.02 * random.random()),
                                "kg_enhanced": search_term != original_kw,
                                "original_query": original_kw,
                                "image_url": mp.get("image_url", "")
                            })
                    combined_items.extend(mock_items)
            
            # Remove duplicates based on title and store
            seen = set()
            unique_items = []
            for item in combined_items:
                key = (item["title"], item["website"])
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
            
            # Sort by similarity score and limit results
            unique_items.sort(key=lambda x: x["similarity_score"], reverse=True)
            final_items = unique_items[:max_results]
            
            results[original_kw] = final_items
            print(f"[TOOL] Retrieved {len(final_items)} items for '{original_kw}' (including KG enhancements)")
            
            # Print items with details
            print(f"[TOOL] Items retrieved for '{original_kw}':")
            for i, item in enumerate(final_items, 1):
                enhanced_mark = "🧠" if item.get("kg_enhanced") else "📦"
                enhanced_text = f" (from: {item.get('enhanced_from', 'direct')})" if item.get("kg_enhanced") else ""
                print(f"       {i}. {enhanced_mark} {item['title']} - SGD {item['price_lkr']} ({item['website']}) [Score: {item['similarity_score']:.2f}]{enhanced_text}")
                if i >= 5:  # Limit displayed items
                    remaining = len(final_items) - 5
                    if remaining > 0:
                        print(f"       ... and {remaining} more items")
                    break
        
        return results
        
    except Exception as e:
        print(f"[TOOL] Error in data acquisition: {e}")
        # Return mock data for all keywords as fallback
        fallback_results = {}
        for kw in keywords:
            kw_items = []
            for store_domain in ["littlefarms.com", "fairprice.com.sg", "shengsiong.com.sg", "coldstorage.com.sg", "lazada.sg"]:
                mock_products = search_mock_products(kw, store_domain)
                for mp in mock_products:
                    kw_items.append({
                        "title": mp["title"],
                        "price_lkr": mp["price_value"],
                        "price_sgd": mp["price_value"],
                        "currency": "SGD",
                        "website": store_domain,
                        "source_url": f"https://{store_domain}/search?q={kw}",
                        "collection": store_domain.split('.')[0],
                        "similarity_score": 0.95,
                        "kg_enhanced": False,
                        "original_query": kw,
                        "image_url": mp.get("image_url", "")
                    })
            fallback_results[kw] = kw_items if kw_items else [
                {
                    "title": f"Premium {kw.title()}", 
                    "price_lkr": 5.0,
                    "price_sgd": 5.0,
                    "currency": "SGD",
                    "website": "fairprice.com.sg",
                    "source_url": f"https://fairprice.com.sg/search?q={kw}",
                    "collection": "fairprice",
                    "similarity_score": 0.95,
                    "kg_enhanced": False,
                    "original_query": kw
                }
            ]
        return fallback_results


class DataAcquisitionAgent:
    """
    Agent responsible for acquiring product data from various sources
    """
    
    def __init__(self, llm_instance):
        self.llm = llm_instance
        self.tools = [retrieve_product_data]
        print("[AGENT] Data Acquisition Agent initialized")
    
    def process(self, keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process keywords and retrieve product data
        
        Args:
            keywords: List of product keywords to search for
            
        Returns:
            Dictionary mapping keywords to product lists
        """
        print(f"[AGENT] Data Acquisition Agent processing keywords: {keywords}")
        
        # Create a simple chat to trigger tool use
        messages = [
            {
                "role": "system",
                "content": f"You are a data acquisition agent. Use the retrieve_product_data tool to get product information for these keywords: {keywords}. Always call the tool with the exact keywords provided."
            },
            {
                "role": "user", 
                "content": f"Please retrieve product data for: {', '.join(keywords)}"
            }
        ]
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Get response with tool call
        response = llm_with_tools.invoke(messages)
        
        # Execute tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call['name'] == 'retrieve_product_data':
                    print(f"[AGENT] LLM called tool: {tool_call['name']} with args: {tool_call['args']}")
                    return retrieve_product_data.invoke(tool_call['args'])
        
        # Fallback - call tool directly
        return retrieve_product_data.invoke({"keywords": keywords})

    def acquire_data(self, keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Legacy method name for compatibility with main.py
        """
        return self.process(keywords)


# Test the agent if run directly
if __name__ == "__main__":
    from langchain_ollama import ChatOllama
    
    # Test configuration
    os.environ["GROQ_API_KEY"] = "your-api-key-here"  # Replace with actual key
    llm = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model="llama-3.1-8b-instant", temperature=0)
    
    # Create and test agent
    agent = DataAcquisitionAgent(llm)
    
    test_keywords = ["rice", "tea"]
    results = agent.process(test_keywords)
    
    print(f"\n🎯 Test Results:")
    for keyword, items in results.items():
        print(f"  {keyword}: {len(items)} items found")
        for item in items[:2]:  # Show first 2 items
            print(f"    - {item['title']} (LKR {item['price_lkr']})")
