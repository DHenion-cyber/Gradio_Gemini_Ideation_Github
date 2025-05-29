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
from trulens_eval import Tru, Feedback, TruChain
from langchain_core.runnables import RunnableLambda
# from trulens_eval.feedback.provider.openai import OpenAI # Commenting out problematic import
from .gemini_feedback import GeminiFeedbackProvider # Using custom Gemini feedback

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
helpfulness = Feedback(
    provider.helpfulness,
    name="Helpfulness"
).on_input_output()

relevance = Feedback(
    provider.relevance,
    name="Relevance"
).on_input_output()

alignment = Feedback(
    provider.crispness,  # Using crispness as a proxy for alignment clarity
    name="Alignment"
).on_output() # Crispness typically evaluates only the output

# Initialize TruLens
tru = Tru()

# Helper to simulate a single chatbot turn for TruLens wrapping
# This function will mimic the core logic of how your chatbot generates a response
# given a user input and the current session state.
async def _simulate_chatbot_turn(user_message: str, current_session_state: Dict[str, Any]) -> str:
    """
    Simulates a single turn of the chatbot, generating an assistant response.
    This function is designed to be wrapped by TruChain.
    """
    # Temporarily set st.session_state to the current_session_state for the duration of this call
    # This is a mock for Streamlit's global session_state. In a real Streamlit app,
    # st.session_state would be managed by Streamlit itself.
    class MockStreamlitSessionState(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.__dict__ = self

    original_st_session_state = None
    if 'st' in sys.modules:
        original_st_session_state = sys.modules['st'].session_state
    
    mock_st = type('module', (object,), {'session_state': MockStreamlitSessionState(current_session_state)})
    sys.modules['streamlit'] = mock_st

    # Ensure conversation_history is present for generate_assistant_response
    if "conversation_history" not in mock_st.session_state:
        mock_st.session_state["conversation_history"] = []
    
    # Append user message to history for this simulated turn
    mock_st.session_state["conversation_history"].append({
        "role": "user",
        "text": user_message,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })

    # Generate assistant response using the actual chatbot logic
    assistant_response = generate_assistant_response(user_message)

    # Restore original st.session_state if it existed
    if original_st_session_state:
        sys.modules['st'].session_state = original_st_session_state
    else:
        # Clean up mock if Streamlit wasn't originally imported
        if 'streamlit' in sys.modules:
            del sys.modules['streamlit']

    return assistant_response

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
    current_session_state = {k: v for k, v in st_mock.session_state.items()} # Capture initial state

    # Wrap the simulated chatbot turn logic with TruChain
    # To make _simulate_chatbot_turn compatible with TruChain's expectation of a Runnable,
    # we can wrap it with RunnableLambda.
    # Note: _simulate_chatbot_turn takes two arguments, user_message and current_session_state.
    # RunnableLambda typically expects a single input dictionary.
    # We'll need to adjust how inputs are passed or how _simulate_chatbot_turn is called.

    # For simplicity, let's assume TruChain can handle an async callable directly,
    # or we might need to adjust the input to _simulate_chatbot_turn if using RunnableLambda strictly.
    # The error "Input should be an instance of Runnable" suggests it needs to be a Runnable.

    # Let's define a wrapper that takes a dict and unpacks it for _simulate_chatbot_turn
    async def runnable_simulate_turn(input_dict: Dict[str, Any]) -> str:
        return await _simulate_chatbot_turn(
            user_message=input_dict["user_message"],
            current_session_state=input_dict["current_session_state"]
        )

    app_runnable = RunnableLambda(runnable_simulate_turn)

    chatbot_chain = TruChain(
        app_id=f"simulated_chatbot_session_{persona['name'].replace(' ', '_')}",
        app=app_runnable, # Pass the RunnableLambda instance
        feedbacks=[helpfulness, relevance, alignment]
    )

    last_bot_message = ""
    for turn_num in range(1, num_turns + 1):
        print(f"\nTurn {turn_num}:")

        # Simulate User Turn (Odd turns)
        if turn_num % 2 != 0:
            if turn_num == 1:
                user_message = persona["intro"]
            else:
                # For subsequent turns, simulate user evolving their intent
                # This is a very basic simulation. A more advanced one might use an LLM
                # to generate user responses based on previous turns and persona goal.
                user_message = f"Building on that, how can we achieve {persona['goal']} focusing on {persona['preferred_focus']}? The assistant just said: {last_bot_message}"
            
            print(f"User ({persona['name']}): {user_message}")
            
            # For TruLens, we need to call the wrapped chain with the user input
            # and the current state that the chatbot would operate on.
            # The _simulate_chatbot_turn function will handle updating its internal mock state.
            # When using TruChain, the call should be made through the wrapped chain
            # and it will handle the recording.
            # The input to the wrapped chain (app_runnable) should be a dictionary.
            chain_input = {"user_message": user_message, "current_session_state": current_session_state}
            # Since app_runnable is async, chatbot_chain.with_record will likely return a coroutine
            # or handle the async execution internally and return the result and record.
            # The error "not enough values to unpack (expected 2, got 0)" suggests it might be returning None
            # or something that doesn't unpack to two values when the underlying async app is not handled correctly.
            #
            # TruChain's with_record is designed to work with LangChain Runnables.
            # If the Runnable is async, with_record should ideally handle it.
            # Let's try awaiting the call to with_record, as this is a common pattern for async operations.
            # However, the typical signature for with_record is that it returns (result, record_future)
            # and the record_future is then awaited if needed, or the feedback is processed later.
            #
            # Given the error, it's possible that `with_record` itself is not async, but the way it
            # interacts with an async `RunnableLambda` is problematic, or the mock setup for tests
            # is interfering.

            # Let's try a slightly different approach for async apps with TruChain.
            # The `acall` method is often used for async chains.
            # We'll use `awith_record` which is the async version of `with_record`.
            assistant_response, record = await chatbot_chain.awith_record(chain_input)
            
            # Update last_bot_message for the next turn
            last_bot_message = assistant_response
            
            # Log the turn
            session_transcript.append({
                "turn_number": turn_num,
                "role": "user",
                "message": user_message,
                "assistant_response": assistant_response,
                "scores": {
                    "helpfulness": record.get_feedback("Helpfulness").score,
                    "relevance": record.get_feedback("Relevance").score,
                    "alignment": record.get_feedback("Alignment").score
                }
            })
            print(f"Assistant: {assistant_response}")

        # Simulate Assistant Turn (Even turns - if applicable, though the above handles it)
        # The above `with tru.track_dx` block already covers the assistant's response.
        # If you had a separate function for assistant's turn, you'd call it here.
        # For this setup, the assistant's response is generated immediately after the user's.
        
        # Update the current_session_state for the next turn based on the mock_st.session_state
        # This is crucial for the chatbot's internal logic to evolve.
        current_session_state = {k: v for k, v in sys.modules['streamlit'].session_state.items()}


    # 3. Output and Review
    log_filename = os.path.join(LOGS_DIR, f"{persona['name'].replace(' ', '_')}_chat.json")
    with open(log_filename, "w") as f:
        json.dump(session_transcript, f, indent=4)
    print(f"Simulation transcript and scores saved to {log_filename}")

    # Optional: Print average scores
    if session_transcript:
        avg_helpfulness = sum(t["scores"]["helpfulness"] for t in session_transcript if t["scores"]["helpfulness"] is not None) / len(session_transcript)
        avg_relevance = sum(t["scores"]["relevance"] for t in session_transcript if t["scores"]["relevance"] is not None) / len(session_transcript)
        avg_alignment = sum(t["scores"]["alignment"] for t in session_transcript if t["scores"]["alignment"] is not None) / len(session_transcript)
        print(f"\nAverage Scores for {persona['name']}:")
        print(f"  Helpfulness: {avg_helpfulness:.2f}")
        print(f"  Relevance: {avg_relevance:.2f}")
        print(f"  Alignment: {avg_alignment:.2f}")

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