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

graph_builder = StateGraph(State)

# ----- LLM (Groq) -----
llm = ChatGroq(model="llama3-70b-8192", temperature=0)

# ----- Node: Extract keywords with LLM -----
def extract_keywords_node(state: State):
    user_message = state["messages"][-1]["content"]
    prompt = f"Extract keywords from the following sentence as a Python list: '{user_message}'"
    ai_msg = llm.invoke([{"role": "user", "content": prompt}])
    # Try to parse keywords from LLM output
    import ast
    try:
        keywords = ast.literal_eval(ai_msg.content)
        if not isinstance(keywords, list):
            keywords = [ai_msg.content]
    except Exception:
        keywords = [ai_msg.content]
    return {"messages": state["messages"] + [ai_msg], "keywords": keywords}

# ----- Node: Retrieve items from Web_scraper -----
def retrieve_items_node(state: State):
    keywords = state.get("keywords", [])
    results = {}
    try:
        import importlib.util
        import os
        item_retriever_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Web_scraper/retrieval/item_retriever.py'))
        spec = importlib.util.spec_from_file_location("item_retriever", item_retriever_path)
        item_retriever = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(item_retriever)
        find_best_items_sync = item_retriever.find_best_items_sync
        results = {}
        for kw in keywords:
            items = find_best_items_sync(kw, max_results=5)
            results[kw] = [item.get("title", str(item)) for item in items]
    except Exception as e:
        results = {kw: [f"Error: {e}"] for kw in keywords}
    return {"messages": state["messages"], "results": results}

# ----- Node: Output results -----
def output_node(state: State):
    results = state.get("results", {})
    output = "\nKeyword Matches:\n"
    for kw, items in results.items():
        output += f"{kw}: {', '.join(items)}\n"
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
