import json
import os
import datetime
import asyncio
import sys
import concurrent.futures # Import concurrent.futures
from typing import Dict, List, Any, Optional
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
# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.conversation_manager import initialize_conversation_state, generate_assistant_response
from src.llm_utils import query_gemini

# TruLens Imports
from trulens.core import Tru, Feedback
from trulens.apps.custom import TruCustomApp as TruApp, instrument
from simulations.gemini_feedback import GeminiFeedbackProvider

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

# Start TruLens dashboard
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

        if "conversation_history" not in st_session_state:
            st_session_state["conversation_history"] = []
        
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
    print(f"\n--- Simulating chat for: {persona['name']} ---")
    session_transcript = []
    
    initialize_conversation_state()

    tru_app = TruApp(
        app_name=f"gemini_simulated_chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        app=run_chatbot_wrapped,
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
        
        app_output, record = tru_app.with_record(run_chatbot_wrapped, user_message)
        assistant_response = await app_output
        
        scores = {}
        # Get feedback results
        feedback_results = record.feedback_results
        if feedback_results:
            # Check if they are already computed or need to be awaited
            if hasattr(feedback_results[0], '__await__'):
                # They are awaitables, so await them
                feedback_results = await asyncio.gather(*feedback_results)
            
            for fr in feedback_results:
                if hasattr(fr, 'name') and hasattr(fr, 'result'):
                    scores[fr.name] = fr.result
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
    asyncio.run(main())