#!/usr/bin/env python3
"""
Python API server to handle Langraph agent pipeline requests
Runs on port 3002 to complement the Node.js server on port 3001
"""

import sys
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from pathlib import Path


# Add the Langraph_Agent directory to Python path
langraph_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Langraph_Agent')
sys.path.insert(0, langraph_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = os.getenv(
    "RAG_CORPUS_DIR",
    str(BASE_DIR / "Langraph_Agent" / "agents" / "data" / "rag_corpus")
)

# Build/load FAISS once (lazy)
_rag = None
def get_rag():
    global _rag
    if _rag is None:
        _rag = get_rag_agent(RAGConfig(
            index_dir=os.getenv("RAG_INDEX_DIR", str(BASE_DIR / "Langraph_Agent" / "vectorstore" / "faiss_index")),
            corpus_dir=CORPUS_DIR,
            top_k=int(os.getenv("RAG_TOP_K", "6")),
            score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.35")),
        ))
    return _rag

def normalize_citations(raw):
    """Strip disk paths, dedupe by file+page, and build a public URL to serve the PDF page."""
    seen = set()
    refs = []
    for c in (raw or []):
        meta = c.get("metadata", {})
        src = c.get("source") or meta.get("source") or ""
        file = os.path.basename(src) if src else "unknown"
        page = meta.get("page")
        page_label = meta.get("page_label") or (str((page or 0) + 1) if page is not None else None)

        key = (file, page_label or page)
        if key in seen:
            continue
        seen.add(key)

        display_page = page_label or (page + 1 if page is not None else 1)
        refs.append({
            "id": f"{file}:p{display_page}",
            "file": file,
            "title": file,
            "page": page,
            "page_label": str(display_page),
            "page_url": f"/api/rag/source/{file}#page={display_page}",
        })
    return refs
try:
    from main import ProductSearchOrchestrator
    from agents.rag_agent import get_rag_agent, RAGConfig
    orchestrator = ProductSearchOrchestrator()
    logger.info("✅ Langraph pipeline initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Langraph pipeline: {e}")
    orchestrator = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'message': 'Python API server is running',
        'langraph_available': orchestrator is not None
    })

@app.route('/api/search', methods=['POST'])
def search_products():
    """
    Search products using the Langraph agentic pipeline
    
    Request body:
    {
        "query": "I need rice and tea for my kitchen"
    }
    
    Returns:
    {
        "status": "success",
        "query": "I need rice and tea",
        "results": {
            "optimized_items": [...],
            "total_cost": 640.0,
            "budget_used": 12.8,
            "delivery_time": 12.0,
            "summary": {...}
        }
    }
    """
    try:
        # Get the search query from request
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing query parameter'
            }), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Query cannot be empty'
            }), 400
        
        logger.info(f"🔍 Processing search query: {query}")
        
        # Check if orchestrator is available
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'Langraph pipeline not available'
            }), 503
        
        # Process the query through the Langraph pipeline
        try:
            result = orchestrator.process_query(query)
            logger.info("✅ Pipeline processing completed successfully")
            
            # Debug: Check if result is None
            if result is None:
                logger.error("❌ Pipeline returned None result")
                return jsonify({
                    'status': 'error',
                    'message': 'Pipeline returned no result'
                }), 500
            
            logger.info(f"📊 Full pipeline result type: {type(result)}")
            logger.info(f"📊 Full pipeline result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Extract key information from the result - FIXED: Use correct keys
            budget_optimized_data = result.get('budget_optimized_data', {})
            budget_optimization_summary = result.get('budget_optimization_summary', {})
            logger.info(f"📊 Budget optimized data: {list(budget_optimized_data.keys()) if budget_optimized_data else 'None'}")
            logger.info(f"📊 Budget optimization summary: {budget_optimization_summary}")
            
            # Extract optimized items from budget_optimized_data
            optimized_items = []
            if budget_optimized_data:
                for category, items in budget_optimized_data.items():
                    if isinstance(items, list) and items:
                        optimized_items.extend(items)
                    elif items:  # Single item
                        optimized_items.append(items)
            
            logger.info(f"📦 Optimized items found: {len(optimized_items)}")
            logger.info(f"📦 Optimized items details: {optimized_items}")
            
            
            # Check if we have any data from data acquisition as fallback
            data_acquisition = result.get('product_data', {}) or {}
            logger.info(f"📊 Data acquisition type: {type(data_acquisition)}")
            logger.info(f"📊 Data acquisition keys: {list(data_acquisition.keys()) if isinstance(data_acquisition, dict) else 'Not a dict'}")
            
            total_items_found = 0
            if isinstance(data_acquisition, dict):
                for keyword, items in data_acquisition.items():
                    item_count = len(items) if isinstance(items, list) else 0
                    total_items_found += item_count
                    logger.info(f"📦 {keyword}: {item_count} items")
            
            # If we have real optimized items, use them
            if optimized_items:
                logger.info(f"✅ Using {len(optimized_items)} real optimized items")
                
                # Calculate totals from the optimized items
                total_cost = sum(item.get('price_lkr', 0) for item in optimized_items)
                selection_summary = {}
                if budget_optimization_summary and isinstance(budget_optimization_summary, dict):
                    selection_summary = budget_optimization_summary.get('selection_summary', {})
                
                # Use selection_summary values if available, otherwise calculate from items
                final_total_cost = selection_summary.get('total_cost', total_cost) if selection_summary else total_cost
                budget_percentage = selection_summary.get('budget_utilization', round((total_cost / 5000.0) * 100, 1)) if selection_summary else round((total_cost / 5000.0) * 100, 1)
                delivery_time = selection_summary.get('estimated_delivery_time', 24.0) if selection_summary else 24.0
                
                response_data = {
                    'status': 'success',
                    'query': query,
                    'results': {
                        'optimized_items': optimized_items,
                        'total_cost': final_total_cost,
                        'budget_used_percentage': budget_percentage,
                        'estimated_delivery_hours': delivery_time,
                        'items_count': len(optimized_items),
                        'stores_used': list(set(item.get('website', 'unknown') for item in optimized_items)),
                        'optimization_method': 'Linear Programming + Multi-Criteria AI',
                        'keywords_processed': result.get('keywords', []),
                        'total_items_found': len(optimized_items),
                        'pipeline_summary': {
                            'keywords_extracted': len(result.get('keywords', [])),
                            'items_acquired': sum(len(items) if isinstance(items, list) else 1 for items in data_acquisition.values()) if isinstance(data_acquisition, dict) and data_acquisition else 0,
                            'items_personalized': len(result.get('personalized_data', {}).get('filtered_items', [])) if result.get('personalized_data') else 0,
                            'items_after_logistics': len(result.get('logistics_optimization', {}).get('filtered_items', [])) if result.get('logistics_optimization') else 0,
                            'loyalty_savings': result.get('loyalty_summary', {}).get('total_savings', 0.0) if result.get('loyalty_summary') else 0.0,
                            'final_selection': len(optimized_items)
                        }
                    }
                }
            
            # If no optimized items but we have data acquisition items, create mock optimization
            elif total_items_found > 0:
                logger.info(f"⚡ Creating demo optimization from {total_items_found} acquired items")
                
                # Get first few items from data acquisition for demo
                demo_items = []
                for keyword, items in data_acquisition.items():
                    if isinstance(items, list) and len(items) > 0:
                        # Take the first item for this keyword
                        item = items[0]
                        demo_items.append({
                            "title": item.get('title', f'Premium {keyword.title()}'),
                            "price_lkr": item.get('price_lkr', 250.0),
                            "website": item.get('website', 'unknown'),
                            "source_url": item.get('source_url', ''),
                            "collection": item.get('collection', 'unknown'),
                            "similarity_score": item.get('similarity_score', 0.9),
                            "kg_enhanced": item.get('kg_enhanced', False),
                            "original_query": query
                        })
                        if len(demo_items) >= 3:  # Limit to 3 items for demo
                            break
                
                if demo_items:
                    demo_total_cost = sum(item["price_lkr"] for item in demo_items)
                    demo_stores = list(set(item["website"] for item in demo_items))
                    
                    response_data = {
                        'status': 'success',
                        'query': query,
                        'results': {
                            'optimized_items': demo_items,
                            'total_cost': demo_total_cost,
                            'budget_used_percentage': round((demo_total_cost / 5000.0) * 100, 1),
                            'estimated_delivery_hours': 24.0,
                            'items_count': len(demo_items),
                            'stores_used': demo_stores,
                            'optimization_method': 'Linear Programming + AI (Demo)',
                            'keywords_processed': result.get('keywords', []),
                            'total_items_found': total_items_found,
                            'pipeline_summary': {
                                'keywords_extracted': len(result.get('keywords', [])),
                                'items_acquired': total_items_found,
                                'items_personalized': total_items_found,
                                'items_after_logistics': min(total_items_found, len(demo_items)),
                                'loyalty_savings': 0.0,
                                'final_selection': len(demo_items)
                            }
                        }
                    }
                else:
                    # Fallback to completely mock data
                    logger.info("⚠️ No usable items found, using fallback mock data")
                    response_data = {
                        'status': 'success',
                        'query': query,
                        'results': {
                            'optimized_items': [],
                            'total_cost': 0.0,
                            'budget_used_percentage': 0.0,
                            'estimated_delivery_hours': 24.0,
                            'items_count': 0,
                            'stores_used': [],
                            'optimization_method': 'No items found',
                            'keywords_processed': result.get('keywords', []),
                            'total_items_found': total_items_found,
                            'pipeline_summary': {
                                'keywords_extracted': len(result.get('keywords', [])),
                                'items_acquired': total_items_found,
                                'items_personalized': 0,
                                'items_after_logistics': 0,
                                'loyalty_savings': 0.0,
                                'final_selection': 0
                            }
                        }
                    }
            else:
                # No items found at all
                logger.info("❌ No items found in pipeline")
                response_data = {
                    'status': 'success',
                    'query': query,
                    'results': {
                        'optimized_items': [],
                        'total_cost': 0.0,
                        'budget_used_percentage': 0.0,
                        'estimated_delivery_hours': 24.0,
                        'items_count': 0,
                        'stores_used': [],
                        'optimization_method': 'No items found',
                        'keywords_processed': result.get('keywords', []),
                        'total_items_found': 0,
                        'pipeline_summary': {
                            'keywords_extracted': len(result.get('keywords', [])),
                            'items_acquired': 0,
                            'items_personalized': 0,
                            'items_after_logistics': 0,
                            'loyalty_savings': 0.0,
                            'final_selection': 0
                        }
                    }
                }
            
            logger.info(f"📦 Returning {len(optimized_items)} optimized items, total cost: LKR {final_total_cost if 'final_total_cost' in locals() else total_cost if 'total_cost' in locals() else 0}")
            return jsonify(response_data)
            
        except Exception as pipeline_error:
            logger.error(f"❌ Pipeline processing error: {pipeline_error}")
            return jsonify({
                'status': 'error',
                'message': f'Pipeline processing failed: {str(pipeline_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ API error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'API error: {str(e)}'
        }), 500

@app.route('/api/search/test', methods=['GET'])
def test_search():
    """Test endpoint with a sample query"""
    try:
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'Langraph pipeline not available'
            }), 503
        
        test_query = "I need rice and tea"
        logger.info(f"🧪 Running test search: {test_query}")
        
        result = orchestrator.process_query(test_query)
        budget_optimized_data = result.get('budget_optimized_data', {})
        budget_optimization_summary = result.get('budget_optimization_summary', {})
        
        # Count optimized items
        optimized_items_count = 0
        if budget_optimized_data:
            for category, items in budget_optimized_data.items():
                if isinstance(items, list):
                    optimized_items_count += len(items)
                elif items:
                    optimized_items_count += 1
        
        selection_summary = {}
        if budget_optimization_summary and isinstance(budget_optimization_summary, dict):
            selection_summary = budget_optimization_summary.get('selection_summary', {})
        
        total_cost = selection_summary.get('total_cost', 0.0) if selection_summary else 0.0
        
        return jsonify({
            'status': 'success',
            'message': 'Test search completed',
            'query': test_query,
            'items_found': optimized_items_count,
            'total_cost': total_cost
        })
        
    except Exception as e:
        logger.error(f"❌ Test search error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {str(e)}'
        }), 500

@app.post("/api/rag/chat")
def rag_chat():
    data = request.get_json(force=True) or {}
    q = (data.get("message") or data.get("q") or "").strip()
    if not q:
        return jsonify({"error": "message is required"}), 400
    try:
        res = get_rag().answer(q)  # { answer, citations, documents }
        references = normalize_citations(res.get("citations"))
        return jsonify({
            "query": q,
            "reply": res.get("answer", ""),
            "references": references
        }), 200
    except Exception as e:
        logger.exception("RAG chat failed")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Change to the Langraph_Agent directory to ensure proper imports
    os.chdir(langraph_path)
    
    print("🚀 Starting Python API server for Langraph pipeline...")
    print("📍 API endpoints:")
    print("   - GET  /health          - Health check")
    print("   - POST /api/search      - Process search query")
    print("   - GET  /api/search/test - Test with sample query")
    print()
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=3004,
        debug=False,
        threaded=True
    )
