"""
Langraph State Management
"""
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ApplicationState(TypedDict):
    """Central state for the Langraph application"""
    messages: Annotated[list, add_messages]
    user_input: str
    keywords: List[str]
    product_data: Dict[str, List[Dict[str, Any]]]
    personalized_data: Dict[str, List[Dict[str, Any]]]
    personalization_summary: Dict[str, Any]
    formatted_output: str
    processing_stage: str
