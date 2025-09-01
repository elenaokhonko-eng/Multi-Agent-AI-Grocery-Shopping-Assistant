import os
os.environ["GROQ_API_KEY"] = "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"

# 1) (Only needed once per runtime)
# pip install -q langgraph langchain langchain-groq

from typing import Annotated, List, Dict
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage

# ----- Graph state -----
class State(TypedDict):
    messages: Annotated[list, add_messages]
    keywords: List[str]
    results: Dict[str, List[Dict[str, any]]]

graph_builder = StateGraph(State)

# ----- LLM (Groq) -----
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0,
    model_kwargs={
        "response_format": {"type": "json_object"}
    }
)

# ----- Node: Extract keywords with LLM -----
def extract_keywords_node(state: State):
    print("[DEBUG] Extracting keywords node...")
    last_msg = state["messages"][-1]
    print(f"[DEBUG] Last message: {last_msg}")
    if hasattr(last_msg, "content"):
        user_message = last_msg.content
    elif isinstance(last_msg, dict) and "content" in last_msg:
        user_message = last_msg["content"]
    else:
        user_message = str(last_msg)
    print(f"[DEBUG] User message: {user_message}")
    prompt = f"""Extract only the important keywords from the following sentence and return them as a JSON object with a "keywords" array.
    
    Sentence: "{user_message}"
    
    Rules:
    - Extract only nouns and important adjectives
    - Ignore common words like 'I', 'need', 'want', 'and', 'the', 'a', etc.
    - Return a valid JSON object
    - Example format: {{"keywords": ["milk", "tea", "organic"]}}
    
    Respond with valid JSON only:"""
    print(f"[DEBUG] LLM prompt: {prompt}")
    ai_msg = llm.invoke([{"role": "user", "content": prompt}])
    print(f"[DEBUG] LLM response: {ai_msg.content}")
    # Try to parse keywords from LLM output
    import json
    import re
    try:
        # Parse JSON response
        response_json = json.loads(ai_msg.content.strip())
        keywords = response_json.get("keywords", [])
        
        if not isinstance(keywords, list):
            keywords = [str(keywords)]
    except Exception as e:
        print(f"[DEBUG] JSON parsing failed: {e}, falling back to simple extraction")
        # Simple fallback: extract words from the response
        words = re.findall(r'"([^"]*)"', ai_msg.content)
        keywords = words if words else [user_message]
    print(f"[DEBUG] Extracted keywords: {keywords}")
    return {"messages": state["messages"] + [ai_msg], "keywords": keywords}

# ----- Node: Retrieve items from Web_scraper -----
def retrieve_items_node(state: State):
    print("[DEBUG] Retrieving items node...")
    keywords = state.get("keywords", [])
    print(f"[DEBUG] Keywords to retrieve: {keywords}")
    results = {}
    try:
        # Temporary mock retrieval to test the flow
        print(f"[DEBUG] Using mock retrieval for testing")
        for kw in keywords:
            print(f"[DEBUG] Mock retrieving items for keyword: {kw}")
            # Mock items that would come from Web_scraper with detailed information
            mock_items = [
                {
                    "title": f"Premium {kw.title()}", 
                    "price_lkr": 250.0,
                    "website": "glowmark.lk",
                    "source_url": f"https://glowmark.lk/product/premium-{kw}",
                    "collection": "glowmark",
                    "similarity_score": 0.95
                },
                {
                    "title": f"Organic {kw.title()}", 
                    "price_lkr": 180.0,
                    "website": "kapruka.com",
                    "source_url": f"https://kapruka.com/product/organic-{kw}",
                    "collection": "kapruka",
                    "similarity_score": 0.87
                },
                {
                    "title": f"Fresh {kw.title()}", 
                    "price_lkr": 320.0,
                    "website": "onlinekade.lk",
                    "source_url": f"https://onlinekade.lk/product/fresh-{kw}",
                    "collection": "onlinekade",
                    "similarity_score": 0.92
                }
            ]
            print(f"[DEBUG] Mock retrieved items: {mock_items}")
            # Store complete item details instead of just titles
            results[kw] = mock_items
            
        # TODO: Replace with actual Web_scraper integration once dependency issues are resolved
        # import importlib.util
        # import os
        # import sys
        # 
        # # Add Web_scraper to Python path
        # webscraper_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Web_scraper'))
        # if webscraper_path not in sys.path:
        #     sys.path.insert(0, webscraper_path)
        # print(f"[DEBUG] Added to sys.path: {webscraper_path}")
        # 
        # # Now import the module
        # from retrieval.item_retriever import find_best_items_sync
        # print(f"[DEBUG] Successfully imported find_best_items_sync")
        # 
        # for kw in keywords:
        #     print(f"[DEBUG] Retrieving items for keyword: {kw}")
        #     items = find_best_items_sync(kw, max_results=5)
        #     print(f"[DEBUG] Retrieved items: {items}")
        #     results[kw] = [item.get("title", str(item)) for item in items]
    except Exception as e:
        print(f"[DEBUG] Error during retrieval: {e}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        results = {kw: [f"Error: {e}"] for kw in keywords}
    print(f"[DEBUG] Final results: {results}")
    return {"messages": state["messages"], "results": results}

# ----- Node: Output results -----
def output_node(state: State):
    print("[DEBUG] Output node...")
    results = state.get("results", {})
    print(f"[DEBUG] Results to output: {results}")
    
    output = "\n" + "="*60 + "\n"
    output += "KEYWORD MATCHES WITH DETAILED INFORMATION\n"
    output += "="*60 + "\n"
    
    for kw, items in results.items():
        output += f"\n🔍 KEYWORD: {kw.upper()}\n"
        output += "-" * 40 + "\n"
        
        for i, item in enumerate(items, 1):
            output += f"\n{i}. {item.get('title', 'N/A')}\n"
            output += f"   💰 Price: LKR {item.get('price_lkr', 0):.2f}\n"
            output += f"   🌐 Website: {item.get('website', 'N/A')}\n"
            output += f"   🔗 URL: {item.get('source_url', 'N/A')}\n"
            output += f"   📦 Collection: {item.get('collection', 'N/A')}\n"
            if item.get('similarity_score'):
                output += f"   📊 Similarity: {item.get('similarity_score', 0):.2f}\n"
            output += "\n"
    
    output += "="*60 + "\n"
    print(output)
    return state

graph_builder.add_node("extract_keywords", extract_keywords_node)
graph_builder.add_node("retrieve_items", retrieve_items_node)
graph_builder.add_node("output", output_node)
graph_builder.add_edge(START, "extract_keywords")
graph_builder.add_edge("extract_keywords", "retrieve_items")
graph_builder.add_edge("retrieve_items", "output")
graph_builder.add_edge("output", END)

graph = graph_builder.compile()

if __name__ == "__main__":
    user_input = input("Enter a sentence with keywords: ")
    result = graph.invoke({"messages": [{"role": "user", "content": user_input}]})
