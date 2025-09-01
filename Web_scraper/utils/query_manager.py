"""
Query management system for saving and processing search queries.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

from config.settings import Config
from utils.helpers import setup_logging

@dataclass
class SavedQuery:
    """Represents a saved search query."""
    query: str
    first_searched: datetime
    last_searched: datetime
    search_count: int
    embedding: Optional[np.ndarray] = None
    priority: float = 1.0
    is_active: bool = True

class QueryManager:
    """Manages search queries with similarity checking and deduplication."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize the query manager."""
        self.logger = setup_logging(Config.LOG_LEVEL)
        self.similarity_threshold = similarity_threshold
        
        # Database connection
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.collection = self.db["search-data"]
        
        # Sentence transformer for similarity checking
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Cache for query embeddings
        self._query_cache = {}
        
        self.logger.info("QueryManager initialized")

    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get embedding for a query with caching."""
        if query not in self._query_cache:
            embedding = self.model.encode([query], normalize_embeddings=True)[0]
            self._query_cache[query] = embedding
        return self._query_cache[query]

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate cosine similarity between two queries."""
        emb1 = self._get_query_embedding(query1)
        emb2 = self._get_query_embedding(query2)
        
        # Cosine similarity (embeddings are already normalized)
        similarity = np.dot(emb1, emb2)
        return float(similarity)

    def _is_similar_query_exists(self, new_query: str) -> Optional[Dict[str, Any]]:
        """Check if a similar query already exists in the database."""
        try:
            # Get all existing queries
            existing_queries = list(self.collection.find({"is_active": True}))
            
            for existing in existing_queries:
                existing_query = existing.get("query", "")
                if not existing_query:
                    continue
                
                similarity = self._calculate_similarity(new_query, existing_query)
                
                if similarity >= self.similarity_threshold:
                    self.logger.debug(
                        f"Found similar query: '{new_query}' ~ '{existing_query}' "
                        f"(similarity: {similarity:.3f})"
                    )
                    return existing
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking similar queries: {e}")
            return None

    def save_query(self, query: str, source: str = "api") -> Dict[str, Any]:
        """
        Save a search query if it's not too similar to existing ones.
        
        Args:
            query: The search query to save
            source: Source of the query (api, manual, etc.)
            
        Returns:
            Dict with save status and details
        """
        try:
            query = query.strip().lower()
            if not query:
                return {"saved": False, "reason": "Empty query"}
            
            # Check for similar existing query
            similar_query = self._is_similar_query_exists(query)
            
            if similar_query:
                # Update existing query instead of creating new
                result = self.collection.update_one(
                    {"_id": similar_query["_id"]},
                    {
                        "$set": {
                            "last_searched": datetime.utcnow(),
                            "last_source": source
                        },
                        "$inc": {"search_count": 1}
                    }
                )
                
                return {
                    "saved": False,
                    "reason": "Similar query exists",
                    "action": "updated_existing",
                    "similar_query": similar_query["query"],
                    "similarity": self._calculate_similarity(query, similar_query["query"]),
                    "updated": result.modified_count > 0
                }
            
            # Create new query document
            now = datetime.utcnow()
            embedding = self._get_query_embedding(query).tolist()  # Convert to list for MongoDB
            
            query_doc = {
                "query": query,
                "first_searched": now,
                "last_searched": now,
                "search_count": 1,
                "embedding": embedding,
                "priority": 1.0,
                "is_active": True,
                "source": source,
                "last_source": source,
                "created_at": now
            }
            
            result = self.collection.insert_one(query_doc)
            
            self.logger.info(f"Saved new query: '{query}' from {source}")
            
            return {
                "saved": True,
                "query_id": str(result.inserted_id),
                "query": query,
                "reason": "New unique query"
            }
            
        except Exception as e:
            self.logger.error(f"Error saving query '{query}': {e}")
            return {
                "saved": False,
                "reason": f"Error: {str(e)}"
            }

    def get_pending_queries(self, limit: int = 50) -> List[Dict]:
        """Get pending queries to be processed."""
        try:
            cursor = self.collection.find(
                {"status": "pending"}
            ).sort("created_at", 1).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"Error getting pending queries: {e}")
            return []
    
    def get_all_queries(self, limit: int = 100) -> List[Dict]:
        """Get all queries with optional limit."""
        try:
            cursor = self.collection.find().sort("created_at", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"Error getting all queries: {e}")
            return []
    
    def update_query_status(self, query_id: str, status: str) -> bool:
        """Update the status of a query."""
        try:
            from bson import ObjectId
            
            result = self.collection.update_one(
                {"_id": ObjectId(query_id)},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"Error updating query status: {e}")
            return False

    def mark_query_processed(self, query: str, success: bool = True, items_found: int = 0):
        """Mark a query as processed and update statistics."""
        try:
            update_data = {
                "last_processed": datetime.utcnow(),
                "last_success": success,
                "last_items_found": items_found
            }
            
            if success:
                update_data["$inc"] = {"successful_runs": 1}
                # Increase priority for successful queries with good results
                if items_found > 5:
                    update_data["$inc"]["priority"] = 0.1
            else:
                update_data["$inc"] = {"failed_runs": 1}
                # Decrease priority for failed queries
                update_data["$inc"]["priority"] = -0.1
            
            result = self.collection.update_one(
                {"query": query, "is_active": True},
                {"$set": update_data, "$inc": update_data.get("$inc", {})}
            )
            
            if result.modified_count > 0:
                self.logger.debug(f"Marked query '{query}' as processed (success: {success})")
            
        except Exception as e:
            self.logger.error(f"Error marking query processed: {e}")

    def deactivate_old_queries(self, days_old: int = 30):
        """Deactivate queries that haven't been searched recently."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = self.collection.update_many(
                {
                    "last_searched": {"$lt": cutoff_date},
                    "is_active": True,
                    "search_count": {"$lt": 5}  # Don't deactivate popular queries
                },
                {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Deactivated {result.modified_count} old queries")
            
        except Exception as e:
            self.logger.error(f"Error deactivating old queries: {e}")

    def get_query_stats(self) -> Dict[str, Any]:
        """Get statistics about saved queries."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_queries": {"$sum": 1},
                        "active_queries": {
                            "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                        },
                        "total_searches": {"$sum": "$search_count"},
                        "avg_priority": {"$avg": "$priority"}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if result:
                stats = result[0]
                stats.pop("_id", None)
                return stats
            else:
                return {
                    "total_queries": 0,
                    "active_queries": 0,
                    "total_searches": 0,
                    "avg_priority": 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting query stats: {e}")
            return {"error": str(e)}

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'client'):
            self.client.close()
            self.logger.debug("Closed MongoDB connection")

if __name__ == "__main__":
    # Example usage
    manager = QueryManager()
    
    try:
        # Test saving queries
        test_queries = ["rice", "basmati rice", "vegetables", "fresh vegetables"]
        
        for query in test_queries:
            result = manager.save_query(query, "test")
            print(f"Query '{query}': {result}")
        
        # Get stats
        stats = manager.get_query_stats()
        print(f"\nQuery stats: {stats}")
        
        # Get pending queries
        pending = manager.get_pending_queries(5)
        print(f"\nPending queries: {[q.query for q in pending]}")
        
    finally:
        manager.close()
