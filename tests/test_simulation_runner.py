import unittest
import asyncio
import json
import os
from unittest.mock import patch, MagicMock

# Adjust the path to import from simulations and src
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulations.trulens_runner import simulate_chat, user_personas, LOGS_DIR, run_chatbot_wrapped
from src.conversation_manager import initialize_conversation_state

class TestSimulationRunner(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Ensure a clean state for Streamlit's session_state mock before each test
        if 'streamlit' in sys.modules:
            del sys.modules['streamlit']
        
        # Create a mock for Streamlit's session_state
        self.mock_st_session_state = MagicMock()
        self.mock_st_session_state.to_dict.return_value = {} # Ensure to_dict exists
        
        # Mock the entire streamlit module
        self.mock_streamlit_module = MagicMock()
        self.mock_streamlit_module.session_state = self.mock_st_session_state
        self.mock_streamlit_module.query_params = {}
        self.mock_streamlit_module.warning = MagicMock()
        self.mock_streamlit_module.error = MagicMock()
        
        sys.modules['streamlit'] = self.mock_streamlit_module

        # Ensure the logs directory is clean for tests
        os.makedirs(LOGS_DIR, exist_ok=True)
        for f in os.listdir(LOGS_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(LOGS_DIR, f))

    def tearDown(self):
        # Clean up the mock Streamlit module
        if 'streamlit' in sys.modules and sys.modules['streamlit'] == self.mock_streamlit_module:
            del sys.modules['streamlit']
        
        # Clean up the added path
        if os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) in sys.path:
            sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    @patch('src.conversation_manager.generate_assistant_response') # Patch generate_assistant_response directly
    @patch('simulations.trulens_runner.TruApp') # Patch TruApp in trulens_runner
    @patch('simulations.trulens_runner.query_gemini') # Patch query_gemini in trulens_runner
    async def test_simulate_chat_and_logging(self, mock_query_gemini, MockTruCustomApp, mock_generate_assistant_response):
        # Mock generate_assistant_response responses
        mock_generate_assistant_response.side_effect = [
"Hello! I'm your assistant. How can I help?", # Initial assistant response
"Here are some ideas for chronic disease management.", # Assistant response for turn 2
"That's a great question. Let's explore that further.", # Assistant response for turn 3
"Indeed, remote monitoring is key.", # Assistant response for turn 4
"AI can certainly personalize mental health support.", # Assistant response for turn 5
"Consider these ethical implications.", # Assistant response for turn 6
"Further research areas include data privacy.", # Assistant response for turn 7
"The market for digital health is growing.", # Assistant response for turn 8
"Regulatory hurdles are common.", # Assistant response for turn 9
"Final thoughts on implementation." # Assistant response for turn 10
        ]

        # Mock TruCustomApp.with_record
        mock_tru_app_instance = MagicMock()
        MockTruCustomApp.return_value = mock_tru_app_instance

        def mock_with_record_side_effect(func, user_message):
            # Simulate the assistant response from the patched generate_assistant_response
            async def _get_assistant_response():
                return await mock_generate_assistant_response(user_message)
            assistant_response_coroutine = _get_assistant_response()

            mock_record = MagicMock()
            feedback_data = [
                ("Helpfulness", 0.8), ("Relevance", 0.9), ("Alignment", 0.7),
                ("User Empowerment", 0.8), ("Coaching Tone", 0.9),
                ("Helpfulness", 0.7), ("Relevance", 0.8), ("Alignment", 0.9),
                ("User Empowerment", 0.7), ("Coaching Tone", 0.8),
                ("Helpfulness", 0.9), ("Relevance", 0.7), ("Alignment", 0.8),
                ("User Empowerment", 0.9), ("Coaching Tone", 0.7),
                ("Helpfulness", 0.8), ("Relevance", 0.9), ("Alignment", 0.7),
                ("User Empowerment", 0.8), ("Coaching Tone", 0.9),
                ("Helpfulness", 0.7), ("Relevance", 0.8), ("Alignment", 0.9),
                ("User Empowerment", 0.7), ("Coaching Tone", 0.8),
                ("Helpfulness", 0.9), ("Relevance", 0.7), ("Alignment", 0.8),
                ("User Empowerment", 0.9), ("Coaching Tone", 0.7),
                ("Helpfulness", 0.8), ("Relevance", 0.9), ("Alignment", 0.7),
                ("User Empowerment", 0.8), ("Coaching Tone", 0.9),
                ("Helpfulness", 0.7), ("Relevance", 0.8), ("Alignment", 0.9),
                ("User Empowerment", 0.7), ("Coaching Tone", 0.8),
                ("Helpfulness", 0.9), ("Relevance", 0.7), ("Alignment", 0.8),
                ("User Empowerment", 0.9), ("Coaching Tone", 0.7),
                ("Helpfulness", 0.8), ("Relevance", 0.9), ("Alignment", 0.7),
                ("User Empowerment", 0.8), ("Coaching Tone", 0.9),
                ("Helpfulness", 0.7), ("Relevance", 0.8), ("Alignment", 0.9),
                ("User Empowerment", 0.7), ("Coaching Tone", 0.8),
            ]
            mock_record.feedback_results = []
            for name_val, result_val in feedback_data:
                fr_mock = MagicMock()
                fr_mock.name = name_val
                fr_mock.result = result_val
                mock_record.feedback_results.append(fr_mock) # Append the mock directly, not an awaitable

            return assistant_response_coroutine, mock_record

        mock_tru_app_instance.with_record.side_effect = mock_with_record_side_effect

        # Select one persona for testing
        persona = user_personas[0] # Startup Clinician
        log_filename = os.path.join(LOGS_DIR, f"{persona['name'].replace(' ', '_')}_chat.json")

        # Run the simulation
        await simulate_chat(persona, num_turns=10)

        # 1. Validate log file creation
        self.assertTrue(os.path.exists(log_filename))

        # 2. Validate log file content and structure
        with open(log_filename, 'r') as f:
            transcript = json.load(f)

        self.assertEqual(len(transcript), 10) # 10 turns simulated

        for i, turn in enumerate(transcript):
            self.assertIn("turn_number", turn)
            self.assertIn("role", turn)
            self.assertIn("message", turn)
            self.assertIn("assistant_response", turn)
            self.assertIn("scores", turn)
            self.assertIn("Helpfulness", turn["scores"])
            self.assertIn("Relevance", turn["scores"])
            self.assertIn("Alignment", turn["scores"])
            self.assertIn("User Empowerment", turn["scores"])
            self.assertIn("Coaching Tone", turn["scores"])
            self.assertIsNotNone(turn["scores"]["Helpfulness"])
            self.assertIsNotNone(turn["scores"]["Relevance"])
            self.assertIsNotNone(turn["scores"]["Alignment"])
            self.assertIsNotNone(turn["scores"]["User Empowerment"])
            self.assertIsNotNone(turn["scores"]["Coaching Tone"])
            
            # Check roles for odd/even turns
            # The log records the user's message and the assistant's response in the same entry.
            self.assertEqual(turn["role"], "user")

        # Verify that query_gemini was called for each assistant response
        self.assertEqual(mock_generate_assistant_response.call_count, 10) # 10 turns, each calls generate_assistant_response

        # Verify that TruCustomApp.evaluate was called for each turn
        self.assertEqual(mock_tru_app_instance.with_record.call_count, 10)

if __name__ == '__main__':
    unittest.main()