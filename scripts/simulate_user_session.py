import sys
import os

# Add project root to sys.path if not already present, so 'src.' imports work
_PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJ_ROOT not in sys.path:
    sys.path.insert(0, _PROJ_ROOT)
    print(f"SIMULATOR_INFO: Added project root '{_PROJ_ROOT}' to sys.path for 'src.' imports.")
# --- IMPORTANT: RESOLVING IMPORT ERRORS ---
# If you see "No module named 'src'" or similar import errors when running this script,
# you likely need to tell Python where to find the 'src' directory.
#
# Option 1: Set PYTHONPATH (Recommended when running from project root)
#   - Windows PowerShell: $env:PYTHONPATH = "$(Resolve-Path ./src)"
#   - Windows CMD: set PYTHONPATH=src
#   - Bash/macOS/Linux: export PYTHONPATH=./src
#   After setting PYTHONPATH, run the script as normal: python scripts/simulate_user_session.py
#
# Option 2: Modify Import Statements (If PYTHONPATH is not feasible or script is run from elsewhere)
#   This script will attempt to import modules using 'src.' prefix first, then without it.
#   If errors persist, you might need to adjust the import paths below directly,
#   or ensure PYTHONPATH correctly points to the directory *containing* the 'src' folder.
#
# Note: The best approach (PYTHONPATH vs. modified imports) depends on your execution context
# and project structure. One or both may be needed.
# --- END IMPORTANT ---
"""
Simulate User Session Script

Purpose:
This script simulates user interactions with the chatbot application based on a
JSONL input file. It aims to mirror the real chatbot's response generation
and database logging behavior as closely as possible. This is useful for:
- Manual review of chatbot behavior over a scripted conversation.
- Generating test data for analysis.
- Automated testing of conversation flows and logging.

Integration with Core Application Logic:
- Chatbot Responses:
    - This script calls `src.conversation_manager.generate_assistant_response`.
    - If `generate_assistant_response`'s signature or location changes, update the
      import and the call in `get_real_chatbot_response` function below.
    - `generate_assistant_response` is async and might depend on Streamlit's
      session state (`st.session_state`). This script uses `asyncio.run()` to call it.
      For session state dependencies, you might need to:
        a) Modify `generate_assistant_response` to accept session state as a parameter.
        b) Mock `st.session_state` if it's imported directly by modules called by
           `generate_assistant_response`. (See TODO in `get_real_chatbot_response`).
- Database Logging:
    - This script calls a logging function (`log_message_to_db`)
      that should write to the application's main SQLite database.
    - If the logger import fails, a placeholder is used and a warning printed.
    - Ensure the logging function correctly records: session_id, user_input,
      bot_response, timestamp, source, module, and stage.
    - If new fields are added to the database schema for logging, update the
      `log_metadata` dictionary in `simulate_session` and the call to the
      logger function.

Adapting for New Modules or Conversation Stages:
- The `scripted_inputs.jsonl` file can specify a "module" for each user input.
  This is used for the "module" and "stage" metadata in logging.
- If your application introduces new modules or stages, ensure your
  `scripted_inputs.jsonl` reflects these, and that the logging function
  can handle them.

Running the Script:
- Ensure `scripted_inputs.jsonl` exists in the project root or update
  `SCRIPT_FILE_PATH`.
- Execute this script from the project root directory:
  `python scripts/simulate_user_session.py`
"""

import json
import uuid
import asyncio
from datetime import datetime, timezone

# --- Core Application Logic Imports ---
from src.conversation_manager import generate_assistant_response
from src.persistence_utils import log_message_to_db

# --- Configure Real Logging ---
# The sys.path modification at the top should handle imports.
# If 'log_message_to_db' cannot be imported, an ImportError will be raised,
# which is the desired behavior if the module or function is truly missing.
logging_function = log_message_to_db

def get_real_chatbot_response(user_input: str, session_id: str) -> str:
    """
    Gets response from the actual chatbot logic.
    Handles async call to `generate_assistant_response`.

    Args:
        user_input (str): The user's message.
        session_id (str): The current session ID (for logging/context).

    Returns:
        str: The chatbot's response.
    """
    print(f"SIMULATOR: Sending to chatbot (session: {session_id}): '{user_input}'")
    try:
        # TODO: If generate_assistant_response requires additional context (history, session state, etc.),
        #       provide dummy/default values or refactor as needed.
        response_text, _ = asyncio.run(generate_assistant_response(user_input))
        print(f"SIMULATOR: Received from chatbot: '{response_text}'")
        return response_text
    except Exception as e:
        print(f"SIMULATOR_ERROR: Error calling generate_assistant_response: {e}")
        print("  Ensure 'generate_assistant_response' can run outside Streamlit context or mock dependencies.")
        return f"SIMULATOR_ERROR_RESPONSE: Could not get response due to: {e}"

def simulate_session(script_path: str, chatbot_handler_func, logger_func):
    """
    Simulates a user session based on a script file.

    Args:
        script_path (str): Path to the .jsonl file with scripted inputs.
        chatbot_handler_func (callable): Function to get chatbot response.
                                         Expected signature: func(user_input: str, session_id: str) -> str
        logger_func (callable): Function to log messages.
                                Expected signature: func(session_uuid: str, timestamp: datetime, source: str, module: str, stage: str, user_message: Optional[str], bot_message: Optional[str], metadata: Optional[Dict])
    """
    session_id = str(uuid.uuid4())
    print(f"SIMULATOR: Starting simulated session: {session_id}")
    turn_counter = 0

    try:
        with open(script_path, 'r') as f:
            for line_number, line in enumerate(f, 1):
                turn_counter += 1
                print(f"\nSIMULATOR: Processing turn {turn_counter} (line {line_number}) for session {session_id}")
                try:
                    record = json.loads(line)
                    user_input = record.get("prompt")
                    module_name = record.get("module", "UnknownModule")
                    stage_name = record.get("stage", module_name)  # Default stage to module if not specified

                    if not user_input:
                        print(f"SIMULATOR_WARN: Skipping record with no input: {record} on line {line_number}")
                        continue

                    # 1. Send input to chatbot and capture response
                    bot_response = chatbot_handler_func(user_input, session_id)

                    # 2. Log input and response with metadata
                    current_datetime_obj = datetime.now(timezone.utc) # Get datetime object
                    
                    # Prepare additional metadata for the 'metadata' field of the logger
                    additional_log_metadata = {
                        "turn_number": turn_counter,
                        "script_line": line_number
                        # Add any other specific details you want in the JSON metadata blob
                    }

                    logger_func(
                        session_uuid=session_id,
                        timestamp=current_datetime_obj, # Pass datetime object
                        source="simulated_user_session_script", # Explicit source
                        module=module_name,
                        stage=stage_name,
                        user_message=user_input,
                        bot_message=bot_response,
                        metadata=additional_log_metadata # Pass the specific metadata dict
                    )

                except json.JSONDecodeError:
                    print(f"SIMULATOR_ERROR: Could not decode JSON from line {line_number}: {line.strip()}")
                except Exception as e:
                    print(f"SIMULATOR_ERROR: Error processing record on line {line_number} '{line.strip()}': {e}")
    except FileNotFoundError:
        print(f"SIMULATOR_ERROR: Script file not found at {script_path}")
        return None
    except Exception as e:
        print(f"SIMULATOR_ERROR: Failed to read or process script file {script_path}: {e}")
        return None

    print(f"\nSIMULATOR: Finished simulated session: {session_id} after {turn_counter} turns.")
    return session_id

def simulate_feedback(session_id: str, feedback_text: str, rating: int = None, logger_func=None):
    """
    Optionally logs simulated feedback for the session.
    This assumes a similar logging mechanism or a specific function for feedback.

    Args:
        session_id (str): The ID of the session to which feedback applies.
        feedback_text (str): The text of the feedback.
        rating (int, optional): A numerical rating if applicable.
        logger_func (callable): The logging function to use.
    """
    if logger_func is None:
        logger_func = logging_function

    print(f"SIMULATOR: Adding feedback for session {session_id}: '{feedback_text}' (Rating: {rating})")

    current_datetime_obj = datetime.now(timezone.utc) # Get datetime object
    
    # Prepare additional metadata for the 'metadata' field of the logger
    additional_feedback_metadata = {
        "rating": rating,
        "feedback_type": "general_session_feedback"
        # Add any other specific details for feedback
    }

    logger_func(
        session_uuid=session_id,
        timestamp=current_datetime_obj, # Pass datetime object
        source="simulated_feedback_entry", # Explicit source
        module="feedback_module", # Or derive from context
        stage="feedback_collection",
        user_message=None, # No direct user message for this type of log
        bot_message=feedback_text, # Feedback text can go into bot_message or a custom metadata field
        metadata=additional_feedback_metadata
    )
    print(f"SIMULATOR: Feedback for session {session_id} logged.")

if __name__ == "__main__":
    SCRIPT_FILE_PATH = "scripted_inputs.jsonl"

    chatbot_interaction_function = get_real_chatbot_response
    print("SIMULATOR: Starting user session simulation...")
    print(f"SIMULATOR: Using chatbot handler: {chatbot_interaction_function.__name__}")
    print(f"SIMULATOR: Using logger: {logging_function.__name__}")
    if logging_function.__name__ == "log_message_to_db_placeholder":
        print("SIMULATOR_WARN: Using PLACEHOLDER logging function. Logs will not be saved to the database.")
        print("SIMULATOR_WARN: Please configure the 'log_message_to_db' import in this script.")

    simulated_session_id = simulate_session(
        script_path=SCRIPT_FILE_PATH,
        chatbot_handler_func=chatbot_interaction_function,
        logger_func=logging_function
    )

    # Optionally, add simulated feedback
    if simulated_session_id:
        print("\nSIMULATOR: Simulating feedback entries...")
        simulate_feedback(
            session_id=simulated_session_id,
            feedback_text="The simulated student found the initial modules very clear but wanted more examples in Module 3.",
            rating=4,
            logger_func=logging_function
        )
        simulate_feedback(
            session_id=simulated_session_id,
            feedback_text="Overall, a good learning experience.",
            rating=5,
            logger_func=logging_function
        )

    print("\nSIMULATOR: Simulation complete.")
