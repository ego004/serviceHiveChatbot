from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Intent(str, Enum):
    CASUAL = "casual"
    INQUIRY = "inquiry"
    HIGH_INTENT = "high_intent"

class AssistantResponse(BaseModel):
    """
    The structured response we expect from the LLM.
    """
    # Chain of thought reasoning
    reasoning: str = Field(
        description="Briefly analyze the user's message. Explicitly check: 'Did the user mention Name? Email? Platform?' regardless of the question."
    )

    # The actual reply to the user
    content: str = Field(
        description="Your natural language response to the user. Maintain a helpful, professional, and persuasive sales tone. Keep responses under 3 sentences unless explaining complex features."
    )
    # The detected intent
    intent: Intent = Field(
        description="Analyze the user's IMMEDIATE goal. \n"
        "- 'casual': Greetings, chit-chat, or off-topic. \n"
        "- 'inquiry': Asking about pricing, features, capabilities, or comparisons. \n"
        "- 'high_intent': Explicit desire to buy, sign up, start a trial, or 'purchase'.",
    )

    # The data capture fields (initially None)
    user_name: Optional[str] = Field(
        description="Extract the user's name ONLY if explicitly stated (e.g., 'I am Vedant'). Do NOT guess. Return None if unknown.", 
        default=None
    )
    user_email: Optional[str] = Field(
        description="Extract the user's email address. Be flexible with typos (e.g., capture 'user@protonme' even if dot is missing).", 
        default=None
    )
    user_platform: Optional[str] = Field(
        description="Extract the content platform they use (e.g., YouTube, Instagram, TikTok). Return None if unknown.", 
        default=None
    )
    
    # The LLM will fill this if it notices something interesting

    sales_notes: Optional[str] = Field(
        description="Extract strategic insights to aid future sales. Capture: Budget constraints, specific feature needs (4K, AI), or user role (student, pro). \n"
        "Example: 'User is a student on a budget' or 'User needs 4K rendering'.",
        default=None
    )
