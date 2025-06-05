import logging
import json
import os
import datetime
import asyncio
import sys

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from typing import Dict
from pydantic import BaseModel

# Mock Streamlit for non-Streamlit execution
class MockStreamlitModuleSingleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockStreamlitModuleSingleton, cls).__new__(cls)
            cls._instance.session_state = {}
            cls._instance.query_params = {}
        return cls._instance
    def warning(self, text): print(f"Streamlit Warning: {text}")
    def error(self, text): print(f"Streamlit Error: {text}")

# Ensure mock Streamlit is in sys.modules BEFORE any imports that might use it
if 'streamlit' not in sys.modules or not isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
    sys.modules['streamlit'] = MockStreamlitModuleSingleton()

# Import necessary modules from the main application
from src.conversation_manager import initialize_conversation_state, generate_assistant_response
from src.constants import EMPTY_SCRATCHPAD

# TruLens Imports
from trulens.core import Tru, Feedback
from trulens.apps.custom import TruCustomApp as TruApp, instrument
from simulations.gemini_feedback import GeminiFeedbackProvider

# Ensure the logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1.1 Simulated User Personas
user_personas = [
    {
        "name": "Startup Clinician",
        "intro": "I'm a practicing nurse practitioner interested in using digital tools to improve chronic disease management.",
        "goal": "Wants to reduce hospital readmissions via remote monitoring.",
        "preferred_focus": "Patient Impact"
    },
    {
        "name": "Tech Researcher",
        "intro": "I have a background in software engineering and data science.",
        "goal": "Interested in AI for personalized mental health support.",
        "preferred_focus": "New Technology"
    }
]

# 2.1 & 2.2 Configure Evaluation Environment & Criteria
def build_feedbacks():
    """
    Builds and returns a list of Feedback objects.
    Each call to this function creates a new GeminiFeedbackProvider instance,
    ensuring that Feedback objects capture the provider instance current at their creation time.
    """
    # Instantiate provider inside the function so each set of feedbacks gets a fresh one
    # This is key for tests to mock GeminiFeedbackProvider *before* feedbacks are built.
    local_provider = GeminiFeedbackProvider()

    def make_feedback_internal(name, question):
        # Capture local_provider
        return Feedback(
            lambda inp, out: local_provider.ask(question, inp, out),
            name=name
        ).on_input_output()

    helpfulness = make_feedback_internal("Helpfulness", "How helpful is this response to the user?")
    relevance = make_feedback_internal("Relevance", "How relevant is this response to the user's intent?")
    alignment = make_feedback_internal("Alignment", "Does this response align with the user's stated goal?")
    empowerment = make_feedback_internal("User Empowerment", "Does this response empower or guide the user to take meaningful next steps?")
    coaching_tone = make_feedback_internal("Coaching Tone", "Does the assistant speak in a tone that is supportive, constructive, and encouraging?")
    
    return [helpfulness, relevance, alignment, empowerment, coaching_tone]

# Initialize feedbacks for the main runner script
# The `provider` instance used by these feedbacks is encapsulated within build_feedbacks
feedbacks = build_feedbacks()
# The global `provider` variable is no longer strictly needed here if only used for feedbacks.
# If it was used elsewhere, it would need to be handled. For now, assuming its primary
# use was for the feedbacks list. Tests will mock GeminiFeedbackProvider class, then call build_feedbacks.

# Initialize TruLens
# Use TRULENS_DATABASE_URL environment variable if set, otherwise default
tru = Tru(database_url=os.getenv("TRULENS_DATABASE_URL", "sqlite:///default.sqlite"))

# Start TruLens dashboard only if not in a test environment
if os.getenv("TRULENS_DATABASE_URL") != "sqlite:///mini.sqlite":
    tru.run_dashboard()

# Re-introduce ChatbotAppWrapper as a Pydantic BaseModel
@instrument
class ChatbotAppWrapper(BaseModel):
    app_name: str = "MyCustomChatbotApp"

    class Config:
        extra = 'allow'

    @instrument
    async def __call__(self, input_text: str) -> str:
        st_session_state = sys.modules['streamlit'].session_state

        # Harden session_state
        for k, v in {
            "scratchpad": EMPTY_SCRATCHPAD.copy(),
            "conversation_history": [],
            "summaries": [],
            "token_usage": {"session": 0, "daily": 0}
        }.items():
            st_session_state.setdefault(k, v)

        if "conversation_history" not in st_session_state or not st_session_state["conversation_history"]: # Ensure it's not empty if it exists
            # If conversation_history is missing or empty, it implies other states might be missing too.
            # initialize_conversation_state should set up all required keys including conversation_history.
            initialize_conversation_state(new_chat=True)
        
        st_session_state["conversation_history"].append({
            "role": "user",
            "text": input_text,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

        assistant_response = await generate_assistant_response(input_text)
        return assistant_response

# Instantiate the wrapper
run_chatbot_wrapped = ChatbotAppWrapper()

async def simulate_chat(persona: Dict[str, str], num_turns: int = 10):
    logger.info(f"\n--- Simulating chat for: {persona['name']} ---")
    session_transcript = []
    tru_app = TruApp(
        app_name=f"gemini_simulated_chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        app=run_chatbot_wrapped,
        feedbacks=feedbacks
    )

    last_bot_message = ""
    initialize_conversation_state(new_chat=True)
    for turn_num in range(1, num_turns + 1):
        logger.info(f"\nTurn {turn_num}:")
        if turn_num == 1:
            user_message = persona["intro"]
        else:
            user_message = f"Building on that, how can we achieve {persona['goal']} focusing on {persona['preferred_focus']}? The assistant just said: {last_bot_message}"
        logger.info(f"User ({persona['name']}): {user_message}")
        
        app_output, record = tru_app.with_record(run_chatbot_wrapped, user_message)
        # Block until all feedback futures finish
        logger.info(f"DEBUG: Calling record.wait_for_feedback_results() for record_id {record.record_id}")
        finished = record.wait_for_feedback_results()
        logger.info(f"DEBUG: 'finished' object from wait_for_feedback_results(): {finished}")
        
        # Standardized extraction of scores
        # `finished` is a dict of {Feedback: FeedbackResultFuture}
        # `getattr(res, "result", res)` will access `res.result` if `res` is a FeedbackResultFuture.
        # If `res` were already a resolved score (not the case here), it would return `res`.
        raw_scores_from_futures = {
            fb.name: getattr(res, "result", res)
            for fb, res in finished.items()
            if fb and hasattr(fb, 'name') and res is not None # Ensure Feedback obj and ResultFuture obj exist
        } if finished else {}

        # Filter out any scores that resolved to None
        scores = {k: v for k, v in raw_scores_from_futures.items() if v is not None}
        
        if not finished:
            logger.warning("DEBUG: 'finished' object (from record.wait_for_feedback_results) was empty or None.")
        elif not scores and raw_scores_from_futures:
            logger.warning(f"DEBUG: All scores resolved to None. Raw scores from futures: {raw_scores_from_futures}")
        elif not scores:
            logger.warning(f"DEBUG: No scores were processed. 'finished' was {finished}, raw_scores_from_futures was {raw_scores_from_futures}")
            
        assistant_response = await app_output

        if isinstance(assistant_response, tuple):
            assistant_response = assistant_response[0]
        
        last_bot_message = assistant_response
        
        logger.info(f"DEBUG: Scores for current turn (before append): {scores}")
        session_transcript.append({
            "turn_number": turn_num,
            "role": "user",
            "message": user_message,
            "assistant_response": assistant_response,
            "scores": scores
        })
        logger.info(f"DEBUG: session_transcript after append (last entry): {session_transcript[-1]}")
        logger.info(f"Assistant: {assistant_response}")

    tru_app.wait_for_feedback_results() # Block until all feedback futures finish
    session_average_scores = {}
    if session_transcript:
        # Aggregate scores per session
        # Ensure session_transcript[0]["scores"] exists before accessing its keys
        if session_transcript and "scores" in session_transcript[0]:
            session_average_scores = {
                k: sum(t["scores"][k] for t in session_transcript if k in t["scores"]) / len(session_transcript)
                for k in session_transcript[0]["scores"]
            }
        logger.info(f"Average scores: {session_average_scores}")
    else:
        logger.warning("Session transcript is empty, cannot calculate average scores.")

    log_filename = os.path.join(LOGS_DIR, f"{persona['name'].replace(' ', '_')}_chat.json")
    
    # Prepare data to be dumped, including both transcript and average scores
    output_data = {
        "session_transcript": session_transcript,
        "session_average_scores": session_average_scores
    }

    with open(log_filename, "w") as f:
        json.dump(output_data, f, indent=4)
    logger.info(f"Simulation transcript and scores saved to {log_filename}")

async def main():
    for persona in user_personas:
        await simulate_chat(persona)

if __name__ == "__main__":
    asyncio.run(main())