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
from typing import Dict, Any

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
# Database setup
# --------------------------
from sqlmodel import SQLModel, create_engine, Session
from packages.domain.repositories.shopping_list_repository import ShoppingListRepository
from packages.domain.repositories.quote_repository import QuoteRepository
from packages.domain.services.pricing import calculate_gst_inclusive, calculate_delivery_fee, add_money, cents_to_display
from packages.domain.services.eligibility import rank_quotes

DB_URL = os.environ.get("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/grocery.db")
engine = create_engine(DB_URL)

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


def create_user_profile_from_request(profile_data: Dict[str, Any]):
    """
    Create UserProfile object from frontend request data

    Args:
        profile_data: Dictionary containing user profile from request

    Returns:
        UserProfile object
    """
    from core.user_profile import (
        UserProfile,
        DietaryNeeds,
        BrandPreferences,
        HouseholdInventory,
        LoyaltyMembership,
        DeliveryPreferences
    )

    # Create base profile
    user_profile = UserProfile(
        user_id=profile_data.get('user_id', 'guest_user'),
        budget_limit_lkr=float(profile_data.get('budget_limit_lkr', 5000.0)),
        location=profile_data.get('location', 'Colombo, Sri Lanka')
    )

    # Set dietary needs
    dietary_data = profile_data.get('dietary_needs', {})
    user_profile.dietary_needs = DietaryNeeds(
        vegetarian=dietary_data.get('vegetarian', False),
        vegan=dietary_data.get('vegan', False),
        gluten_free=dietary_data.get('gluten_free', False),
        dairy_free=dietary_data.get('dairy_free', False),
        organic_only=dietary_data.get('organic_only', False),
        low_sodium=dietary_data.get('low_sodium', False),
        sugar_free=dietary_data.get('sugar_free', False),
        halal=dietary_data.get('halal', False),
        kosher=dietary_data.get('kosher', False),
        allergies=dietary_data.get('allergies', [])
    )

    # Set brand preferences
    brand_data = profile_data.get('brand_preferences', {})
    user_profile.brand_preferences = BrandPreferences(
        preferred_brands=brand_data.get('preferred_brands', []),
        disliked_brands=brand_data.get('disliked_brands', [])
    )

    # Set household inventory
    inventory_data = profile_data.get('household_inventory', {})
    user_profile.household_inventory = HouseholdInventory(
        current_items=inventory_data.get('current_items', {}),
        low_stock_threshold=inventory_data.get('low_stock_threshold', 2)
    )

    # Set loyalty membership
    loyalty_data = profile_data.get('loyalty_membership', {})
    user_profile.loyalty_membership = LoyaltyMembership(
        preferred_stores=loyalty_data.get('preferred_stores', []),
        memberships=loyalty_data.get('memberships', {})
    )

    # Set delivery preferences (if provided)
    delivery_data = profile_data.get('delivery_preferences', {})
    if delivery_data:
        user_profile.delivery_preferences = DeliveryPreferences(
            preferred_stores=delivery_data.get('preferred_stores', []),
            max_delivery_time_hours=delivery_data.get('max_delivery_time_hours', 48.0),
            preferred_delivery_method=delivery_data.get('preferred_delivery_method', 'standard')
        )

    return user_profile


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
    Search products using the Langraph agentic pipeline with user profile from request

    Request body:
      {
        "query": "I need rice and tea for my kitchen",
        "user_profile": {                              # OPTIONAL
          "user_id": "user123",
          "budget_limit_lkr": 5000.0,
          "location": "Colombo, Sri Lanka",
          "dietary_needs": {
            "vegetarian": false,
            "vegan": false,
            "gluten_free": false,
            "dairy_free": false,
            "allergies": []
          },
          "brand_preferences": {
            "preferred_brands": ["Anchor", "Maliban"],
            "disliked_brands": []
          },
          "household_inventory": {
            "current_items": {},
            "low_stock_threshold": 2
          },
          "loyalty_membership": {
            "preferred_stores": ["glowmark.lk", "kapruka.com"],
            "memberships": {}
          }
        }
      }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'status': 'error', 'message': 'Missing query parameter'}), 400

        query = data['query'].strip()
        if not query:
            return jsonify({'status': 'error', 'message': 'Query cannot be empty'}), 400

        logger.info(f"🔍 Processing search query: {query}")

        # ===== NEW: Handle user profile from request =====
        user_profile_data = data.get('user_profile', None)
        request_orchestrator = None

        if user_profile_data:
            try:
                # Create UserProfile from request
                user_profile = create_user_profile_from_request(user_profile_data)
                logger.info(f"✅ Using user profile from request: {user_profile.user_id}")

                # Create NEW orchestrator with this profile
                request_orchestrator = ProductSearchOrchestrator(user_profile)

            except Exception as profile_error:
                logger.error(f"❌ Failed to parse user profile: {profile_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid user profile data: {str(profile_error)}'
                }), 400
        else:
            # Use global orchestrator with default profile
            logger.info("ℹ️  No user profile in request, using default orchestrator")
            if not orchestrator:
                return jsonify({'status': 'error', 'message': 'Langraph pipeline not available'}), 503
            request_orchestrator = orchestrator
        # ===== END NEW CODE =====

        try:
            # MODIFIED: Use request_orchestrator instead of orchestrator
            result = request_orchestrator.process_query(query)
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
                total_cost = budget_optimization_summary.get('total_cost', sum(item.get('price_lkr', 0) for item in optimized_items))
                selection_summary = budget_optimization_summary.get('selection_summary', {}) if isinstance(
                    budget_optimization_summary, dict) else {}
                final_total_cost = total_cost
                budget_percentage = round((total_cost / 1000.0) * 100, 1)
                delivery_time = budget_optimization_summary.get('total_delivery_time', 24.0)
                single_store_comparisons = budget_optimization_summary.get('single_store_comparisons', {})

                response_data = {
                    'status': 'success',
                    'query': query,
                    'user_id': user_profile_data.get('user_id', 'default') if user_profile_data else 'default',
                    'results': {
                        'optimized_items': optimized_items,
                        'total_cost': final_total_cost,
                        'budget_used_percentage': budget_percentage,
                        'estimated_delivery_hours': delivery_time,
                        'items_count': len(optimized_items),
                        'stores_used': list({item.get('website', 'unknown') for item in optimized_items}),
                        'optimization_method': result.get('optimization_method', 'Linear Programming + Multi-Criteria AI'),
                        'keywords_processed': result.get('keywords', []),
                        'total_items_found': len(optimized_items),
                        'single_store_comparisons': single_store_comparisons,
                        'pipeline_summary': {
                            'keywords_extracted': len(result.get('keywords', [])),
                            'items_acquired': sum(
                                len(items) for items in data_acquisition.values() if isinstance(items, list)),
                            'items_personalized': len(
                                result.get('personalized_data', {}).get('filtered_items', [])) if result.get(
                                'personalized_data') else 0,
                            'items_after_logistics': len(
                                result.get('logistics_optimization', {}).get('filtered_items', [])) if result.get(
                                'logistics_optimization') else 0,
                            'loyalty_savings': result.get('loyalty_summary', {}).get('total_savings',
                                                                                     0.0) if result.get(
                                'loyalty_summary') else 0.0,
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
                        'user_id': user_profile_data.get('user_id', 'default') if user_profile_data else 'default',
                        # NEW
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
                        'user_id': user_profile_data.get('user_id', 'default') if user_profile_data else 'default',
                        # NEW
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
                    'user_id': user_profile_data.get('user_id', 'default') if user_profile_data else 'default',  # NEW
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
# Multi-Agent Endpoints
# --------------------------
@app.route('/api/compare_carts', methods=['POST'])
def compare_carts():
    """
    Spawns StoreAgents to fetch carts concurrently.
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Simple keyword extraction for MVP
        keywords = [k.strip() for k in query.replace(',', ' ').split() if k.strip().lower() not in ["compare", "grocery", "cart", "list", "weekly", "bi-weekly", "items", "i", "need", "some"]]
        
        # Load fixed grocery list
        main_dir = os.path.dirname(os.path.abspath(__file__))
        list_path = os.path.join(main_dir, "data", "fixed_grocery_list.json")
        try:
            with open(list_path, 'r') as f:
                grocery_data = json.load(f)
            fixed_keywords = [item["keyword"] for item in grocery_data.get("weekly_items", [])]
            keywords.extend(fixed_keywords)
        except Exception as e:
            logger.error(f"Failed to load fixed grocery list: {e}")
            
        # Deduplicate
        keywords = list(set(keywords))
        
        if not keywords:
            return jsonify({'status': 'error', 'message': 'No keywords found to search'}), 400
            
        logger.info(f"🛒 Comparing carts for keywords: {keywords}")
        
        import threading
        from agents.store_agents import FairPriceAgent, RedMartAgent
        
        # Create a dummy LLM for the agents
        from langchain_ollama import ChatOllama
        from core.config import Config
        dummy_llm = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model=Config.GROQ_MODEL)
        
        fp_agent = FairPriceAgent(dummy_llm)
        rm_agent = RedMartAgent(dummy_llm)
        
        results = {}
        
        def fetch_fp():
            results["FairPrice"] = fp_agent.get_cart(keywords)
            
        def fetch_rm():
            results["RedMart"] = rm_agent.get_cart(keywords)
            
        t1 = threading.Thread(target=fetch_fp)
        t2 = threading.Thread(target=fetch_rm)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        return jsonify({
            'status': 'success',
            'query': query,
            'carts': [results.get("FairPrice"), results.get("RedMart")]
        }), 200

    except Exception as e:
        logger.exception("Failed to compare carts")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/execute_order', methods=['POST'])
def execute_order():
    """
    Executes an order using the designated StoreAgent.
    """
    # [PHASE 0]: Disabled simulated live ordering
    return jsonify({
        'status': 'error', 
        'message': 'NOT_IMPLEMENTED: Live ordering is disabled in fixture/demo mode.'
    }), 501


# ---------------------------------------------
# E2E FLOW: Orchestration and Checkout Endpoints
# ---------------------------------------------

@app.route('/api/shopping-list', methods=['GET'])
def get_shopping_list():
    """Return the editable shopping list from SQLModel repository"""
    try:
        with Session(engine) as session:
            repo = ShoppingListRepository(session)
            # Find the default list, or create one
            lists = repo.list_all()
            if not lists:
                sl = repo.create("Default List")
                # Seed it with something for now if empty? Or just return empty.
                repo.add_item(sl.id, "Oat Milk", 1)
                repo.add_item(sl.id, "Eggs", 1)
                lists = [sl]
            
            sl = lists[0]
            # Convert items to dict for frontend
            items = []
            for item in sl.items:
                items.append({
                    "id": str(item.id),
                    "item": item.keyword,
                    "quantity": item.quantity,
                    "must_have": item.must_have
                })
            return jsonify(items)
    except Exception as e:
        logger.error(f"Error reading shopping list: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/orchestrate', methods=['POST'])
def orchestrate_shopping():
    """
    Run shopping list through the new domain model to generate StoreQuotes.
    """
    try:
        from sqlmodel import select
        from domain.models.core import ProductCandidate, StoreSKUPreference
        from uuid import UUID
        
        with Session(engine) as session:
            repo = ShoppingListRepository(session)
            quote_repo = QuoteRepository(session)
            
            # 1. Get the current shopping list
            lists = repo.list_all()
            if not lists:
                return jsonify({"error": "No shopping list found."}), 400
            shopping_list = lists[0]
            
            # 2. Create Comparison Run
            run = quote_repo.create_run(shopping_list.id)
            
            # We'll support FairPrice and Little Farms
            results = {}
            for store_name in ["FairPrice", "Little Farms"]:
                items_data = []
                missing_items = []
                subtotal_cents = 0
                
                # Check each item
                for item in shopping_list.items:
                    # Find preferred sku
                    pref = session.exec(
                        select(StoreSKUPreference)
                        .where(StoreSKUPreference.keyword == item.keyword)
                        .where(StoreSKUPreference.store_name == store_name)
                    ).first()
                    
                    candidate = None
                    if pref:
                        candidate = session.exec(
                            select(ProductCandidate)
                            .where(ProductCandidate.retailer_sku == pref.preferred_retailer_sku)
                        ).first()
                    else:
                        # Fallback if no pref, just find cheapest candidate for this keyword in this store
                        # In the seed script, we used title containing keyword.
                        # For simplicity, we just check all candidates for the store whose title contains the keyword
                        candidates = session.exec(
                            select(ProductCandidate)
                            .where(ProductCandidate.store_name == store_name)
                        ).all()
                        
                        # Very simple match: keyword in title (case insensitive)
                        matches = [c for c in candidates if item.keyword.lower() in c.title.lower()]
                        if matches:
                            matches.sort(key=lambda c: c.price_cents)
                            candidate = matches[0]
                    
                    if candidate:
                        line_total = candidate.price_cents * item.quantity
                        subtotal_cents += line_total
                        items_data.append({
                            "candidate_id": str(candidate.id),
                            "raw_candidate_id": candidate.id,
                            "title": candidate.title,
                            "price_cents": candidate.price_cents,
                            "quantity": item.quantity,
                            "line_total_cents": line_total
                        })
                    else:
                        missing_items.append(item.keyword)
                
                # Use domain logic to calc delivery fee
                if store_name == "Little Farms":
                    # LF free delivery threshold $100
                    delivery_fee_cents = calculate_delivery_fee(subtotal_cents, 10000, 1498)
                else:
                    # FP free delivery threshold $79
                    delivery_fee_cents = calculate_delivery_fee(subtotal_cents, 7900, 399)
                
                is_complete = len(missing_items) == 0
                
                # Only create quote if we found some items (or maybe always?)
                if items_data:
                    quote = quote_repo.create_quote(run.id, store_name, subtotal_cents, delivery_fee_cents, is_complete)
                    for i_data in items_data:
                        quote_repo.add_line_item(
                            quote_id=quote.id,
                            candidate_id=UUID(str(i_data["raw_candidate_id"])),
                            quantity=i_data["quantity"],
                            line_total_cents=i_data["line_total_cents"]
                        )
                        
                    results[store_name] = {
                        "quote_id": str(quote.id),
                        "items": items_data,
                        "missing_items": missing_items,
                        "subtotal_cents": quote.subtotal_cents,
                        "delivery_fee_cents": quote.delivery_fee_cents,
                        "total_cents": quote.total_cents,
                        "is_complete": quote.is_complete,
                        # Display friendly formatting for the legacy frontend to use while it transitions
                        "subtotal": cents_to_display(quote.subtotal_cents),
                        "delivery_fee": cents_to_display(quote.delivery_fee_cents),
                        "total": cents_to_display(quote.total_cents)
                    }
                    
            # Use eligibility.py rank_quotes to rank them
            all_quotes = quote_repo.get_run_quotes(run.id)
            ranked_quotes = rank_quotes(all_quotes)
            
            # Sort the results dictionary by the ranked order (just for frontend)
            cheapest_store = ranked_quotes[0].store_name if ranked_quotes else None
            
            return jsonify({
                "run_id": str(run.id),
                "shopping_list_id": str(shopping_list.id),
                "comparisons": results,
                "cheapest_store": cheapest_store
            })

    except Exception as e:
        logger.error(f"Error orchestrating shopping: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/prepare_checkout', methods=['POST'])
def prepare_checkout():
    """
    Prepare checkout for a chosen store, returning delivery details
    """
    try:
        data = request.get_json()
        store = data.get("store")
        total = data.get("total", 0)
        delivery_fee = data.get("delivery_fee", 0)
        subtotal = data.get("subtotal", 0)
        
        if not store:
            return jsonify({"error": "Store is required"}), 400
            
        from agents.store_agents import FairPriceAgent, RedMartAgent, ShengSiongAgent, LittleFarmsAgent
        mock_llm = "mock"
        
        agent = None
        if store == "FairPrice":
            agent = FairPriceAgent(mock_llm)
        elif store == "RedMart":
            agent = RedMartAgent(mock_llm)
        elif store == "ShengSiong":
            agent = ShengSiongAgent(mock_llm)
        elif store == "LittleFarms":
            agent = LittleFarmsAgent(mock_llm)
        else:
            return jsonify({"error": f"Unknown store {store}"}), 400
            
        # Dynamically fetch details via Playwright
        details = agent.get_checkout_details()
        details["subtotal"] = subtotal
        details["delivery_fee"] = delivery_fee
        details["total"] = total
            
        return jsonify({
            "status": "success",
            "details": details
        })
            
    except Exception as e:
        logger.error(f"Error preparing checkout: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/confirm_checkout', methods=['POST'])
def confirm_checkout():
    """
    Finalize checkout for a chosen store
    """
    try:
        data = request.get_json()
        store = data.get("store")
        items = data.get("items", [])
        
        if not store:
            return jsonify({"error": "Store is required"}), 400
            
        from agents.store_agents import FairPriceAgent, RedMartAgent, ShengSiongAgent, LittleFarmsAgent
        mock_llm = "mock"
        
        agent = None
        if store == "FairPrice":
            agent = FairPriceAgent(mock_llm)
        elif store == "RedMart":
            agent = RedMartAgent(mock_llm)
        elif store == "ShengSiong":
            agent = ShengSiongAgent(mock_llm)
        elif store == "LittleFarms":
            agent = LittleFarmsAgent(mock_llm)
        else:
            return jsonify({"error": f"Unknown store {store}"}), 400
            
        success = agent.checkout(items)
        if success:
            return jsonify({"status": "success", "message": f"Successfully placed order at {store}!"})
        else:
            return jsonify({"status": "error", "message": f"Failed to checkout at {store}."}), 500
            
    except Exception as e:
        logger.error(f"Error during checkout: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



# --------------------------
# Main
# --------------------------
if __name__ == '__main__':
    print("🚀 Starting Python API server...")
    
    # [PHASE 0]: Refuse live ordering unless explicit flag is set
    import os
    live_purchase = os.environ.get("LIVE_PURCHASE_ENABLED", "false").lower() == "true"
    if not live_purchase:
        print("⚠️  LIVE_PURCHASE_ENABLED is false. Server starting in FIXTURE/DEMO mode.")
    else:
        print("🚨 LIVE_PURCHASE_ENABLED is true. Real transactions are allowed.")
    
    print("📍 API endpoints:")
    print("   - GET  /health")
    print("   - POST /api/search")
    print("   - GET  /api/search/test")
    print("   - POST /api/rag/chat")
    print("   - GET  /api/rag/source/<file>")
    print("   - POST /api/feedback")
    print("   - GET  /api/feedback/snapshot")
    print("   - GET  /api/feedback/health")
    print("   - POST /api/compare_carts")
    print("   - POST /api/execute_order")
    print()

    app.run(host='0.0.0.0', port=3004, debug=False, threaded=True)

