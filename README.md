# AutoStream Agent: Social-to-Lead Workflow

This project implements an intelligent Conversational AI Agent for **AutoStream**, a SaaS platform for video editing. Built with **LangGraph** and **Google Gemini 2.5 Flash**, the agent is designed to autonomously qualify leads, answer product queries using RAG, and capture structured lead data in a conversational manner.

## Project Structure

```bash
├── data/          # Knowledge base (Pricing & Features)
│   ├── knowledge_base.json       # LangGraph definition, routing logic, and persistence
├── src/
│   ├── graph.py       # LangGraph definition, routing logic, and persistence
│   ├── nodes.py       # Core logic: Chatbot, RAG retrieval, and Lead Capture nodes
│   ├── models.py      # Pydantic schemas for Structured Output
│   ├── state.py       # AgentState definition (TypedDict)
├── main.py            
└── docker-compose.yml 
```

## Quick Start

### Prerequisites
- Python 3.9+ or Docker
- Google Gemini API Key

### Running with Docker (Recommended)
1. Create a `.env` file from `.env.example`:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```
2. Build and run the container:
   ```bash
   docker-compose up --build
   ```
3. Attach to the interactive CLI:
   ```bash
   docker attach autostream_agent
   ```

### Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the agent:
   ```bash
   python main.py
   ```

---

## Architecture Decisions

### Why LangGraph?
I selected **LangGraph** over AutoGen for this specific use case because the workflow requires precise, deterministic control over the state transitions. AutoGen is excellent for multi-agent conversation, but for a structured sales funnel (Inquiry -> Qualify -> Capture), a **State Graph** provides superior reliability.
*   **Cyclic Graph:** Allows the agent to loop back (e.g., retrieving RAG data and then continuing the conversation) without losing context.
*   **Persistence:** LangGraph's checkpointer mechanism (`MemorySaver`) ensures robust session management, allowing the agent to remember details provided 5-10 turns ago.

### State Management
State is managed via a `TypedDict` (`AgentState`) passed between nodes.
*   **Conversation History:** Handled via the `add_messages` reducer, ensuring a complete log of the dialogue.
*   **Slot Filling:** Fields like `user_name` and `user_platform` are updated destructively/mergingly. Once a slot is filled (e.g., "YouTube"), it persists in the state.
*   **Context Injection:** The bot checks the extracted slots before every turn. If `user_platform` is known, it is injected into the System Prompt context, preventing the bot from asking redundant questions.

### Passive Extraction Strategy
To handle non-linear conversations (e.g., "I am a YouTube creator, what is the price?"), the model uses a chain-of-thought approach.
1.  **Reasoning Step:** The model first analyzes the message for entities (Name, Email, Platform) in a hidden reasoning block.
2.  **Extraction:** If entities are found, they are extracted immediately, even if the user's primary intent was an Inquiry.
3.  **Response:** The model then generates the response, already "aware" of the extracted data.

---

## WhatsApp Integration Strategy

To deploy this agent on WhatsApp, I would use the **Meta Cloud API** or **Twilio AIP** with a webhook architecture:

I would Create a Python web server to receive inbound webhooks from WhatsApp. Then, I would use the WhatsApp `wa_id` (phone number) as the `thread_id` for the LangGraph checkpointer. This maps the WhatsApp user uniquely to a persistent graph session.

    *   **Inbound:** When a webhook arrives, push the message to the LangGraph executor using `app.invoke`.
    *   **Outbound:** The graph's response content is sent back to the WhatsApp API endpoint (`POST /messages`).
NOTE: **Media & Rich Text:** The `AssistantResponse` schema can be extended to support WhatsApp interactive messages to improve conversion rates.
