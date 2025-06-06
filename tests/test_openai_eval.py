import evals
import evals.record
import openai
import os
import random  # For eval_sample signature
from evals.api import CompletionFn, CompletionResult  # For type hinting
from evals.record import Recorder  # For type hinting
from typing import Any  # For type hinting

# Make sure the OpenAI key is configured
# This should be handled by the environment or completion_fn configuration ideally
# For now, keeping it as it might be expected by the 'chatbot-openai' completion_fn if it's custom.
if os.getenv('OPENAI_API_KEY'):
    openai.api_key = os.getenv('OPENAI_API_KEY')

class ChatbotEval(evals.Eval):
    def __init__(self, completion_fn: CompletionFn, samples_jsonl: str, *args, **kwargs):
        # The framework passes a single resolved completion_fn.
        # The base class expects a list.
        super().__init__(completion_fns=[completion_fn], samples_jsonl=samples_jsonl, *args, **kwargs)
        # self.samples_jsonl is now set by the parent.

    def eval_sample(self, sample: Any, rng: random.Random):
        # rng is not used by us but part of the signature from the base class
        
        if not self.completion_fns or len(self.completion_fns) == 0:
            evals.record.record_error("No completion_fns configured for ChatbotEval", sample=sample)
            return

        active_completion_fn = self.completion_fns[0]

        prompt_content = sample.get('input')
        ideal_response = sample.get('ideal', '')

        if prompt_content is None:
            evals.record.record_error("Sample missing 'input' field.", sample=sample)
            return

        try:
            # Assuming active_completion_fn is a callable that takes a prompt string
            # and returns a CompletionResult object (like OpenAICompletionFn).
            result_obj: CompletionResult = active_completion_fn(prompt=prompt_content)
            completed_text = result_obj.get_first_choice().strip()
        except Exception as e:
            evals.record.record_error(f"API call or completion processing failed: {e}", sample_prompt=prompt_content, exception=str(e))
            completed_text = "" 

        is_match = (completed_text == ideal_response)

        evals.record.record_match(
            is_match,
            expected=ideal_response,
            output=completed_text,
            sample_prompt=prompt_content, # Using a more descriptive key for the prompt
            metrics={"accuracy": 1.0 if is_match else 0.0} # Example of custom metric
        )

    def run(self, recorder: Recorder):
        samples = self.get_samples()  # This uses self.samples_jsonl set in __init__
        self.eval_all_samples(recorder, samples)
        
        # Calculate final metrics from recorded events
        accuracy = evals.record.get_accuracy(recorder)
        # You can add more custom metric calculations here if needed
        
        return {"accuracy": accuracy}