import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

class GeminiFeedbackProvider:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-pro")

    def ask(self, prompt: str, input_text: str, response_text: str) -> str:
        full_prompt = f"""
You are a helpful evaluator. Given the user's message and the assistant's response, answer the following:
PROMPT: {input_text}
RESPONSE: {response_text}
QUESTION: {prompt}
Only return a score from 1 to 5 with no explanation.
"""
        response = self.model.generate_content(full_prompt)
        return response.text.strip()