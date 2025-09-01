"""
Enhanced Flask web application for coordinating multiple e-commerce scrapers.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from scrapers import GlowmarkScraper, KaprukaScraper, OnlineKadeScraper
from config.settings import Config, ScraperConfig
from utils.helpers import setup_logging, calculate_stats

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging
logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)

# Initialize scrapers
scrapers = {
    "glowmark": GlowmarkScraper(),
    "kapruka": KaprukaScraper(),
    "onlinekade": OnlineKadeScraper()
}

# Thread pool for concurrent scraping
executor = ThreadPoolExecutor(max_workers=3)

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
