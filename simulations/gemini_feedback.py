import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

class GeminiFeedbackProvider:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

    def ask(self, prompt: str, input_text: str, response_text: str) -> int:
        full_prompt = f"""
        You are a helpful evaluator. Given the user's message and the assistant's response, answer the following:
        PROMPT: {input_text}
        RESPONSE: {response_text}
        QUESTION: {prompt}
        Only return a score from 1 to 5 with no explanation.
        """
        response = self.model.generate_content(full_prompt) # Use synchronous version
        
        # Debugging: Print raw response parts and stripped text
        print(f"DEBUG: Raw Gemini response parts: {response.parts}")
        response_text = "".join([part.text for part in response.parts])
        print(f"DEBUG: Stripped Gemini response text: '{response_text.strip()}'")

        # Attempt to extract score
        import re
        match = re.search(r'\d+', response_text.strip())
        if match:
            score = int(match.group(0))
            return score
        else:
            # If no integer is found, log the full response and return 0
            print(f"Warning: No integer found in Gemini feedback response: '{response_text.strip()}'. Returning 0.")
            return 0