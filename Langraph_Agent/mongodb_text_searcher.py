"""
Simplified MongoDB searcher using text matching instead of semantic search
"""

import re
from typing import List, Dict, Any
from pymongo import MongoClient

class MongoDBTextSearcher:
    """MongoDB text search without semantic dependencies"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = ["Glowmark", "Kapuruka", "OnlineKade"]
        self.collection_mapping = {
            "Glowmark": "glowmark.lk",
            "Kapuruka": "kapruka.com",
            "OnlineKade": "onlinekade.lk"
        }
        
        self._initialize()
    
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
            return float(price)
        
        if isinstance(price, str):
            # Extract numbers from price string
            price_match = re.search(r'[\d,]+\.?\d*', price.replace(',', ''))
            if price_match:
                return float(price_match.group().replace(',', ''))
        
        return 0.0
    
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
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Test the searcher
if __name__ == "__main__":
    searcher = MongoDBTextSearcher()
    
    # Test searches
    test_queries = ["rice", "tea", "coffee", "chocolate"]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: {query}")
        results = searcher.search(query, top_k=3)
        print(f"📊 Found {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title']} - LKR {result['price_lkr']} ({result['website']}) [Score: {result['similarity_score']:.3f}]")
    
    searcher.close()
    print("\n✅ Test completed")
