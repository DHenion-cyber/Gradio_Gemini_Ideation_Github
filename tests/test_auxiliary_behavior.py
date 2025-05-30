import unittest
import os
import json
from unittest.mock import patch, MagicMock
from reportlab.lib.pagesizes import letter

from simulations.export_summary import export_to_csv, export_to_pdf, generate_weighted_score_summary, flag_poor_turns

class TestAuxiliaryBehavior(unittest.TestCase):

    def setUp(self):
        self.log_data = [
            {
                "turn_number": 1,
                "role": "user",
                "message": "Hello, how are you?",
                "assistant_response": "I'm fine, thank you!",
                "scores": {
                    "Helpfulness": 4,
                    "Relevance": 5,
                    "Alignment": 4,
                    "User Empowerment": 3,
                    "Coaching Tone": 5
                }
            },
            {
                "turn_number": 2,
                "role": "user",
                "message": "Tell me about AI.",
                "assistant_response": "AI is a broad field.",
                "scores": {
                    "Helpfulness": 2,
                    "Relevance": 3,
                    "Alignment": 2,
                    "User Empowerment": 1,
                    "Coaching Tone": 2
                }
            }
        ]
        self.summary_data = generate_weighted_score_summary(self.log_data)
        self.export_dir = "simulations/exports"
        os.makedirs(self.export_dir, exist_ok=True)
        self.csv_path = os.path.join(self.export_dir, "test_session_eval.csv")
        self.pdf_path = os.path.join(self.export_dir, "test_session_eval.pdf")

    def tearDown(self):
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)
        if os.path.exists(self.export_dir) and not os.listdir(self.export_dir):
            os.rmdir(self.export_dir)

    def test_export_to_csv(self):
        export_to_csv(self.log_data, output_path=self.csv_path)
        self.assertTrue(os.path.exists(self.csv_path))
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Helpfulness", content)
            self.assertIn("Hello, how are you?", content)

    @patch('reportlab.pdfgen.canvas.Canvas')
    def test_export_to_pdf(self, MockCanvas):
        mock_canvas_instance = MockCanvas.return_value
        export_to_pdf(self.log_data, self.summary_data, output_path=self.pdf_path)
        MockCanvas.assert_called_once_with(self.pdf_path, pagesize=letter)
        mock_canvas_instance.save.assert_called_once()

if __name__ == '__main__':
    unittest.main()