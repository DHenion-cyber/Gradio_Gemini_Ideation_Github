import streamlit as st
import json
import os
import datetime

# Placeholder for a simple file-based persistence.
# In a real application, this would interact with a database.

def _get_session_file_path(uuid_str: str) -> str:
    """Constructs the file path for a given session UUID."""
    # Ensure a directory for sessions exists
    session_dir = "sessions"
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    return os.path.join(session_dir, f"session_{uuid_str}.json")

def persist_session(uuid_str: str):
    """
    Saves conversation_history, scratchpad, and summaries from st.session_state
    to a persistent store (e.g., a JSON file).
    """
    session_data = {
        "conversation_history": st.session_state.get("conversation_history", []),
        "scratchpad": st.session_state.get("scratchpad", {}),
        "summaries": st.session_state.get("summaries", []),
        "stage": st.session_state.get("stage", "intake"),
        "turn_count": st.session_state.get("turn_count", 0),
        "intake_index": st.session_state.get("intake_index", 0),
        "token_usage": st.session_state.get("token_usage", {"session": 0, "daily": 0}),
        "last_summary": st.session_state.get("last_summary", ""),
        "start_timestamp": st.session_state.get("start_timestamp", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
        "user_id": st.session_state.get("user_id", uuid_str) # Ensure user_id is saved
    }
    file_path = _get_session_file_path(uuid_str)
    try:
        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=4)
        print(f"Session {uuid_str} persisted successfully.")
    except Exception as e:
        print(f"Error persisting session {uuid_str}: {e}")

def load_session(uuid_str: str):
    """
    Loads saved state for a given UUID into st.session_state.
    If the session file is not found, it calls initialize_conversation_state()
    from conversation_manager.py (assuming it's imported or accessible).
    """
    file_path = _get_session_file_path(uuid_str)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                session_data = json.load(f)

            # Populate st.session_state with loaded data
            st.session_state["conversation_history"] = session_data.get("conversation_history", [])
            st.session_state["scratchpad"] = session_data.get("scratchpad", {})
            st.session_state["summaries"] = session_data.get("summaries", [])
            st.session_state["stage"] = session_data.get("stage", "intake")
            st.session_state["turn_count"] = session_data.get("turn_count", 0)
            st.session_state["intake_index"] = session_data.get("intake_index", 0)
            st.session_state["token_usage"] = session_data.get("token_usage", {"session": 0, "daily": 0})
            st.session_state["last_summary"] = session_data.get("last_summary", "")
            st.session_state["start_timestamp"] = datetime.datetime.fromisoformat(session_data.get("start_timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()))
            st.session_state["user_id"] = session_data.get("user_id", uuid_str) # Ensure user_id is loaded

            print(f"Session {uuid_str} loaded successfully.")
        except Exception as e:
            print(f"Error loading session {uuid_str}: {e}")
            # If loading fails, re-initialize
            from conversation_manager import initialize_conversation_state
            initialize_conversation_state()
    else:
        print(f"Session file for {uuid_str} not found. Initializing new conversation state.")
        # If file not found, initialize new state
        from conversation_manager import initialize_conversation_state
        initialize_conversation_state()