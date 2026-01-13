from langchain_core.messages import SystemMessage, AIMessage
import json
from .models import AssistantResponse, Intent
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Define the System Prompt
SYSTEM_PROMPT = """
You are the elite AI Sales Representative for **AutoStream**, a premium SaaS platform for automated video editing.

### YOUR PRODUCT:
AutoStream helps content creators edit videos 10x faster using AI. 
- **Target Audience:** YouTubers, Instagram Influencers, TikTok Creators.
- **Key Value:** Save time, professional quality, AI captions.

### YOUR GOAL:
1. **Assist:** Answer questions about features/pricing accurately (using RAG context if provided).
2. **Qualify:** Identify when a user is interested in buying.
3. **Capture:** Smoothly collect their Name, Email, and Platform to generate a lead.

### SLOT EXTRACTION RULES (CRITICAL - PASSIVE EXTRACTION):
- **ALWAYS** check every message for: Name, Email, or Platform (YouTube/Instagram/TikTok), even if the user is asking a question.
- **Example:** "I am a YouTube creator, what is the price?" -> Answer price AND extract 'user_platform'="YouTube".
- **Example:** "My name is Ved, do you have discounts?" -> Answer discounts AND extract 'user_name'="Ved".
- If detected, fill the corresponding field in the structured output.

### INTENT CLASSIFICATION RULES:
- **CASUAL:** "Hi", "Hello", "How are you?". Also use this if you have just answered an inquiry using RAG context.
- **INQUIRY:** General questions about "price", "cost", "features", "4K".
  - Examples: "What is your pricing?", "How much is it?".
  - **Exception:** If the user is SELECTING a plan (e.g., "Basic Plan", "I choose Pro"), classify as HIGH_INTENT.
- **HIGH_INTENT:** 
  1. Clear intent to purchase or select a plan. (e.g., "I want to buy", "Sign me up").
  2. **DATA PROVISION:** If the user answers your question by providing Name, Email, or Platform, classify as HIGH_INTENT.
     - Example: "My name is Ved" -> HIGH_INTENT.
     - Example: "ved@test.com" -> HIGH_INTENT.

### DATA COLLECTION STRATEGY (When Intent is HIGH_INTENT):
- You need to collect: Name, Email, and Platform (e.g. YouTube).
- **CRITICAL:** Check the [[CURRENT KNOWN INFO]] section. **DO NOT ASK** for details that are already known/extracted.
  - If we extracted "YouTube" previously, do NOT ask "Which platform?". Just ask for Name/Email.
- You can ask for these details naturally. You may ask for multiple details at once if it flows well.
- **Goal:** Get the info efficiently but conversationally. Don't be too rigid.

### SALES MEMORY:
- If the user mentions constraints (e.g., "I'm a student"), save this to 'sales_notes'.
- If the user mentions goals (e.g., "I need 4K for YouTube"), save this to 'sales_notes'.

### TONE GUIDELINES:
- Be enthusiastic but professional.
- Be concise (mobile-friendly responses).
- **Never** make up pricing. If you don't know, ask the user to check the website.
"""

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.15,
)

structured_llm = llm.with_structured_output(AssistantResponse)

def chatbot_node(state):
    # Node logic for the Chatbot
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # Inject Context (Memory)
    known_info = []
    if state.get("user_name"):
        known_info.append(f"Name: {state['user_name']}")
    if state.get("user_email"):
        known_info.append(f"Email: {state['user_email']}")
    if state.get("user_platform"):
        known_info.append(f"Platform: {state['user_platform']}")
        
    if known_info or state.get("sales_notes"):
        context_str = "[[CURRENT KNOWN INFO]]\n" + "\n".join(known_info)
        if state.get("sales_notes"):
            context_str += f"\nNOTES: {state['sales_notes']}"
            
        messages.append(SystemMessage(content=context_str))
    
    # Add History
    messages.extend(state["messages"])

    # Invoke the LLM
    response = structured_llm.invoke(messages)

    output_messages = [AIMessage(content=response.content)]
    final_intent = response.intent

    # Check if we are ready to capture (All slots filled + High Intent)
    curr_name = response.user_name or state.get("user_name")
    curr_email = response.user_email or state.get("user_email")
    curr_platform = response.user_platform or state.get("user_platform")
    
    is_ready_for_capture = (
        final_intent == Intent.HIGH_INTENT 
        and curr_name 
        and curr_email 
        and curr_platform
    )

    # Explicitly track previous node to prevent loops
    last_node = state.get("last_node")
    
    if last_node == "rag_node":
        # We just used RAG to answer. We MUST stop the loop.
        final_intent = Intent.CASUAL
    elif last_node == "lead_capture_node":
        # We just captured a lead. We MUST stop the loop.
        final_intent = Intent.CASUAL
    elif response.intent == Intent.INQUIRY:
        # We are about to go to RAG. Suppress the immediate output.
        output_messages = []
    elif is_ready_for_capture:
        # We are about to go to Lead Capture. Suppress the immediate output to avoid double-talk.
        # The bot will speak AFTER the capture (in the next turn).
        output_messages = []

    # We always update the intent and the message history
    return_dict = {
        "messages": output_messages,
        "intent": final_intent,
        "last_node": "chatbot_node"
    }

    if response.user_name:
        return_dict["user_name"] = response.user_name
        
    if response.user_email:
        return_dict["user_email"] = response.user_email
        
    if response.user_platform:
        return_dict["user_platform"] = response.user_platform
    
    if response.sales_notes:
        return_dict["sales_notes"] = response.sales_notes
        
    return return_dict



def rag_node(state):
    # Load the data (In a real app, this would be a vector search)
    with open("data/knowledge_base.json", "r") as f:
        data = json.load(f)
    
    # We turn the JSON back into text so the LLM understands it
    context_text = f"Here is the info: {json.dumps(data, indent=2)}"
    
    system_message = SystemMessage(content=f"RAG CONTEXT: {context_text}")
    
    # Return the update
    return {
        "messages": [system_message],
        "last_node": "rag_node"
    }

# Mock Lead Capture API
def mock_lead_capture(name, email, platform):
    print(f"Lead captured successfully: {name}, {email}, {platform}")

def lead_capture_node(state):

    name = state.get("user_name")
    email = state.get("user_email")
    platform = state.get("user_platform")
    
    # Call the mock API
    mock_lead_capture(name, email, platform)
    
    # Reset the intent so the bot goes back to normal chatting
    return {
        "messages": [SystemMessage(content="Lead saved successfully. Thank the user.")],
        "intent": "casual",
        "last_node": "lead_capture_node"
    }
