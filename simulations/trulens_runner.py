import json
import os
import datetime
import asyncio
from typing import Dict, List, Any, Optional

# Import necessary modules from the main application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from conversation_manager import initialize_conversation_state, run_intake_flow, generate_assistant_response, navigate_value_prop_elements
from llm_utils import query_gemini, count_tokens # Assuming count_tokens is in llm_utils

# TruLens Imports
from trulens_eval import Tru, Feedback, TruCustomApp
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
# For now, using OpenAI as a proxy. If a GeminiFeedbackProvider is implemented,
# it would replace OpenAIFeedback here.
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

# Helper to simulate a single chatbot turn for TruLens wrapping
# This function will mimic the core logic of how your chatbot generates a response
# given a user input and the current session state.

# 1.2 Simulate Conversation Function
# Define MockStreamlit class at the module level to be accessible
class MockStreamlitModuleSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockStreamlitModuleSingleton, cls).__new__(cls)
            cls._instance.session_state = {}
            cls._instance.query_params = {}
        return cls._instance

    def warning(self, text):
        print(f"Streamlit Warning: {text}")

    def error(self, text):
        print(f"Streamlit Error: {text}")

    # Add a to_dict method to session_state if it's a plain dict for compatibility
    # or ensure session_state itself is an object with a to_dict method.
    # For simplicity, if session_state is a dict, we can wrap it or add to_dict.
    # However, initialize_conversation_state expects st.session_state to be directly usable.

async def simulate_chat(persona: Dict[str, str], num_turns: int = 10):
    """
    Simulates a fixed-turn chat loop with a given persona and evaluates it with TruLens.
    """
    print(f"\n--- Simulating chat for: {persona['name']} ---")
    session_transcript = []

    # Ensure Streamlit is mocked for the entire simulation run
    # This is important for functions like initialize_conversation_state
    # which directly use `st.session_state`.
    if 'streamlit' not in sys.modules or not isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
        sys.modules['streamlit'] = MockStreamlitModuleSingleton()
    
    st_mock = sys.modules['streamlit']

    # Initialize conversation state for the simulation
    # This will set up a fresh session_state for each simulation
    initialize_conversation_state() # This function uses st.session_state

    tru_app = TruCustomApp(
        app_id="gemini_simulated_chat",
        app=run_chatbot,
        feedbacks=feedbacks
    )

    last_bot_message = ""
    for turn_num in range(1, num_turns + 1):
        print(f"\nTurn {turn_num}:")

        # Simulate User Turn (Odd turns)
        if turn_num == 1:
            user_message = persona["intro"]
        else:
            # For subsequent turns, simulate user evolving their intent
            user_message = f"Building on that, how can we achieve {persona['goal']} focusing on {persona['preferred_focus']}? The assistant just said: {last_bot_message}"
        
        print(f"User ({persona['name']}): {user_message}")
        
        # Evaluate the chatbot turn with TruLens
        # The evaluate method takes inputs and outputs as dictionaries
        result = tru_app.evaluate(
            inputs={"input": user_message},
            outputs={"output": run_chatbot(user_message)} # Call run_chatbot directly for the output
        )
        
        # Extract assistant response from the evaluation result
        assistant_response = result.outputs["output"]
        
        # Update last_bot_message for the next turn
        last_bot_message = assistant_response
        
        # Log the turn
        scores = {f.name: f.result for f in result.feedback_results}
        session_transcript.append({
            "turn_number": turn_num,
            "role": "user",
            "message": user_message,
            "assistant_response": assistant_response,
            "scores": scores
        })
        print(f"Assistant: {assistant_response}")

        # Update the current_session_state for the next turn based on the mock_st.session_state
        # This is crucial for the chatbot's internal logic to evolve.
        # Note: With TruCustomApp, the `run_chatbot` function directly interacts with the mocked
        # Streamlit session state, so `current_session_state` is implicitly updated.
        # We don't need to explicitly re-capture it here unless `run_chatbot` was modifying a local copy.
        # Given the current `run_chatbot` implementation, it modifies `sys.modules['streamlit'].session_state` directly.


    # 3. Output and Review
    log_filename = os.path.join(LOGS_DIR, f"{persona['name'].replace(' ', '_')}_chat.json")
    with open(log_filename, "w") as f:
        json.dump(session_transcript, f, indent=4)
    print(f"Simulation transcript and scores saved to {log_filename}")

    # Optional: Print average scores
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
    # This is needed because Streamlit's session_state is not available outside a Streamlit app.
    # We are mocking it for the health check and simulation.
    # For actual Streamlit app, this mock would not be needed.
    # Ensure Streamlit is mocked if running as main
    if 'streamlit' not in sys.modules or not isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
        sys.modules['streamlit'] = MockStreamlitModuleSingleton()
    
    asyncio.run(main())