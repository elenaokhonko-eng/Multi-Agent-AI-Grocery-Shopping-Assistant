"""
Enhanced Flask web application for coordinating multiple e-commerce scrapers.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from scrapers import LittleFarmsScraper, FairPriceScraper, ShengSiongScraper, ColdStorageScraper, LazadaScraper
from retrieval import ItemRetriever
from utils.query_manager import QueryManager
from config.settings import Config, ScraperConfig
from utils.helpers import setup_logging, calculate_stats

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging
logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)

# Initialize scrapers and retriever
scrapers = {
    "littlefarms": LittleFarmsScraper(),
    "fairprice": FairPriceScraper(),
    "shengsiong": ShengSiongScraper(),
    "coldstorage": ColdStorageScraper(),
    "lazada": LazadaScraper()
}

# Initialize item retriever and query manager
item_retriever = ItemRetriever()
query_manager = QueryManager()

# Thread pool for concurrent scraping
executor = ThreadPoolExecutor(max_workers=3)

def save_search_query(query: str, endpoint: str = "unknown") -> Dict[str, Any]:
    """Save a search query with similarity checking."""
    try:
        result = query_manager.save_query(query, source=f"api_{endpoint}")
        if result.get("saved"):
            logger.debug(f"Saved new query: '{query}' from {endpoint}")
        else:
            logger.debug(f"Query '{query}' not saved: {result.get('reason')}")
        return result
    except Exception as e:
        logger.error(f"Error saving query '{query}': {e}")
        return {"saved": False, "error": str(e)}

def scrape_single_site(scraper_name: str, scraper, query: str) -> Dict[str, Any]:
    """Scrape a single website and return results."""
    try:
        result = scraper.scrape_sync(query)
        result["scraper"] = scraper_name
        return result
    except Exception as e:
        logger.error(f"Error scraping {scraper_name}: {e}")
        return {
            "success": False,
            "scraper": scraper_name,
            "error": str(e),
            "items_count": 0
        }

@app.route("/", methods=["GET"])
def index():
    """Home page with API documentation."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>E-commerce Scraper API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
            .example { background: #e9ecef; padding: 10px; margin: 10px 0; border-radius: 3px; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>E-commerce Scraper API</h1>
        <p>This API provides endpoints for scraping product data from multiple Sri Lankan e-commerce websites.</p>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /scrape</h3>
            <p>Scrape all websites for a given query</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>query</code> (required): Search term</li>
                <li><code>sites</code> (optional): Comma-separated list of sites (glowmark,kapruka,onlinekade)</li>
                <li><code>parallel</code> (optional): Set to 'false' for sequential scraping</li>
            </ul>
            <div class="example">
                <strong>Example:</strong><br>
                <code>GET /scrape?query=rice&sites=glowmark,kapruka</code>
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /scrape/{site}</h3>
            <p>Scrape a specific website</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>query</code> (required): Search term</li>
            </ul>
            <div class="example">
                <strong>Example:</strong><br>
                <code>GET /scrape/glowmark?query=vegetables</code>
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /retrieve</h3>
            <p>Advanced item retrieval combining scraping and similarity search</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>query</code> (required): Search term</li>
                <li><code>max_results</code> (optional): Maximum results to return (default: 20)</li>
                <li><code>include_scraping</code> (optional): Include fresh scraping (default: true)</li>
                <li><code>include_similarity</code> (optional): Include similarity search (default: true)</li>
                <li><code>scrape_sites</code> (optional): Sites to scrape (comma-separated)</li>
                <li><code>min_similarity</code> (optional): Minimum similarity score (default: 0.3)</li>
            </ul>
            <div class="example">
                <strong>Example:</strong><br>
                <code>GET /retrieve?query=rice&max_results=10&include_scraping=true</code>
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /search</h3>
            <p>Semantic similarity search in existing data</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>query</code> (required): Search term</li>
                <li><code>top_k</code> (optional): Number of results (default: 10)</li>
                <li><code>min_similarity</code> (optional): Minimum similarity score (default: 0.3)</li>
            </ul>
            <div class="example">
                <strong>Example:</strong><br>
                <code>GET /search?query=vegetables&top_k=5</code>
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /search/refresh</h3>
            <p>Refresh the similarity search index</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /health</h3>
            <p>Check API health status</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /sites</h3>
            <p>List all available scraper sites</p>
        </div>
        
        <h2>Response Format</h2>
        <pre>{
  "success": true,
  "query": "rice",
  "total_items": 45,
  "execution_time": 12.34,
  "results": {
    "glowmark": {
      "success": true,
      "items_count": 15,
      "execution_time": 4.12,
      "item_stats": {...}
    },
    "kapruka": {...}
  },
  "combined_stats": {...}
}</pre>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "available_scrapers": list(scrapers.keys()),
        "version": "2.0.0"
    })

@app.route("/sites", methods=["GET"])
def list_sites():
    """List all available scraper sites."""
    site_info = {}
    for name, scraper in scrapers.items():
        config = ScraperConfig.SCRAPERS.get(name, {})
        site_info[name] = {
            "name": config.get("name", name.title()),
            "base_url": config.get("base_url", ""),
            "collection": scraper.get_collection_name(),
            "website": scraper.get_website_name()
        }
    
    return jsonify({
        "available_sites": site_info,
        "total_sites": len(scrapers)
    })

@app.route("/scrape/<site>", methods=["GET"])
def scrape_single(site: str):
    """Scrape a single website."""
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    
    if site not in scrapers:
        return jsonify({
            "error": f"Unknown site '{site}'",
            "available_sites": list(scrapers.keys())
        }), 404
    
    start_time = time.time()
    
    try:
        scraper = scrapers[site]
        result = scraper.scrape_sync(query)
        result["execution_time"] = time.time() - start_time
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error scraping {site}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "site": site,
            "query": query,
            "execution_time": time.time() - start_time
        }), 500

@app.route("/scrape", methods=["GET"])
def scrape_all():
    """Scrape multiple or all websites."""
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    
    # Parse site selection
    sites_param = request.args.get("sites", "")
    if sites_param:
        selected_sites = [s.strip() for s in sites_param.split(",")]
        # Validate sites
        invalid_sites = [s for s in selected_sites if s not in scrapers]
        if invalid_sites:
            return jsonify({
                "error": f"Unknown sites: {invalid_sites}",
                "available_sites": list(scrapers.keys())
            }), 400
    else:
        selected_sites = list(scrapers.keys())
    
    # Check if parallel execution is requested (default: True)
    parallel = request.args.get("parallel", "true").lower() != "false"
    
    start_time = time.time()
    logger.info(f"Starting scrape for query '{query}' on sites: {selected_sites}")
    
    try:
        results = {}
        
        if parallel and len(selected_sites) > 1:
            # Parallel execution
            logger.debug("Using parallel execution")
            future_to_site = {
                executor.submit(scrape_single_site, site, scrapers[site], query): site
                for site in selected_sites
            }
            
            for future in future_to_site:
                site = future_to_site[future]
                try:
                    results[site] = future.result(timeout=60)  # 60 second timeout
                except Exception as e:
                    logger.error(f"Parallel scraping failed for {site}: {e}")
                    results[site] = {
                        "success": False,
                        "error": str(e),
                        "scraper": site,
                        "items_count": 0
                    }
        else:
            # Sequential execution
            logger.debug("Using sequential execution")
            for site in selected_sites:
                results[site] = scrape_single_site(site, scrapers[site], query)
        
        # Calculate combined statistics
        total_items = sum(r.get("items_count", 0) for r in results.values())
        successful_sites = sum(1 for r in results.values() if r.get("success", False))
        execution_time = time.time() - start_time
        
        # Collect all item statistics for combined stats
        all_stats = [r.get("item_stats") for r in results.values() 
                    if r.get("success") and r.get("item_stats")]
        
        combined_stats = None
        if all_stats:
            all_prices = []
            for stats in all_stats:
                if stats.get("price_stats"):
                    # This is a simplified approach - in a real scenario, 
                    # you'd want to recalculate from all individual items
                    all_prices.extend([stats["price_stats"]["min"], 
                                     stats["price_stats"]["max"]])
            
            if all_prices:
                combined_stats = {
                    "total_items": total_items,
                    "price_range": {
                        "min": min(all_prices),
                        "max": max(all_prices)
                    }
                }
        
        response = {
            "success": successful_sites > 0,
            "query": query,
            "sites_requested": selected_sites,
            "sites_successful": successful_sites,
            "total_items": total_items,
            "execution_time": execution_time,
            "parallel_execution": parallel,
            "results": results,
            "combined_stats": combined_stats,
            "timestamp": time.time()
        }
        
        logger.info(
            f"Scraping completed: {total_items} items from {successful_sites}/{len(selected_sites)} sites "
            f"in {execution_time:.2f}s"
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error during bulk scraping: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "query": query,
            "sites_requested": selected_sites,
            "execution_time": time.time() - start_time
        }), 500

@app.route("/retrieve", methods=["GET"])
def retrieve_items():
    """Advanced item retrieval combining scraping and similarity search."""
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    
    # Save the query
    query_save_result = save_search_query(query, "retrieve")
    
    # Parse parameters
    max_results = int(request.args.get("max_results", 20))
    include_scraping = request.args.get("include_scraping", "true").lower() == "true"
    include_similarity = request.args.get("include_similarity", "true").lower() == "true"
    min_similarity = float(request.args.get("min_similarity", 0.3))
    
    scrape_sites = request.args.get("scrape_sites")
    if scrape_sites:
        scrape_sites = [s.strip() for s in scrape_sites.split(",")]
        # Validate sites
        invalid_sites = [s for s in scrape_sites if s not in scrapers]
        if invalid_sites:
            return jsonify({
                "error": f"Unknown sites: {invalid_sites}",
                "available_sites": list(scrapers.keys())
            }), 400
    
    start_time = time.time()
    logger.info(f"Starting item retrieval for query '{query}'")
    
    try:
        results, summary = item_retriever.retrieve_sync(
            query=query,
            max_results=max_results,
            include_scraping=include_scraping,
            include_similarity=include_similarity,
            scrape_sites=scrape_sites,
            min_similarity=min_similarity
        )
        
        # Convert results to dict format
        results_data = []
        for result in results:
            result_dict = {
                "title": result.title,
                "price_lkr": result.price_lkr,
                "currency": result.currency,
                "source": result.source,
                "website": result.website,
                "collection": result.collection
            }
            
            if result.similarity_score:
                result_dict["similarity_score"] = result.similarity_score
            if result.source_url:
                result_dict["source_url"] = result.source_url
            if result.source_domain:
                result_dict["source_domain"] = result.source_domain
            if result.item_id:
                result_dict["item_id"] = result.item_id
            
            results_data.append(result_dict)
        
        # Convert summary to dict
        summary_data = {
            "query": summary.query,
            "total_results": summary.total_results,
            "scraped_results": summary.scraped_results,
            "similarity_results": summary.similarity_results,
            "execution_time": summary.execution_time,
            "websites_searched": summary.websites_searched
        }
        
        if summary.price_range:
            summary_data["price_range"] = summary.price_range
        
        if summary.best_match:
            summary_data["best_match"] = {
                "title": summary.best_match.title,
                "price_lkr": summary.best_match.price_lkr,
                "website": summary.best_match.website,
                "source": summary.best_match.source
            }
        
        response = {
            "success": True,
            "results": results_data,
            "summary": summary_data,
            "query_saved": query_save_result,
            "timestamp": time.time()
        }
        
        logger.info(f"Item retrieval completed: {len(results)} items in {summary.execution_time:.2f}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error during item retrieval: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "query": query,
            "execution_time": time.time() - start_time
        }), 500

@app.route("/search", methods=["GET"])
def similarity_search():
    """Semantic similarity search in existing data."""
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    
    # Save the query
    query_save_result = save_search_query(query, "search")
    
    top_k = int(request.args.get("top_k", 10))
    min_similarity = float(request.args.get("min_similarity", 0.3))
    
    start_time = time.time()
    
    try:
        # Use the search engine directly for faster response
        search_engine = item_retriever.search_engine
        results = search_engine.search(query, top_k, min_similarity)
        
        # Convert results to dict format
        results_data = []
        for result in results:
            results_data.append({
                "title": result.title,
                "similarity_score": result.similarity_score,
                "collection": result.collection,
                "website": result.website or result.collection,
                "price_lkr": result.price_lkr,
                "source_domain": result.source_domain,
                "item_id": result.item_id
            })
        
        execution_time = time.time() - start_time
        
        response = {
            "success": True,
            "query": query,
            "results": results_data,
            "total_results": len(results_data),
            "execution_time": execution_time,
            "search_type": "similarity",
            "parameters": {
                "top_k": top_k,
                "min_similarity": min_similarity
            },
            "query_saved": query_save_result,
            "timestamp": time.time()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error during similarity search: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "query": query,
            "execution_time": time.time() - start_time
        }), 500

@app.route("/search/refresh", methods=["POST"])
def refresh_search_index():
    """Refresh the similarity search index."""
    try:
        start_time = time.time()
        item_retriever.refresh_similarity_index()
        execution_time = time.time() - start_time
        
        # Get updated stats
        stats = item_retriever.search_engine.get_stats()
        
        return jsonify({
            "success": True,
            "message": "Search index refreshed successfully",
            "execution_time": execution_time,
            "stats": stats,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing search index: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to refresh search index"
        }), 500

@app.route("/stats", methods=["GET"])
def get_system_stats():
    """Get comprehensive system statistics."""
    try:
        retriever_stats = item_retriever.get_stats()
        
        return jsonify({
            "success": True,
            "system_stats": retriever_stats,
            "api_info": {
                "version": "2.0.0",
                "available_endpoints": [
                    "/", "/health", "/sites", "/scrape", "/scrape/<site>",
                    "/retrieve", "/search", "/search/refresh", "/stats",
                    "/query-stats", "/queries", "/query/<query_id>/status"
                ]
            },
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/query-stats', methods=['GET'])
def get_query_stats():
    """Get statistics about saved queries"""
    try:
        from utils.query_manager import QueryManager
        query_manager = QueryManager()
        
        # Get all queries
        all_queries = query_manager.get_all_queries()
        pending_queries = query_manager.get_pending_queries()
        processed_queries = [q for q in all_queries if q.get('status') == 'processed']
        
        stats = {
            "total_queries": len(all_queries),
            "pending_queries": len(pending_queries),
            "processed_queries": len(processed_queries),
            "recent_queries": all_queries[:10] if all_queries else []
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get query stats: {str(e)}"
        }), 500

@app.route('/queries', methods=['GET'])
def get_queries():
    """Get all saved queries with optional filtering"""
    try:
        from utils.query_manager import QueryManager
        query_manager = QueryManager()
        
        status = request.args.get('status')  # 'pending', 'processed', or None for all
        limit = int(request.args.get('limit', 50))
        
        if status:
            if status == 'pending':
                queries = query_manager.get_pending_queries()
            else:
                all_queries = query_manager.get_all_queries()
                queries = [q for q in all_queries if q.get('status') == status]
        else:
            queries = query_manager.get_all_queries()
        
        # Limit results
        queries = queries[:limit]
        
        return jsonify({
            "success": True,
            "queries": queries,
            "total": len(queries),
            "filters": {"status": status, "limit": limit}
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get queries: {str(e)}"
        }), 500

@app.route('/query/<query_id>/status', methods=['PUT'])
def update_query_status(query_id: str):
    """Update the status of a specific query"""
    try:
        from utils.query_manager import QueryManager
        query_manager = QueryManager()
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        # Update query status in database
        result = query_manager.update_query_status(query_id, new_status)
        
        return jsonify({
            "success": True,
            "query_id": query_id,
            "new_status": new_status,
            "updated": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to update query status: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/sites", "/scrape", "/scrape/<site>"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "Please check the logs for more details"
    }), 500

def cleanup():
    """Cleanup resources when shutting down."""
    logger.info("Shutting down scrapers...")
    for scraper in scrapers.values():
        try:
            scraper.close()
        except Exception as e:
            logger.error(f"Error closing scraper: {e}")
    
    # Close item retriever
    try:
        item_retriever.close()
        logger.info("Item retriever closed")
    except Exception as e:
        logger.error(f"Error closing item retriever: {e}")
    
    executor.shutdown(wait=True)
    logger.info("Cleanup completed")

# Register cleanup function
import atexit
atexit.register(cleanup)

if __name__ == "__main__":
    logger.info("Starting Enhanced Scraper API...")
    logger.info(f"Available scrapers: {list(scrapers.keys())}")
    
    # Development server
    app.run(
        debug=True, 
        port=5000,
        host="0.0.0.0"  # Allow external connections
    )
