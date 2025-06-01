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
        try:
            # Extract text from the response, handling multiple parts if necessary
            response_text = "".join([part.text for part in response.parts])
            score = int(response_text.strip())
            return score
        except ValueError:
            # If parsing fails, return a default or log an error
            response_text = "".join([part.text for part in response.parts]) # Re-extract for logging
            print(f"Warning: Could not parse Gemini feedback response '{response_text.strip()}' to int. Returning 0.")
            return 0