"""
Data Acquisition Agent with Knowledge Graph integration and MongoDB semantic search
"""
import json
import os
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from agents.knowledge_graph_agent import KnowledgeGraphAgent

"""
Data Acquisition Agent with Knowledge Graph integration and MongoDB text search
"""
import json
import os
import re
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_groq import ChatGroq
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

class MongoDBTextSearcher:
    """MongoDB text search without semantic dependencies"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = ["Glowmark", "Kapuruka", "Lassana_Flora", "OnlineKade"]
        self.collection_mapping = {
            "Glowmark": "glowmark.lk",
            "Kapuruka": "kapruka.com", 
            "Lassana_Flora": "lassanaflora.com",
            "OnlineKade": "onlinekade.lk"
        }
        
        if MONGODB_AVAILABLE:
            self._initialize()
        else:
            print("[MONGODB] Searcher not available, will use mock data")
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        try:
            print("[MONGODB] Connecting to MongoDB...")
            self.client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
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
                            standardized = {
                                "title": product.get('title', product.get('name', 'Unknown')),
                                "price_lkr": self._extract_price(product),
                                "website": self.collection_mapping.get(collection_name, collection_name.lower()),
                                "source_url": product.get('source_url', product.get('url', '')),
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

# Initialize Knowledge Graph Agent globally
kg_agent = KnowledgeGraphAgent()

class MongoDBSemanticSearcher:
    """MongoDB semantic search with FAISS indexing"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.model = None
        self.index = None
        self.meta = []
        self.collections = ["Glowmark", "Kapuruka", "Lassana_Flora", "OnlineKade"]
        self.collection_mapping = {
            "Glowmark": "glowmark.lk",
            "Kapuruka": "kapruka.com", 
            "Lassana_Flora": "lassanaflora.com",
            "OnlineKade": "onlinekade.lk"
        }
        
        if MONGODB_AVAILABLE:
            self._initialize()
        else:
            print("[MONGODB] Searcher not available, will use mock data")
    
    def _initialize(self):
        """Initialize MongoDB connection and FAISS index"""
        try:
            print("[MONGODB] Connecting to MongoDB...")
            self.client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client["ecommerce_db"]
            
            print("[MONGODB] Loading embedding model...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            
            print("[MONGODB] Building FAISS index...")
            self._build_index()
            
        except Exception as e:
            print(f"[MONGODB] Error initializing: {e}")
            print("[MONGODB] Will use mock data instead")
            self.client = None
    
    def _build_index(self):
        """Build FAISS index from MongoDB documents"""
        if not MONGODB_AVAILABLE:
            return
            
        docs = []
        self.meta = []
        
        for coll_name in self.collections:
            try:
                coll = self.db[coll_name]
                count = 0
                for doc in coll.find({}, {"title": 1, "price": 1, "url": 1}):
                    if "title" in doc and doc["title"]:
                        docs.append(doc["title"])
                        self.meta.append({
                            "collection": coll_name,
                            "id": str(doc["_id"]),
                            "title": doc["title"],
                            "price": doc.get("price", 0),
                            "url": doc.get("url", ""),
                            "website": self.collection_mapping.get(coll_name, coll_name.lower())
                        })
                        count += 1
                print(f"[MONGODB] Loaded {count} documents from {coll_name}")
            except Exception as e:
                print(f"[MONGODB] Error loading from {coll_name}: {e}")
        
        if docs and MONGODB_AVAILABLE:
            try:
                print(f"[MONGODB] Total documents loaded: {len(docs)}")
                embeddings = self.model.encode(docs, convert_to_numpy=True, normalize_embeddings=True)
                
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dim)  # cosine similarity
                self.index.add(embeddings)
                
                print(f"[MONGODB] FAISS index built with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"[MONGODB] Error building FAISS index: {e}")
                self.index = None
        else:
            print("[MONGODB] No documents found to index")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search for similar products using semantic similarity"""
        if not self.index or not self.model:
            print(f"[MONGODB] Search unavailable, returning empty results for: {query}")
            return []
        
        try:
            q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            scores, idxs = self.index.search(q_emb, min(top_k, self.index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], idxs[0]):
                if idx < len(self.meta):  # Valid index
                    item = self.meta[idx]
                    results.append({
                        "title": item["title"],
                        "price_lkr": float(item["price"]) if item["price"] else 0.0,
                        "website": item["website"],
                        "source_url": item["url"],
                        "collection": item["collection"].lower(),
                        "similarity_score": float(score),
                        "kg_enhanced": False,  # Will be set by caller if enhanced
                        "original_query": query
                    })
            
            return results
            
        except Exception as e:
            print(f"[MONGODB] Error during search for '{query}': {e}")
            return []

# Initialize global searcher
mongodb_searcher = None
if MONGODB_AVAILABLE:
    try:
        mongodb_searcher = MongoDBSemanticSearcher()
    except Exception as e:
        print(f"[MONGODB] Failed to initialize searcher: {e}")
        mongodb_searcher = None
else:
    print("[MONGODB] Searcher not available, will use mock data")


@tool
def retrieve_product_data(keywords: List[str], max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve product data for given keywords from MongoDB with semantic search and knowledge graph enhancement.
    
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
                    # Use MongoDB semantic search
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
                    mock_items = [
                        {
                            "title": f"Premium {search_term.title()}", 
                            "price_lkr": 250.0,
                            "website": "glowmark.lk",
                            "source_url": f"https://glowmark.lk/product/premium-{search_term}",
                            "collection": "glowmark",
                            "similarity_score": 0.95,
                            "kg_enhanced": search_term != original_kw,
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
            
            # Remove duplicates based on title and sort by relevance
            unique_items = {}
            for item in combined_items:
                key = item["title"].lower()
                if key not in unique_items or unique_items[key]["similarity_score"] < item["similarity_score"]:
                    unique_items[key] = item
            
            # Sort by similarity score and limit results
            sorted_items = sorted(unique_items.values(), key=lambda x: x["similarity_score"], reverse=True)
            results[original_kw] = sorted_items[:max_results]
            
            print(f"[TOOL] Retrieved {len(results[original_kw])} items for '{original_kw}' (including KG enhancements)")
            
            # Print detailed retrieved items
            print(f"[TOOL] Items retrieved for '{original_kw}':")
            for i, item in enumerate(results[original_kw][:5], 1):  # Show first 5 items
                kg_indicator = "🧠" if item.get("kg_enhanced") else "📦"
                enhanced_info = f" (from: {item.get('enhanced_from', 'direct')})" if item.get("kg_enhanced") else ""
                print(f"       {i}. {kg_indicator} {item['title']} - LKR {item['price_lkr']} ({item['website']}) [Score: {item['similarity_score']:.2f}]{enhanced_info}")
            if len(results[original_kw]) > 5:
                print(f"       ... and {len(results[original_kw]) - 5} more items")
            
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
