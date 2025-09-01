"""
Enhanced similarity search engine for finding relevant products using embeddings.
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pickle

import numpy as np
import faiss
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

from config.settings import Config
from utils.helpers import setup_logging

@dataclass
class SearchResult:
    """Result from similarity search."""
    collection: str
    item_id: str
    title: str
    similarity_score: float
    price_lkr: Optional[float] = None
    source_domain: Optional[str] = None
    website: Optional[str] = None
    scraped_at: Optional[str] = None

class SimilaritySearchEngine:
    """Enhanced similarity search engine with caching and optimization."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "data/search_cache"):
        """Initialize the search engine."""
        self.logger = setup_logging(Config.LOG_LEVEL)
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Database connection
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client[Config.DATABASE_NAME]
        
        # Collections to search
        self.collections = ["Glowmark", "Kapuruka", "Lassana_Flora", "OnlineKade"]
        
        # Model and index (loaded lazily)
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        self.is_loaded = False
        
        # Cache files
        self.embeddings_cache = self.cache_dir / "embeddings.pkl"
        self.metadata_cache = self.cache_dir / "metadata.pkl"
        self.index_cache = self.cache_dir / "faiss_index.bin"
        
        self.logger.info(f"Initialized SimilaritySearchEngine with model: {model_name}")

    def _load_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            self.logger.info(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.logger.debug("Model loaded successfully")

    def _should_rebuild_index(self) -> bool:
        """Check if the index should be rebuilt based on data freshness."""
        if not all([
            self.embeddings_cache.exists(),
            self.metadata_cache.exists(),
            self.index_cache.exists()
        ]):
            self.logger.info("Cache files missing, will rebuild index")
            return True
        
        # Check if cache is older than 1 hour (configurable)
        cache_age = time.time() - self.embeddings_cache.stat().st_mtime
        max_age = 3600  # 1 hour in seconds
        
        if cache_age > max_age:
            self.logger.info(f"Cache is {cache_age/3600:.1f} hours old, rebuilding")
            return True
        
        # Check if new data has been added to MongoDB
        try:
            total_docs = 0
            for coll_name in self.collections:
                if coll_name in self.db.list_collection_names():
                    total_docs += self.db[coll_name].count_documents({})
            
            # Load cached metadata to compare
            with open(self.metadata_cache, 'rb') as f:
                cached_metadata = pickle.load(f)
            
            if len(cached_metadata) != total_docs:
                self.logger.info(f"Document count changed: {len(cached_metadata)} -> {total_docs}")
                return True
                
        except Exception as e:
            self.logger.warning(f"Error checking data freshness: {e}")
            return True
        
        return False

    def _load_documents_from_db(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Load all documents from MongoDB collections."""
        documents = []
        metadata = []
        
        self.logger.info("Loading documents from MongoDB...")
        
        for coll_name in self.collections:
            if coll_name not in self.db.list_collection_names():
                self.logger.warning(f"Collection {coll_name} not found in database")
                continue
                
            coll = self.db[coll_name]
            count = 0
            
            for doc in coll.find({}, {
                "title": 1, 
                "price_LKR": 1, 
                "source_domain": 1, 
                "website": 1,
                "scraped_at": 1
            }):
                if "title" in doc and doc["title"].strip():
                    documents.append(doc["title"].strip())
                    metadata.append({
                        "collection": coll_name,
                        "item_id": str(doc["_id"]),
                        "title": doc["title"].strip(),
                        "price_lkr": doc.get("price_LKR"),
                        "source_domain": doc.get("source_domain"),
                        "website": doc.get("website"),
                        "scraped_at": doc.get("scraped_at")
                    })
                    count += 1
            
            self.logger.debug(f"Loaded {count} documents from {coll_name}")
        
        self.logger.info(f"Total documents loaded: {len(documents)}")
        return documents, metadata

    def _build_embeddings(self, documents: List[str]) -> np.ndarray:
        """Build embeddings for documents."""
        self.logger.info("Building embeddings...")
        self._load_model()
        
        # Process in batches to handle memory efficiently
        batch_size = 100
        embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch, 
                convert_to_numpy=True, 
                normalize_embeddings=True,
                show_progress_bar=False
            )
            embeddings.append(batch_embeddings)
            
            if (i // batch_size + 1) % 10 == 0:
                self.logger.debug(f"Processed {i + len(batch)}/{len(documents)} documents")
        
        embeddings_array = np.vstack(embeddings)
        self.logger.info(f"Built embeddings: {embeddings_array.shape}")
        return embeddings_array

    def _build_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Build FAISS index for fast similarity search."""
        self.logger.info("Building FAISS index...")
        
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # Inner product (cosine similarity with normalized vectors)
        index.add(embeddings.astype(np.float32))
        
        self.logger.info(f"FAISS index built with {index.ntotal} vectors")
        return index

    def _save_cache(self, embeddings: np.ndarray, metadata: List[Dict], index: faiss.Index):
        """Save embeddings, metadata, and index to cache."""
        try:
            # Save embeddings and metadata
            with open(self.embeddings_cache, 'wb') as f:
                pickle.dump(embeddings, f)
            
            with open(self.metadata_cache, 'wb') as f:
                pickle.dump(metadata, f)
            
            # Save FAISS index
            faiss.write_index(index, str(self.index_cache))
            
            self.logger.debug("Cache saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def _load_cache(self) -> Tuple[Optional[np.ndarray], Optional[List[Dict]], Optional[faiss.Index]]:
        """Load embeddings, metadata, and index from cache."""
        try:
            # Load embeddings and metadata
            with open(self.embeddings_cache, 'rb') as f:
                embeddings = pickle.load(f)
            
            with open(self.metadata_cache, 'rb') as f:
                metadata = pickle.load(f)
            
            # Load FAISS index
            index = faiss.read_index(str(self.index_cache))
            
            self.logger.debug(f"Cache loaded: {len(metadata)} items, {embeddings.shape}")
            return embeddings, metadata, index
            
        except Exception as e:
            self.logger.warning(f"Error loading cache: {e}")
            return None, None, None

    def load_data(self, force_rebuild: bool = False):
        """Load or rebuild the search index."""
        start_time = time.time()
        
        # Check if we should use cache or rebuild
        if not force_rebuild and not self._should_rebuild_index():
            self.logger.info("Loading from cache...")
            embeddings, metadata, index = self._load_cache()
            
            if embeddings is not None and metadata is not None and index is not None:
                self.metadata = metadata
                self.index = index
                self.is_loaded = True
                load_time = time.time() - start_time
                self.logger.info(f"Loaded {len(metadata)} items from cache in {load_time:.2f}s")
                return
        
        # Rebuild index
        self.logger.info("Rebuilding search index...")
        
        # Load documents from database
        documents, metadata = self._load_documents_from_db()
        
        if not documents:
            self.logger.error("No documents found in database")
            return
        
        # Build embeddings
        embeddings = self._build_embeddings(documents)
        
        # Build FAISS index
        index = self._build_faiss_index(embeddings)
        
        # Save to cache
        self._save_cache(embeddings, metadata, index)
        
        # Update instance variables
        self.metadata = metadata
        self.index = index
        self.is_loaded = True
        
        load_time = time.time() - start_time
        self.logger.info(f"Index rebuilt with {len(metadata)} items in {load_time:.2f}s")

    def search(self, query: str, top_k: int = 10, min_similarity: float = 0.3) -> List[SearchResult]:
        """Search for similar items."""
        if not self.is_loaded:
            self.load_data()
        
        if not self.is_loaded or self.index is None:
            self.logger.error("Search index not loaded")
            return []
        
        self._load_model()
        
        # Encode query
        query_embedding = self.model.encode(
            [query], 
            convert_to_numpy=True, 
            normalize_embeddings=True
        )
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype(np.float32), top_k)
        
        # Convert results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
                
            similarity = float(score)
            if similarity < min_similarity:
                continue
            
            meta = self.metadata[idx]
            result = SearchResult(
                collection=meta["collection"],
                item_id=meta["item_id"],
                title=meta["title"],
                similarity_score=similarity,
                price_lkr=meta.get("price_lkr"),
                source_domain=meta.get("source_domain"),
                website=meta.get("website"),
                scraped_at=meta.get("scraped_at")
            )
            results.append(result)
        
        self.logger.debug(f"Found {len(results)} results for query: '{query}'")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index."""
        if not self.is_loaded:
            return {"loaded": False}
        
        stats = {
            "loaded": True,
            "total_items": len(self.metadata),
            "collections": {}
        }
        
        # Count items per collection
        for meta in self.metadata:
            collection = meta["collection"]
            if collection not in stats["collections"]:
                stats["collections"][collection] = 0
            stats["collections"][collection] += 1
        
        return stats

    def refresh_index(self):
        """Force refresh the search index."""
        self.logger.info("Forcing index refresh...")
        self.load_data(force_rebuild=True)

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'client'):
            self.client.close()
            self.logger.debug("Closed MongoDB connection")

# Legacy compatibility function
def search_similar_items(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Legacy function for backwards compatibility."""
    engine = SimilaritySearchEngine()
    try:
        results = engine.search(query, top_k)
        return [
            {
                "collection": r.collection,
                "id": r.item_id,
                "title": r.title,
                "similarity": r.similarity_score
            }
            for r in results
        ]
    finally:
        engine.close()

if __name__ == "__main__":
    # Example usage
    engine = SimilaritySearchEngine()
    
    try:
        # Load data
        engine.load_data()
        
        # Test search
        query = "rice"
        results = engine.search(query, top_k=5)
        
        print(f"\nTop matches for '{query}':")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   Collection: {result.collection}")
            print(f"   Similarity: {result.similarity_score:.3f}")
            if result.price_lkr:
                print(f"   Price: LKR {result.price_lkr}")
            print()
        
        # Show stats
        stats = engine.get_stats()
        print(f"Index stats: {stats}")
        
    finally:
        engine.close()
