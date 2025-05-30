import json
import os
import datetime
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel # Re-add BaseModel import

# Import necessary modules from the main application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from conversation_manager import initialize_conversation_state, generate_assistant_response
from llm_utils import query_gemini

# TruLens Imports
from trulens.core import Tru, Feedback
from trulens.apps.custom import TruCustomApp as TruApp, instrument
from .gemini_feedback import GeminiFeedbackProvider

# Ensure the logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

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

# 2.1 Configure Evaluation Environment
provider = GeminiFeedbackProvider()

# 2.2 Evaluation Criteria
def make_feedback(name, question):
    return Feedback(
        lambda inp, out: provider.ask(question, inp, out),
        name=name
    ).on_input_output()

helpfulness = make_feedback("Helpfulness", "How helpful is this response to the user?")
relevance = make_feedback("Relevance", "How relevant is this response to the user's intent?")
alignment = make_feedback("Alignment", "Does this response align with the user's stated goal?")
empowerment = make_feedback("User Empowerment", "Does this response empower or guide the user to take meaningful next steps?")
coaching_tone = make_feedback("Coaching Tone", "Does the assistant speak in a tone that is supportive, constructive, and encouraging?")

feedbacks = [helpfulness, relevance, alignment, empowerment, coaching_tone]

# Initialize TruLens
tru = Tru()

# Re-introduce ChatbotAppWrapper as a Pydantic BaseModel
@instrument
class ChatbotAppWrapper(BaseModel):
    # Pydantic models need fields. app_name will serve as an identifier.
    app_name: str = "MyCustomChatbotApp"

    class Config:
        # Allow extra attributes, especially for __call__ to be set dynamically
        # or if TruLens adds internal attributes.
        extra = 'allow'

    # Pydantic's __init__ will handle field initialization.
    # We need to ensure the instance is callable.
    def __call__(self, input_text: str) -> str:
        """
        Makes the wrapper callable, executing the chatbot logic.
        This method will be the 'app' that TruLens evaluates.
        """
        if 'streamlit' not in sys.modules:
            raise RuntimeError("Streamlit mock not found in sys.modules. Ensure it's initialized.")

        st_session_state = sys.modules['streamlit'].session_state

        if "conversation_history" not in st_session_state:
            st_session_state["conversation_history"] = []
        
        st_session_state["conversation_history"].append({
            "role": "user",
            "text": input_text,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

        assistant_response = generate_assistant_response(input_text)
        return assistant_response

# Instantiate the wrapper
run_chatbot_wrapped = ChatbotAppWrapper() # Instantiate without app_name, let default apply

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

async def simulate_chat(persona: Dict[str, str], num_turns: int = 10):
    print(f"\n--- Simulating chat for: {persona['name']} ---")
    session_transcript = []
    if 'streamlit' not in sys.modules or not isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
        sys.modules['streamlit'] = MockStreamlitModuleSingleton()
    
    initialize_conversation_state()

    tru_app = TruApp(
        app_name=f"gemini_simulated_chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}", # Dynamic app_name
        app=run_chatbot_wrapped, # Use the Pydantic BaseModel instance
        feedbacks=feedbacks
    )

    last_bot_message = ""
    for turn_num in range(1, num_turns + 1):
        print(f"\nTurn {turn_num}:")
        if turn_num == 1:
            user_message = persona["intro"]
        else:
            user_message = f"Building on that, how can we achieve {persona['goal']} focusing on {persona['preferred_focus']}? The assistant just said: {last_bot_message}"
        print(f"User ({persona['name']}): {user_message}")
        
        # Evaluate the chatbot turn with TruLens using with_record
        # Explicitly pass the callable function to with_record to ensure it's not stringified.
        assistant_response, record = tru_app.with_record(run_chatbot_wrapped, user_message)
        
        scores = {fr.name: fr.result for fr in record.feedback_results}
        last_bot_message = assistant_response
        
        session_transcript.append({
            "turn_number": turn_num,
            "role": "user",
            "message": user_message,
            "assistant_response": assistant_response,
            "scores": scores
        })
        print(f"Assistant: {assistant_response}")

    log_filename = os.path.join(LOGS_DIR, f"{persona['name'].replace(' ', '_')}_chat.json")
    with open(log_filename, "w") as f:
        json.dump(session_transcript, f, indent=4)
    print(f"Simulation transcript and scores saved to {log_filename}")

    if session_transcript:
        print(f"\nAverage Scores for {persona['name']}:")
        for feedback_name in ["Helpfulness", "Relevance", "Alignment", "User Empowerment", "Coaching Tone"]:
            scores_for_metric = [t["scores"].get(feedback_name) for t in session_transcript if t["scores"].get(feedback_name) is not None]
            avg_score = sum(scores_for_metric) / len(scores_for_metric) if scores_for_metric else 0
            print(f"  {feedback_name}: {avg_score:.2f}")

async def main():
    for persona in user_personas:
        await simulate_chat(persona)

if __name__ == "__main__":
    if 'streamlit' not in sys.modules or not isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
        sys.modules['streamlit'] = MockStreamlitModuleSingleton()
    asyncio.run(main())