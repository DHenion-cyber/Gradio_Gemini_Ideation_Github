import re
import json # Added import for json
from src.llm_utils import get_llm_response

def update_scratchpad(user_message: str, scratchpad: dict) -> dict:
    """
    Updates the scratchpad dictionary with information extracted from the user message.
    Uses regex and simple heuristics first, then falls back to an LLM.
    """
    updated_scratchpad = scratchpad.copy()

    # Define keys for extraction and their corresponding regex patterns/heuristics
    extraction_patterns = {
        "problem": [
            r"\b(?:problem|issue|challenge|difficulty) is\s+(.+?)(?:\.|$)",
            r"\bwe are facing\s+(.+?)(?:\.|$)",
        ],
        "customer_segment": [
            r"\b(?:customer|target|user)s?\s+(?:are|is)\s+(.+?)(?:\.|$)",
            r"\bfor\s+(.+?)\s+(?:customers|users)",
        ],
        "solution": [
            r"\b(?:solution|idea|product) is\s+(.+?)(?:\.|$)",
            r"\bwe propose\s+(.+?)(?:\.|$)",
        ],
        "differentiator": [
            r"\b(?:differentiator|unique selling point|usp|key difference|secret sauce) is\s+(.+?)(?:\.|$)",
            r"\b(?:sets us apart|makes us different) by\s+(.+?)(?:\.|$)",
            r"\bour key differentiator is\s+(.+?)(?:\.|$)",
        ],
        "revenue_model": [
            r"\b(?:revenue model|how we make money|pricing|pay|charge)\s+(?:is|will be)\s+(.+?)(?:\.|$)",
            r"\bwill pay a\s+(.+? fee)",
            r"\blicence fee of\s+(.+?)(?:\.|$)",
            r"\ba\s+(.+? fee)",
        ],
        "value_proposition": [
            r"\b(?:value proposition|benefit)\s+(?:is|will be)\s+(.+?)(?:\.|$)",
            r"\bwe offer\s+(.+?)\s+to",
        ],
        "market_size": [
            r"\b(?:market size|total addressable market|TAM) is\s+(.+?)(?:\.|$)",
            r"\bworth\s+(.+?)\s+billion",
        ],
    }

    # First pass: Regex and simple heuristics
    for key, patterns in extraction_patterns.items():
        if key not in updated_scratchpad or not updated_scratchpad[key]: # Only try to extract if key is not already filled
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    extracted_value = match.group(1).strip()
                    # Simple post-processing for common phrases
                    if extracted_value.lower().startswith("that "):
                        extracted_value = extracted_value[5:]
                    updated_scratchpad[key] = extracted_value
                    break # Move to next key once a match is found

    # Second pass: LLM fallback for remaining or more complex extractions
    # Only call LLM if there are still empty or partially filled relevant fields
    keys_to_extract_with_llm = [
        key for key in extraction_patterns.keys()
        if key not in updated_scratchpad or not updated_scratchpad[key]
    ]

    if keys_to_extract_with_llm:
        llm_prompt = (
            f"From the following user message, extract any information relevant to these keys: "
            f"{', '.join(keys_to_extract_with_llm)}. "
            f"Provide the extracted information as a JSON object with the keys as specified. "
            f"If no information is found for a key, omit that key from the JSON. "
            f"User message: \"{user_message}\""
        )
        try:
            llm_response = get_llm_response(llm_prompt, temperature=0.1)
            # Attempt to parse LLM response as JSON
            llm_extracted_data = {}
            # Basic attempt to find JSON in the response, handling potential markdown code blocks
            json_match = re.search(r"```json\n({.*?})\n```", llm_response, re.DOTALL)
            if json_match:
                json_string = json_match.group(1)
            else:
                json_string = llm_response # Assume the whole response is JSON if no markdown block

            try:
                llm_extracted_data = json.loads(json_string)
            except json.JSONDecodeError:
                # print(f"Warning: LLM response not valid JSON: {json_string}") # Keep this print for actual debugging if needed
                # Fallback for non-JSON responses, try to parse key-value pairs if possible
                for key_fallback in keys_to_extract_with_llm: # Renamed to avoid clash
                    # Simple heuristic for "key: value" in plain text
                    match = re.search(rf"{key_fallback}:\s*(.+)", llm_response, re.IGNORECASE)
                    if match:
                        llm_extracted_data[key_fallback] = match.group(1).strip()


            for key_update, value_update in llm_extracted_data.items(): # Renamed to avoid clash
                # If the LLM was tasked to find this key (because regex didn't initially),
                # and the key is a known extraction target, update it.
                if key_update in keys_to_extract_with_llm and key_update in extraction_patterns:
                    updated_scratchpad[key_update] = value_update
        except Exception:
            # print(f"Error during LLM extraction: {e}") # Keep this print for actual debugging if needed
            pass # Silently pass exceptions during LLM extraction for now in tests

    return updated_scratchpad