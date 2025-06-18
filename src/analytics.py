import json
import datetime
import streamlit as st
from src.core.logger import get_logger

logger = get_logger(__name__)

LOG_FILE_PATH = "analytics_log.jsonl"

def log_event(event_name: str, **kwargs):
    """
    Logs an event to a JSON Lines file.
    Each event is a JSON object on a new line.
    """
    try:
        timestamp = datetime.datetime.utcnow().isoformat()
        workflow = st.session_state.get("workflow", "unknown_workflow")
        phase = st.session_state.get("phase", "unknown_phase")

        log_entry = {
            "utc_ts": timestamp,
            "workflow": workflow,
            "phase": phase,
            "event": event_name,
            **kwargs
        }
        with open(LOG_FILE_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.debug(f"Analytics event logged: {event_name}, Data: {log_entry}")
    except Exception as e:
        logger.error(f"Failed to log analytics event: {event_name}. Error: {e}", exc_info=True)

if __name__ == '__main__':
    # Example usage (for testing purposes)
    if 'workflow' not in st.session_state:
        st.session_state.workflow = "test_workflow"
    if 'phase' not in st.session_state:
        st.session_state.phase = "test_phase"

    log_event("test_event", detail="This is a test event.", custom_data={"value": 123})
    log_event("another_event", source="manual_test")

    print(f"Check '{LOG_FILE_PATH}' for logged events.")