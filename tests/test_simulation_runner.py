import unittest
import asyncio
import json
import os
from unittest.mock import patch, MagicMock

# Adjust the path to import from simulations and src
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulations.trulens_runner import simulate_chat, user_personas, LOGS_DIR
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

    @patch('src.llm_utils.query_gemini')
    @patch('trulens_eval.TruChain.with_record')
    async def test_simulate_chat_and_logging(self, mock_tru_chain_with_record, mock_query_gemini):
        # Mock Gemini responses
        mock_query_gemini.side_effect = [
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

        # Mock TruLens feedback scores
        mock_record = MagicMock()
        mock_record.get_feedback.side_effect = [
            MagicMock(score=0.8), MagicMock(score=0.9), MagicMock(score=0.7), # Turn 1 scores
            MagicMock(score=0.7), MagicMock(score=0.8), MagicMock(score=0.9), # Turn 2 scores
            MagicMock(score=0.9), MagicMock(score=0.7), MagicMock(score=0.8), # Turn 3 scores
            MagicMock(score=0.8), MagicMock(score=0.9), MagicMock(score=0.7), # Turn 4 scores
            MagicMock(score=0.7), MagicMock(score=0.8), MagicMock(score=0.9), # Turn 5 scores
            MagicMock(score=0.9), MagicMock(score=0.7), MagicMock(score=0.8), # Turn 6 scores
            MagicMock(score=0.8), MagicMock(score=0.9), MagicMock(score=0.7), # Turn 7 scores
            MagicMock(score=0.7), MagicMock(score=0.8), MagicMock(score=0.9), # Turn 8 scores
            MagicMock(score=0.9), MagicMock(score=0.7), MagicMock(score=0.8), # Turn 9 scores
            MagicMock(score=0.8), MagicMock(score=0.9), MagicMock(score=0.7)  # Turn 10 scores
        ]
        mock_tru_chain_with_record.return_value.__enter__.return_value = mock_record

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
            self.assertIn("helpfulness", turn["scores"])
            self.assertIn("relevance", turn["scores"])
            self.assertIn("alignment", turn["scores"])
            self.assertIsNotNone(turn["scores"]["helpfulness"])
            self.assertIsNotNone(turn["scores"]["relevance"])
            self.assertIsNotNone(turn["scores"]["alignment"])
            
            # Check roles for odd/even turns
            if (i + 1) % 2 != 0: # User turn
                self.assertEqual(turn["role"], "user")
            else: # Assistant turn (response to user's previous message)
                self.assertEqual(turn["role"], "user") # The log records the user's message and the assistant's response in the same entry.

        # Verify that query_gemini was called for each assistant response
        self.assertEqual(mock_query_gemini.call_count, 10) # 10 turns, each calls query_gemini

        # Verify that TruChain.with_record was called for each turn
        self.assertEqual(mock_tru_chain_with_record.call_count, 10)

if __name__ == '__main__':
    unittest.main()