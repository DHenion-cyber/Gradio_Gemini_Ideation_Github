import os
import sys
from typing import Optional

# Ensure src directory is in path to import llm_utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.llm_utils import query_gemini
from trulens_eval.feedback.provider.base import Provider
from trulens_eval.utils.pyschema import WithClassInfo

class GeminiFeedbackProvider(Provider, WithClassInfo):
    """
    A custom feedback provider that uses the Gemini API via `query_gemini`
    to evaluate helpfulness, relevance, and crispness.
    """

    model_id: str = "gemini-pro"

    def __init__(self, model_id: Optional[str] = None, **kwargs):
        """
        Initialize the Gemini feedback provider.

        Args:
            model_id: The Gemini model to use for feedback. Defaults to "gemini-pro".
        """
        # Pydantic V2 requires super().__init__ to be called before setting attributes
        # if they are not defined as fields or if `model_config['validate_assignment'] = True`
        # For simplicity and compatibility, we'll pass model_id to super if it's a recognized Pydantic field,
        # or handle it after if it's a custom attribute.
        # Since model_id is now a field, it should be handled by Pydantic's init.
        super().__init__(**kwargs)
        if model_id is not None: # Allow overriding the default if provided
            self.model_id = model_id
        # If model_id was not provided, it will use the class-level default "gemini-pro"

    def _get_llm_response(self, prompt: str) -> Optional[float]:
        """
        Helper function to query Gemini and parse a float score from the response.
        Expects the LLM to respond with a single number between 0.0 and 1.0.
        """
        try:
            # Use a specific model and parameters for scoring
            response_text = query_gemini(
                prompt,
                model=self.model_id,
                temperature=0.2, # Lower temperature for more deterministic scoring
                max_output_tokens=10 # Expecting a short numerical response
            )
            # Attempt to parse the score
            score = float(response_text.strip())
            # Clamp score between 0 and 1 as TruLens expects scores in this range
            return max(0.0, min(1.0, score / 10.0)) # Assuming LLM gives 0-10, convert to 0-1
        except ValueError:
            print(f"GeminiFeedbackProvider: Could not parse score from response: {response_text}")
            return None
        except Exception as e:
            print(f"GeminiFeedbackProvider: Error querying Gemini for feedback: {e}")
            return None

    def helpfulness(self, input_text: str, output_text: str) -> Optional[float]:
        """
        Evaluates the helpfulness of the output text given the input text.
        Score should be between 0.0 (not helpful) and 1.0 (very helpful).
        """
        prompt = (
            f"Evaluate the helpfulness of the assistant's response to the user's query. "
            f"Respond with a single numerical score from 0 to 10, where 0 is not at all helpful and 10 is extremely helpful. "
            f"Do not provide any explanation, only the numerical score.\n\n"
            f"User Query: \"{input_text}\"\n"
            f"Assistant Response: \"{output_text}\"\n\n"
            f"Helpfulness Score (0-10):"
        )
        return self._get_llm_response(prompt)

    def relevance(self, input_text: str, output_text: str) -> Optional[float]:
        """
        Evaluates the relevance of the output text to the input text.
        Score should be between 0.0 (not relevant) and 1.0 (very relevant).
        """
        prompt = (
            f"Evaluate the relevance of the assistant's response to the user's query. "
            f"Respond with a single numerical score from 0 to 10, where 0 is not at all relevant and 10 is extremely relevant. "
            f"Do not provide any explanation, only the numerical score.\n\n"
            f"User Query: \"{input_text}\"\n"
            f"Assistant Response: \"{output_text}\"\n\n"
            f"Relevance Score (0-10):"
        )
        return self._get_llm_response(prompt)

    def crispness(self, text: str) -> Optional[float]: # Changed signature to match common use (evaluates a single text)
        """
        Evaluates the crispness (clarity and conciseness) of the given text.
        Score should be between 0.0 (not crisp) and 1.0 (very crisp).
        """
        prompt = (
            f"Evaluate the crispness (clarity and conciseness) of the following text. "
            f"Respond with a single numerical score from 0 to 10, where 0 is not at all crisp and 10 is extremely crisp. "
            f"Do not provide any explanation, only the numerical score.\n\n"
            f"Text to Evaluate: \"{text}\"\n\n"
            f"Crispness Score (0-10):"
        )
        return self._get_llm_response(prompt)

    # Adding other feedback functions as methods for completeness,
    # though they might not all be used directly by the crispness feedback function.
    def conciseness(self, text: str) -> Optional[float]:
        return self.crispness(text) # Using crispness as a proxy

    def correctness(self, input_text: str, output_text: str) -> Optional[float]:
        # This would typically require ground truth. For a general LLM-based eval:
        prompt = (
            f"Evaluate the factual correctness of the assistant's response to the user's query. "
            f"Respond with a single numerical score from 0 to 10, where 0 is completely incorrect and 10 is perfectly correct. "
            f"If correctness cannot be determined, respond with 'None'. "
            f"Do not provide any explanation, only the numerical score or 'None'.\n\n"
            f"User Query: \"{input_text}\"\n"
            f"Assistant Response: \"{output_text}\"\n\n"
            f"Correctness Score (0-10 or None):"
        )
        return self._get_llm_response(prompt)