import json
import uuid
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()


# Placeholder for the actual chatbot interaction function
# This function should take user_input (str) and session_id (str)
# and return the chatbot's response (str).
def get_chatbot_response(user_input: str, session_id: str) -> str:
    """
    Placeholder function to simulate chatbot interaction.
    Replace this with the actual function/API call.
    """
    print(f"SIMULATOR: Sending to chatbot (session: {session_id}): '{user_input}'")
    # Example: response = actual_chatbot_function(user_input, session_id)
    response = f"Chatbot echo: {user_input}"
    print(f"SIMULATOR: Received from chatbot: '{response}'")
    return response

# Assumed logging function from src/logging_utils.py
# from src.logging_utils import log_message_to_db

# Placeholder for the logging function if src.logging_utils is not available
# This is to allow the script to be runnable for now.
# The user should replace this with the actual import and function.
def log_message_to_db(session_id: str, user_message: str, bot_message: str, metadata: dict):
    """
    Placeholder for the actual logging function.
    """
    print(f"SIMULATOR_LOG: Logging to DB (session: {session_id}):")
    print(f"  User: {user_message}")
    print(f"  Bot: {bot_message}")
    print(f"  Metadata: {metadata}")
    # Example: actual_log_message_to_db(
    #     session_id=session_id,
    #     user_message=user_message,
    #     bot_message=bot_message,
    #     metadata=metadata
    # )
    pass

def simulate_session(script_path: str, chatbot_handler_func, logger_func):
    """
    Simulates a user session based on a script file.

    Args:
        script_path (str): Path to the .jsonl file with scripted inputs.
        chatbot_handler_func (callable): Function to get chatbot response.
                                         Expected signature: func(user_input: str, session_id: str) -> str
        logger_func (callable): Function to log messages.
                                Expected signature: func(session_id: str, user_message: str, bot_message: str, metadata: dict)
    """
    session_id = str(uuid.uuid4())
    print(f"SIMULATOR: Starting simulated session: {session_id}")

    with open(script_path, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                user_input = record.get("input")
                module_phase = record.get("module", "Unknown") # 'phase' or 'module'

                if not user_input:
                    print(f"SIMULATOR_WARN: Skipping record with no input: {record}")
                    continue

                # 2. Send input to chatbot and capture response
                bot_response = chatbot_handler_func(user_input, session_id)

                # 3. Log input and response with metadata
                timestamp = datetime.utcnow().isoformat()
                log_metadata = {
                    "timestamp": timestamp,
                    "source": "simulated",
                    "module": module_phase, # Using 'module' as per scripted_inputs.jsonl
                    # Add other relevant metadata if needed
                }
                logger_func(
                    session_id=session_id,
                    user_message=user_input,
                    bot_message=bot_response,
                    metadata=log_metadata
                )

            except json.JSONDecodeError:
                print(f"SIMULATOR_ERROR: Could not decode JSON from line: {line.strip()}")
            except Exception as e:
                print(f"SIMULATOR_ERROR: Error processing record '{line.strip()}': {e}")

    print(f"SIMULATOR: Finished simulated session: {session_id}")
    return session_id

def simulate_feedback(session_id: str, feedback_text: str, rating: int = None):
    """
    Optionally logs simulated feedback for the session.
    This assumes a similar logging mechanism or a specific function for feedback.
    For now, it will use the same logger_func with a special message type.

    Args:
        session_id (str): The ID of the session to which feedback applies.
        feedback_text (str): The text of the feedback.
        rating (int, optional): A numerical rating if applicable.
    """
    print(f"SIMULATOR: Adding feedback for session {session_id}: '{feedback_text}'")
    # This is a simplified approach. The actual implementation might involve
    # writing to a different table (e.g., general_session_feedback)
    # or using a different logging function.
    # For now, we'll log it as a special "feedback" message.

    timestamp = datetime.utcnow().isoformat()
    feedback_metadata = {
        "timestamp": timestamp,
        "source": "simulated_feedback",
        "type": "general_session_feedback", # To distinguish it
        "rating": rating
    }
    # Using the main logger for simplicity; replace if a dedicated feedback logger exists
    log_message_to_db(
        session_id=session_id,
        user_message="N/A (Feedback Entry)", # Or the last user prompt
        bot_message=feedback_text, # Storing feedback text as "bot_message" for this placeholder
        metadata=feedback_metadata
    )
    print(f"SIMULATOR: Feedback for session {session_id} logged.")


if __name__ == "__main__":
    # Configuration
    SCRIPT_FILE_PATH = "scripted_inputs.jsonl" # Relative to project root

    # --- Integration Points ---
    # 1. Replace 'get_chatbot_response' with the actual function from your application
    #    that handles user input and returns the chatbot's response.
    #    Example: from src.streamlit_app import handle_user_query
    #             chatbot_interaction_function = handle_user_query
    chatbot_interaction_function = get_chatbot_response

    # 2. Ensure 'log_message_to_db' is correctly imported from 'src.logging_utils'
    #    or replace 'log_message_to_db_placeholder' with the actual logging function.
    #    Example: from src.logging_utils import log_message_to_db
    #             logging_function = log_message_to_db
    logging_function = log_message_to_db # Using the placeholder for now

    print("SIMULATOR: Starting user session simulation...")

    # Run the simulation
    simulated_session_id = simulate_session(
        script_path=SCRIPT_FILE_PATH,
        chatbot_handler_func=chatbot_interaction_function,
        logger_func=logging_function
    )

    # Optionally, add simulated feedback
    if simulated_session_id:
        simulate_feedback(
            session_id=simulated_session_id,
            feedback_text="The simulated student found the initial modules very clear but wanted more examples in Module 3.",
            rating=4
        )
        simulate_feedback(
            session_id=simulated_session_id,
            feedback_text="Overall, a good learning experience.",
            rating=5
        )

    print("SIMULATOR: Simulation complete.")