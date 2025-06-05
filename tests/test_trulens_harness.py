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
from trulens.apps.custom import TruCustomApp # Moved to top-level

@pytest.mark.asyncio
async def test_single_turn_happy_path(monkeypatch, mock_streamlit_for_tests): # Fixture will be auto-used
    import trulens_eval
    print(f"\nDEBUG: TruLens Version: {trulens_eval.__version__}")
    print(f"DEBUG: Python Version: {sys.version}")

    # Configure TruLens to use a temporary SQLite database for tests
    monkeypatch.setenv("TRULENS_DATABASE_URL", "sqlite:///mini.sqlite")
    tru = Tru(database_url="sqlite:///mini.sqlite")
    tru.reset_database() # Clear any previous test data

    # Prevent TruLens dashboard from running during tests
    monkeypatch.setattr(Tru, 'run_dashboard', lambda *args, **kwargs: None)

    # Import necessary components
    from simulations.trulens_runner import ChatbotAppWrapper, GeminiFeedbackProvider, build_feedbacks
    # TruCustomApp is already imported at the top level

    # 1. Patch the GeminiFeedbackProvider CLASS method *before* feedbacks are constructed
    monkeypatch.setattr(GeminiFeedbackProvider, "ask", lambda *a, **k: 4)

    # 2. Build feedbacks *after* the provider's class method is patched
    # This ensures the Feedback objects capture the mocked 'ask' method via their provider instance.
    current_feedbacks = build_feedbacks()

    print("\n=== Feedback objects and their providers (test_single_turn_happy_path) ===")
    for f_idx, f_obj in enumerate(current_feedbacks):
        print(f"Feedback [{f_idx}]: {f_obj}")
        if hasattr(f_obj, 'provider') and f_obj.provider is not None: # provider might be None if not set
            print(f"  Provider: {f_obj.provider}, Provider.ask: {getattr(f_obj.provider, 'ask', 'N/A')}, Type(Provider.ask): {type(getattr(f_obj.provider, 'ask', None))}")
        elif hasattr(f_obj, 'imp') and hasattr(f_obj.imp, '__closure__') and f_obj.imp.__closure__:
             # Attempt to inspect closure if provider attribute is not direct
            for cell in f_obj.imp.__closure__:
                try:
                    closure_var = cell.cell_contents
                    if isinstance(closure_var, GeminiFeedbackProvider): # Check if it's our provider
                         print(f"  Inferred Provider from closure: {closure_var}, Provider.ask: {getattr(closure_var, 'ask', 'N/A')}, Type(Provider.ask): {type(getattr(closure_var, 'ask', None))}")
                except ValueError: # cell_contents might be empty
                    pass
        else:
            print(f"  Provider attribute not found or is None.")
    print("--- End Feedback objects ---")

    # print("\n=== Manually running first feedback function (test_single_turn_happy_path) ===")
    # if current_feedbacks:
    #     try:
    #         # Feedback.fn takes (app_input, app_output) or just app_output depending on .on_...()
    #         # The lambda is (inp, out) -> provider.ask(question, inp, out)
    #         # For on_input_output, it will be called with app_input and app_output.
    #         # Let's simulate a call. The actual input/output for provider.ask doesn't matter much
    #         # as provider.ask itself is mocked to return 4.
    #         manual_result = current_feedbacks[0].fn("test input", "test output")
    #         print(f"Manual feedback fn[0] call result: {manual_result}")
    #     except Exception as e:
    #         print(f"Manual feedback fn[0] call failed: {e}")
    # print("--- End Manual feedback run ---\n")
    
    app_instance = ChatbotAppWrapper()
    # 3. Use these freshly built feedbacks when initializing TruCustomApp
    bot_tru_app = TruCustomApp(app_instance, app_id="TestBotApp_SingleTurn", feedbacks=current_feedbacks)
    
    # Call TruCustomApp with_record method
    # with_record is not async, it returns futures
    app_output_future, record_placeholder = bot_tru_app.with_record(app_instance, "Hi there")
    reply = await app_output_future # Await the future to get the actual reply
    # Ensure TruLens finishes evaluating feedback before we read records
    # Unwrap tuple if needed
    if isinstance(reply, tuple):
        reply = reply[0]
    assert isinstance(reply, str) and reply.strip() != ""
    
    # Get records associated with this specific TruApp instance if possible,
    # or rely on the global Tru().get_records_and_feedback()
    # For simplicity, using global Tru() and assuming it captures from bot_tru_app
    # Use in-memory feedback map returned by TruCustomApp
    # wait_for_feedback_results yields (feedback_def, result) pairs
    # Get finished feedback results for this specific record
    feedback_map = dict(record_placeholder.wait_for_feedback_results())
    processed_scores = {
        fb.name: getattr(res, "result", res)
        for fb, res in feedback_map.items()
        if res is not None
    }

    # At least one score must be non-zero
    assert any(processed_scores.values()), "Feedback scores empty or zero"

    # 4. Assert the feedback dict contains 'Helpfulness' with value == 4
    assert isinstance(processed_scores, dict), f"processed_scores is not a dict: {type(processed_scores)}"
    assert "Helpfulness" in processed_scores, f"'Helpfulness' not in processed_scores: {processed_scores.keys()}"
    assert processed_scores["Helpfulness"] == 4, \
        f"Helpfulness score is not 4. Got: {processed_scores['Helpfulness']}. All scores: {processed_scores}"

@pytest.mark.asyncio
async def test_golden_persona_ci_check(monkeypatch, mock_streamlit_for_tests): # Fixture will be auto-used
    # Configure TruLens to use a temporary SQLite database for tests
    monkeypatch.setenv("TRULENS_DATABASE_URL", "sqlite:///golden_persona.sqlite")
    tru = Tru(database_url="sqlite:///golden_persona.sqlite")
    tru.reset_database() # Clear any previous test data

    # Prevent TruLens dashboard from running during tests
    monkeypatch.setattr(Tru, 'run_dashboard', lambda *args, **kwargs: None)

    # Import necessary components
    from simulations.trulens_runner import ChatbotAppWrapper, GeminiFeedbackProvider, build_feedbacks
    # TruCustomApp is already imported at the top level

    # 1. Patch the GeminiFeedbackProvider CLASS method *before* feedbacks are constructed
    monkeypatch.setattr(GeminiFeedbackProvider, "ask", lambda *a, **k: 4)

    # 2. Build feedbacks *after* the provider's class method is patched
    current_feedbacks = build_feedbacks()

    print("\n=== Feedback objects and their providers (test_golden_persona_ci_check) ===")
    for f_idx, f_obj in enumerate(current_feedbacks):
        print(f"Feedback [{f_idx}]: {f_obj}")
        if hasattr(f_obj, 'provider') and f_obj.provider is not None:
            print(f"  Provider: {f_obj.provider}, Provider.ask: {getattr(f_obj.provider, 'ask', 'N/A')}, Type(Provider.ask): {type(getattr(f_obj.provider, 'ask', None))}")
        elif hasattr(f_obj, 'imp') and hasattr(f_obj.imp, '__closure__') and f_obj.imp.__closure__:
            for cell in f_obj.imp.__closure__:
                try:
                    closure_var = cell.cell_contents
                    if isinstance(closure_var, GeminiFeedbackProvider):
                         print(f"  Inferred Provider from closure: {closure_var}, Provider.ask: {getattr(closure_var, 'ask', 'N/A')}, Type(Provider.ask): {type(getattr(closure_var, 'ask', None))}")
                except ValueError:
                    pass
        else:
            print(f"  Provider attribute not found or is None.")
    print("--- End Feedback objects ---")

    # print("\n=== Manually running first feedback function (test_golden_persona_ci_check) ===")
    # if current_feedbacks:
    #     try:
    #         manual_result = current_feedbacks[0].fn("test input", "test output")
    #         print(f"Manual feedback fn[0] call result: {manual_result}")
    #     except Exception as e:
    #         print(f"Manual feedback fn[0] call failed: {e}")
    # print("--- End Manual feedback run ---\n")

    # Load the golden persona
    persona_path = "tests/fixtures/golden_persona.json"
    with open(persona_path, 'r') as f:
        persona_data = json.load(f)

    app_instance = ChatbotAppWrapper()
    # Explicitly create a TruApp with feedbacks for testing
    bot_tru_app = TruCustomApp(app_instance, app_id="TestBotApp_GoldenPersona", feedbacks=current_feedbacks)

    for turn_idx, turn in enumerate(persona_data["conversation"]):
        user_message = turn["user_message"]
        # llm_response = turn["llm_response"] # This is the expected response, not used for actual LLM call

        # Call TruCustomApp with_record method
        # with_record is not async, it returns futures
        app_output_future, record_placeholder = bot_tru_app.with_record(app_instance, user_message)
        reply = await app_output_future # Await the future
        # Ensure TruLens finishes evaluating feedback before we read records
        # Unwrap tuple if needed
        if isinstance(reply, tuple):
            reply = reply[0]
        assert isinstance(reply, str) and reply.strip() != ""
        
        # Use in-memory feedback map returned by TruCustomApp
        # wait_for_feedback_results yields (feedback_def, result) pairs
        # Get finished feedback results for this specific record
        feedback_map = dict(record_placeholder.wait_for_feedback_results())
        processed_scores = {
            fb.name: getattr(res, "result", res)
            for fb, res in feedback_map.items()
            if res is not None
        }

        # At least one score must be non-zero
        assert any(processed_scores.values()), "Feedback scores empty or zero"
        
        assert processed_scores is not None and isinstance(processed_scores, dict), \
            f"Processed scores is not a dictionary or is None. Value: {processed_scores} for record 0 after turn {turn_idx}"
        
        # 4. Assert the feedback dict contains 'Helpfulness' with value == 4
        # This check is on the *first overall record's* feedback after each turn.
        assert "Helpfulness" in processed_scores, \
            f"'Helpfulness' not in processed_scores of record 0 (after turn {turn_idx}). Keys: {processed_scores.keys()}"
        assert processed_scores["Helpfulness"] == 4, \
            f"Helpfulness score of record 0 (after turn {turn_idx}) is not 4. Got: {processed_scores['Helpfulness']}. All scores: {processed_scores}"

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