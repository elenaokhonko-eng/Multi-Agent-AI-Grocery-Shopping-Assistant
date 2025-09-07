#!/usr/bin/env python3
"""
Python API server to handle Langraph agent pipeline requests
Runs on port 3004 (pairs nicely with a frontend/proxy on 8080)
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --------------------------
# Paths & import plumbing
# --------------------------
BACKEND_DIR = Path(__file__).resolve().parent                      # .../Backend
PROJECT_ROOT = BACKEND_DIR.parent                                  # .../<repo root>
LANGRAPH_DIR = PROJECT_ROOT / "Langraph_Agent"                     # .../Langraph_Agent  (sibling of Backend)

# Make both the LangGraph package and project root importable
if str(LANGRAPH_DIR) not in sys.path:
    sys.path.insert(0, str(LANGRAPH_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --------------------------
# Logging
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# Local data dirs (feedback/profile)
# --------------------------
PREFS_DIR = BACKEND_DIR / ".prefs"
PROFILES_DIR = BACKEND_DIR / ".profiles"
PREFS_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------
# Optional feedback/profile modules
# --------------------------
try:
    from core.feedback import FeedbackEvent, PreferenceStore, FeedbackEngine
    prefs_store = PreferenceStore(str(PREFS_DIR))
    feedback_engine = FeedbackEngine(prefs_store)
    logger.info("✅ Feedback engine initialized")
except Exception as e:
    logger.error(f"Feedback imports failed: {e}")
    FeedbackEvent = None
    prefs_store = None
    feedback_engine = None

try:
    from core.profile_store import UserProfileStore
    from core.profile_sync import augment_profile_from_learned
    profile_store = UserProfileStore(str(PROFILES_DIR))
except Exception as e:
    logger.warning(f"Profile sync unavailable: {e}")
    profile_store = None

# --------------------------
# Flask app
# --------------------------
app = Flask(__name__)
CORS(app)  # allow all origins for /api/*

# --------------------------
# RAG setup
# --------------------------
# Import the agent types from Langraph_Agent
from agents.rag_agent import get_rag_agent, RAGConfig

# Corpus + index live inside Langraph_Agent
CORPUS_DIR = os.getenv(
    "RAG_CORPUS_DIR",
    str(LANGRAPH_DIR / "agents" / "data" / "rag_corpus")
)

_rag = None
def get_rag():
    """Lazy singleton for the RAG agent (loads/creates FAISS once)."""
    global _rag
    if _rag is None:
        _rag = get_rag_agent(RAGConfig(
            index_dir=os.getenv("RAG_INDEX_DIR", str(LANGRAPH_DIR / "vectorstore" / "faiss_index")),
            corpus_dir=CORPUS_DIR,
            top_k=int(os.getenv("RAG_TOP_K", "6")),
            score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.35")),
        ))
    return _rag

def normalize_citations(raw):
    """
    Strip disk paths, dedupe by file+page, and build a public URL to serve the PDF page.
    (Safe even if your UI ignores references.)
    """
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

@app.route("/api/rag/source/<path:filename>", methods=["GET"])
def rag_source(filename):
    """Serve source PDFs from the corpus folder (for clickable references)."""
    return send_from_directory(CORPUS_DIR, filename, as_attachment=False)

@app.route("/api/rag/chat", methods=["POST"])
def rag_chat():
    """RAG chat endpoint: {message} -> {reply, references}"""
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

# --------------------------
# LangGraph pipeline
# --------------------------
try:
    # Import main orchestrator from Langraph_Agent
    from main import ProductSearchOrchestrator
    orchestrator = ProductSearchOrchestrator()
    logger.info("✅ Langraph pipeline initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Langraph pipeline: {e}")
    orchestrator = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
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
      { "query": "I need rice and tea for my kitchen" }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'status': 'error', 'message': 'Missing query parameter'}), 400

        query = data['query'].strip()
        if not query:
            return jsonify({'status': 'error', 'message': 'Query cannot be empty'}), 400

        logger.info(f"🔍 Processing search query: {query}")

        if not orchestrator:
            return jsonify({'status': 'error', 'message': 'Langraph pipeline not available'}), 503

        try:
            result = orchestrator.process_query(query)
            logger.info("✅ Pipeline processing completed successfully")

            if result is None:
                logger.error("❌ Pipeline returned None result")
                return jsonify({'status': 'error', 'message': 'Pipeline returned no result'}), 500

            logger.info(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            budget_optimized_data = result.get('budget_optimized_data', {})
            budget_optimization_summary = result.get('budget_optimization_summary', {})

            optimized_items = []
            if budget_optimized_data:
                for category, items in budget_optimized_data.items():
                    if isinstance(items, list) and items:
                        optimized_items.extend(items)
                    elif items:
                        optimized_items.append(items)

            data_acquisition = result.get('product_data', {}) or {}
            total_items_found = sum(len(items) for items in data_acquisition.values() if isinstance(items, list))

            if optimized_items:
                total_cost = sum(item.get('price_lkr', 0) for item in optimized_items)
                selection_summary = budget_optimization_summary.get('selection_summary', {}) if isinstance(budget_optimization_summary, dict) else {}
                final_total_cost = selection_summary.get('total_cost', total_cost) or total_cost
                budget_percentage = selection_summary.get('budget_utilization', round((total_cost / 5000.0) * 100, 1))
                delivery_time = selection_summary.get('estimated_delivery_time', 24.0)

                response_data = {
                    'status': 'success',
                    'query': query,
                    'results': {
                        'optimized_items': optimized_items,
                        'total_cost': final_total_cost,
                        'budget_used_percentage': budget_percentage,
                        'estimated_delivery_hours': delivery_time,
                        'items_count': len(optimized_items),
                        'stores_used': list({item.get('website', 'unknown') for item in optimized_items}),
                        'optimization_method': 'Linear Programming + Multi-Criteria AI',
                        'keywords_processed': result.get('keywords', []),
                        'total_items_found': len(optimized_items),
                        'pipeline_summary': {
                            'keywords_extracted': len(result.get('keywords', [])),
                            'items_acquired': sum(len(items) for items in data_acquisition.values() if isinstance(items, list)),
                            'items_personalized': len(result.get('personalized_data', {}).get('filtered_items', [])) if result.get('personalized_data') else 0,
                            'items_after_logistics': len(result.get('logistics_optimization', {}).get('filtered_items', [])) if result.get('logistics_optimization') else 0,
                            'loyalty_savings': result.get('loyalty_summary', {}).get('total_savings', 0.0) if result.get('loyalty_summary') else 0.0,
                            'final_selection': len(optimized_items)
                        }
                    }
                }

            elif total_items_found > 0:
                # Demo fallback using first items per category
                demo_items = []
                for keyword, items in data_acquisition.items():
                    if isinstance(items, list) and items:
                        it = items[0]
                        demo_items.append({
                            "title": it.get('title', f'Premium {keyword.title()}'),
                            "price_lkr": it.get('price_lkr', 250.0),
                            "website": it.get('website', 'unknown'),
                            "source_url": it.get('source_url', ''),
                            "collection": it.get('collection', 'unknown'),
                            "similarity_score": it.get('similarity_score', 0.9),
                            "kg_enhanced": it.get('kg_enhanced', False),
                            "original_query": query
                        })
                        if len(demo_items) >= 3:
                            break

                if demo_items:
                    demo_total_cost = sum(item["price_lkr"] for item in demo_items)
                    demo_stores = list({item["website"] for item in demo_items})
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

            logger.info(f"📦 Returning {len(response_data['results']['optimized_items'])} item(s)")
            return jsonify(response_data)

        except Exception as pipeline_error:
            logger.error(f"❌ Pipeline processing error: {pipeline_error}")
            return jsonify({'status': 'error', 'message': f'Pipeline processing failed: {str(pipeline_error)}'}), 500

    except Exception as e:
        logger.error(f"❌ API error: {e}")
        return jsonify({'status': 'error', 'message': f'API error: {str(e)}'}), 500

@app.route('/api/search/test', methods=['GET'])
def test_search():
    """Test endpoint with a sample query."""
    try:
        if not orchestrator:
            return jsonify({'status': 'error', 'message': 'Langraph pipeline not available'}), 503

        test_query = "I need rice and tea"
        logger.info(f"🧪 Running test search: {test_query}")

        result = orchestrator.process_query(test_query)
        bod = result.get('budget_optimized_data', {})
        bos = result.get('budget_optimization_summary', {})

        optimized_items_count = 0
        if bod:
            for _, items in bod.items():
                if isinstance(items, list):
                    optimized_items_count += len(items)
                elif items:
                    optimized_items_count += 1

        selection_summary = bos.get('selection_summary', {}) if isinstance(bos, dict) else {}
        total_cost = selection_summary.get('total_cost', 0.0)

        return jsonify({
            'status': 'success',
            'message': 'Test search completed',
            'query': test_query,
            'items_found': optimized_items_count,
            'total_cost': total_cost
        })

    except Exception as e:
        logger.error(f"❌ Test search error: {e}")
        return jsonify({'status': 'error', 'message': f'Test failed: {str(e)}'}), 500

# --------------------------
# Feedback endpoints (optional)
# --------------------------
@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    """
    Record a user action (click/like/add_to_cart/purchase/dislike/hide/rating)
    """
    if not feedback_engine:
        return jsonify({"status": "error", "message": "Feedback engine not available on server"}), 503

    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    action = (data.get("action") or "").strip().lower()
    item = data.get("item") or {}

    if not user_id or not action:
        logger.warning(f"/api/feedback 400: missing fields payload={data}")
        return jsonify({"status": "error", "message": "user_id and action are required"}), 400

    try:
        ev = FeedbackEvent(
            user_id=user_id,
            timestamp=data.get("timestamp") or time.time(),
            query=data.get("query", ""),
            category=item.get("category"),
            item_id=item.get("item_id"),
            title=item.get("title"),
            brand=item.get("brand"),
            store=item.get("store") or item.get("website") or item.get("collection"),
            price_lkr=item.get("price_lkr"),
            delivery_hours=item.get("delivery_hours"),
            tags=item.get("tags", []),
            action=action,
            rating=data.get("rating")
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"invalid feedback payload: {e}"}), 400

    try:
        feedback_engine.record(ev)
    except Exception as e:
        logger.error(f"Feedback recording failed: {e}")
        return jsonify({"status": "error", "message": f"feedback recording failed: {e}"}), 500

    did_sync = False
    if profile_store:
        try:
            learned = prefs_store.load(user_id)
            profile = profile_store.load(user_id)
            profile = augment_profile_from_learned(profile, learned, allow_overwrite=False)
            profile_store.save(profile)
            did_sync = True
        except Exception as e:
            logger.warning(f"Profile sync skipped: {e}")

    try:
        learned = prefs_store.load(user_id)
        snapshot = {
            "brand_beta": dict(learned.brand_beta),
            "store_beta": dict(learned.store_beta),
            "category_beta": dict(learned.category_beta),
            "tag_scores": learned.tag_scores,
            "price_mean": learned.price_mean,
            "price_var": learned.price_var,
            "delivery_mean_h": learned.delivery_mean_h,
            "last_updated": learned.last_updated,
        }
    except Exception:
        snapshot = None

    return jsonify({
        "status": "success",
        "message": "feedback recorded",
        "synced_profile": did_sync,
        "impression_id": data.get("impression_id"),
        "position": data.get("position"),
        "snapshot": snapshot
    }), 200

@app.route('/api/feedback/snapshot', methods=['GET'])
def feedback_snapshot():
    user_id = (request.args.get("user_id") or "").strip()
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400
    if not prefs_store:
        return jsonify({"status": "error", "message": "preference store unavailable"}), 503

    up = prefs_store.load(user_id)
    return jsonify({
        "status": "success",
        "user_id": user_id,
        "prefs": {
            "brand_beta": dict(up.brand_beta),
            "store_beta": dict(up.store_beta),
            "category_beta": dict(up.category_beta),
            "tag_scores": up.tag_scores,
            "price_mean": up.price_mean,
            "price_var": up.price_var,
            "delivery_mean_h": up.delivery_mean_h,
            "last_updated": up.last_updated
        }
    })

@app.route('/api/feedback/health', methods=['GET'])
def feedback_health():
    info = {
        "has_FeedbackEvent": FeedbackEvent is not None,
        "has_PreferenceStore": prefs_store is not None,
        "has_feedback_engine_instance": feedback_engine is not None,
        "prefs_dir": str(PREFS_DIR),
        "profiles_dir": str(PROFILES_DIR),
        "prefs_dir_exists": PREFS_DIR.is_dir(),
        "profiles_dir_exists": PROFILES_DIR.is_dir(),
    }
    return jsonify({"status": "ok" if feedback_engine else "unavailable", "feedback": info}), (
        200 if feedback_engine else 503
    )

# --------------------------
# Main
# --------------------------
if __name__ == '__main__':
    print("🚀 Starting Python API server...")
    print("📍 API endpoints:")
    print("   - GET  /health")
    print("   - POST /api/search")
    print("   - GET  /api/search/test")
    print("   - POST /api/rag/chat")
    print("   - GET  /api/rag/source/<file>")
    print("   - POST /api/feedback")
    print("   - GET  /api/feedback/snapshot")
    print("   - GET  /api/feedback/health")
    print()

    app.run(host='0.0.0.0', port=3004, debug=False, threaded=True)
