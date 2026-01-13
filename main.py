import uuid
import dotenv
from src.graph import app

dotenv.load_dotenv()

def run_chat():
    # Generate a unique session ID
    # In a real web app, this would be the User ID or Session Cookie.
    thread_id = str(uuid.uuid4())
    
    # Configure the graph state
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n\033[1mAutoStream Agent\033[0m (Type 'q' to quit)")
    print("---------------------------------------")

    while True:
        # Get User Input
        try:
            user_input = input("\033[94mYou:\033[0m ") # Blue color for 'You'
        except EOFError:
            break

        if user_input.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break

        # Stream the Graph Events
        # stream_mode="values" returns the Full State at every step.
        events = app.stream(
            {"messages": [("user", user_input)]}, 
            config, 
            stream_mode="values"
        )

        # Process & Print Output
        for event in events:
            # DEBUG PRINT
            # print(f"DEBUG: Event Keys: {list(event.keys())}")
            
            # We filter to find the AI's response in the message list
            if "messages" in event:
                messages = event["messages"]
                if not messages:
                    continue
                    
                last_message = messages[-1]
                
                # DEBUG PRINT
                # print(f"DEBUG: Last Msg Type: {type(last_message)}")
                # print(f"DEBUG: Last Msg: {last_message}")
            
                # Only print if it's an AI message and it's NEW (not history)
                try:
                    # Check for LangChain Message Object
                    if hasattr(last_message, "type") and last_message.type == "ai":
                        print(f"\033[92mAgent:\033[0m {last_message.content}")
                    # Check for string
                    elif isinstance(last_message, str):
                         print(f"\033[92mAgent (str):\033[0m {last_message}")
                    # Check for dictionary (sometimes happens with json serialization)
                    elif isinstance(last_message, dict) and "content" in last_message:
                         print(f"\033[92mAgent (dict):\033[0m {last_message['content']}")
                    else:
                         # Ultimate fallback
                         # print(f"\033[92mAgent (unknown):\033[0m {last_message}")
                         pass
                except Exception as e:
                    print(f"Error processing message: {e}")

if __name__ == "__main__":
    run_chat()
