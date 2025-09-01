import os
os.environ["GROQ_API_KEY"] = "###replace later###"

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
    # TODO: Replace with actual import from Web_scraper
    # from Web_scraper.retrieval.similarity_search import retrieve_similar_items
    # results = retrieve_similar_items(keywords)
    # For now, simulate retrieval
    results = {kw: [f"Item matching {kw}"] for kw in keywords}
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
