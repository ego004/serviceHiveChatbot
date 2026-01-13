import operator
from typing import Annotated, List, Union, TypedDict
from langgraph.graph.message import add_messages
from .models import Intent

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    intent: Intent
    user_name: Union[str, None]
    user_email: Union[str, None]
    user_platform: Union[str, None]
    sales_notes: Union[str, None]
    last_node: str
