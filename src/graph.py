from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import chatbot_node, rag_node, lead_capture_node
from .models import Intent

# Define the Router Logic
def route_intent(state):
    """
    This function looks at the State and decides the NEXT node.
    It returns the NAME of the node to go to.
    """
    intent = state["intent"]
    
    # User asks about price -> Go to RAG
    if intent == Intent.INQUIRY:
        return "rag_node"
    
    # User wants to buy -> Check if we have data
    if intent == Intent.HIGH_INTENT:
        name = state.get("user_name")
        email = state.get("user_email")
        platform = state.get("user_platform")
        
        # Only go to 'lead_capture' if ALL fields are present
        if name and email and platform:
            return "lead_capture_node"
        else:
            # If data is missing, go to END. 
            # (The Chatbot already asked for the missing info in the previous step)
            return END
            
    # Casual chat -> Stop and wait for user
    return END

# Initialize the Graph
workflow = StateGraph(AgentState)

workflow.add_node("chatbot_node", chatbot_node)
workflow.add_node("rag_node", rag_node)
workflow.add_node("lead_capture_node", lead_capture_node)

workflow.set_entry_point("chatbot_node")

workflow.add_conditional_edges(
    "chatbot_node",
    route_intent,
    {
        "rag_node": "rag_node",
        "lead_capture_node": "lead_capture_node",
        END: END
    }
)

workflow.add_edge("rag_node", "chatbot_node")

workflow.add_edge("lead_capture_node", "chatbot_node")

# Add Persistence
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
