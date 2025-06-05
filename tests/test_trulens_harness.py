import pytest
import asyncio
import os
import json
import sys

# Define the mock Streamlit class
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

@pytest.fixture(scope="module", autouse=True)
def mock_streamlit_for_tests():
    # Ensure mock Streamlit is in sys.modules BEFORE any imports that might use it
    # within the test functions or the modules they import.
    current_mock = None
    if 'streamlit' not in sys.modules or not isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
        current_mock = MockStreamlitModuleSingleton()
        sys.modules['streamlit'] = current_mock
    else: # It is our mock
        current_mock = sys.modules['streamlit']

    # Ensure session_state is clean and has conversation_history for the module/session
    current_mock.session_state = {"conversation_history": []}
    current_mock.query_params = {}
    
    # Store original sys.modules['streamlit'] if it exists and is not our mock, to restore later if needed
    original_streamlit = sys.modules.get('streamlit_original_for_restore', None) # Placeholder for complex scenarios
    
    yield # This is where the tests will run

    # Optional: Clean up or restore original Streamlit module if necessary
    # For this case, leaving the mock in place is usually fine for the test session.
    # If restoration is needed:
    # if original_streamlit:
    #     sys.modules['streamlit'] = original_streamlit
    # elif 'streamlit' in sys.modules and isinstance(sys.modules['streamlit'], MockStreamlitModuleSingleton):
    #     del sys.modules['streamlit']


from trulens_eval import Tru

@pytest.mark.asyncio
async def test_single_turn_happy_path(monkeypatch, mock_streamlit_for_tests): # Fixture will be auto-used
    # Configure TruLens to use a temporary SQLite database for tests
    monkeypatch.setenv("TRULENS_DATABASE_URL", "sqlite:///mini.sqlite")
    tru = Tru(database_url="sqlite:///mini.sqlite")
    tru.reset_database() # Clear any previous test data

    # Prevent TruLens dashboard from running during tests
    monkeypatch.setattr(Tru, 'run_dashboard', lambda *args, **kwargs: None)

    # Import ChatbotAppWrapper and GeminiFeedbackProvider AFTER setting up TruLens
    from simulations.trulens_runner import ChatbotAppWrapper, GeminiFeedbackProvider

    # Mock Gemini feedback provider to return a constant value
    monkeypatch.setattr(GeminiFeedbackProvider, "ask", lambda *a, **k: 4)

    bot = ChatbotAppWrapper()
    reply = await bot("Hi there")
    assert reply  # Should be non-empty

@pytest.mark.asyncio
async def test_golden_persona_ci_check(monkeypatch, mock_streamlit_for_tests): # Fixture will be auto-used
    # Configure TruLens to use a temporary SQLite database for tests
    monkeypatch.setenv("TRULENS_DATABASE_URL", "sqlite:///golden_persona.sqlite")
    tru = Tru(database_url="sqlite:///golden_persona.sqlite")
    tru.reset_database() # Clear any previous test data

    # Prevent TruLens dashboard from running during tests
    monkeypatch.setattr(Tru, 'run_dashboard', lambda *args, **kwargs: None)

    # Import ChatbotAppWrapper and GeminiFeedbackProvider AFTER setting up TruLens
    from simulations.trulens_runner import ChatbotAppWrapper, GeminiFeedbackProvider

    # Mock Gemini feedback provider to return a constant value for all feedback
    monkeypatch.setattr(GeminiFeedbackProvider, "ask", lambda *a, **k: 4)

    # Load the golden persona
    persona_path = "tests/fixtures/golden_persona.json"
    with open(persona_path, 'r') as f:
        persona_data = json.load(f)

    bot = ChatbotAppWrapper()
    for turn in persona_data["conversation"]:
        user_message = turn["user_message"]
        llm_response = turn["llm_response"] # This is the expected response, not used for actual LLM call

        # Simulate the conversation turn
        # In a real scenario, bot(user_message) would call the LLM.
        # Here, we are testing the TruLens integration and feedback aggregation.
        # We can assert that the bot returns something, but the core is TruLens recording.
        reply = await bot(user_message)
        assert reply is not None # Ensure a response was generated

    # Assert that TruLens recorded feedback for each turn
    # This is a basic check; more robust checks would involve querying the TruLens DB
    # to verify specific feedback values or aggregation results.
    records = tru.get_records_and_feedback()
    assert len(records) == len(persona_data["conversation"])

    # Example of a more specific aggregation check (assuming feedback is aggregated)
    # This part might need adjustment based on how TruLens aggregates feedback.
    # For now, we'll just check if records exist.
    # If there's a specific aggregation method, we'd call it here.
    # For instance, if `tru.get_latest_feedback()` or similar exists.
    # Since we mocked GeminiFeedbackProvider.ask to return 4, we expect some feedback.
    # The exact aggregation mechanism depends on TruLens's internal workings.
    # For a simple CI check, ensuring records are created is a good start.