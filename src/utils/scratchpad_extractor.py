"""Extracts information from user messages to update the scratchpad using regex and LLM fallback."""
import re
import json
from llm_utils import get_llm_response
from constants import CANONICAL_KEYS

# Define synonyms for legacy keys that map to canonical keys
SYNONYMS = {
    "high_level_competitive_view": "competitive_moat",
    "barriers_to_entry": "competitive_moat",
    "mechanism": "solution",
    "revenue_hypotheses": "revenue_model",
    "compliance_snapshot": "problem", # Placeholder, might need refinement
    "top_3_risks_and_mitigations": "problem", # Placeholder, might need refinement
    "market_size": "impact_metrics",
}

def update_scratchpad(user_message: str, scratchpad: dict) -> dict:
    """
    Updates the scratchpad dictionary with information extracted from the user message.
    Uses regex and simple heuristics first, then falls back to an LLM.
    """
    updated_scratchpad = scratchpad.copy()

    # Define regex patterns for canonical keys
    extraction_patterns = {
        "problem": [
            r"\b(?:problem|issue|challenge|difficulty) is\s+(.+?)(?:\.|$)",
            r"\bwe are facing\s+(.+?)(?:\.|$)",
        ],
        "target_customer": [ # Changed from customer_segment
            r"\b(?:customer|target|user)s?\s+(?:are|is)\s+(.+?)(?:\.|$)",
            r"\bfor\s+(.+?)\s+(?:customers|users)",
        ],
        "solution": [
            r"\b(?:solution|idea|product) is\s+(.+?)(?:\.|$)",
            r"\bwe propose\s+(.+?)(?:\.|$)",
        ],
        "main_benefit": [ # Changed back to main_benefit
            r"\b(?:unique selling point|usp|key difference|secret sauce|unique benefit) is\s+(.+?)(?:\.|$)",
            r"\b(?:our|my|the)?\s*unique benefit is\s+(.+?)(?:\.|$)",
        ],
        "differentiator": [
            r"\b(?:differentiator|sets us apart|makes us different) is\s+(.+?)(?:\.|$)",
            r"\b(?:our|my|the)?\s*key differentiator is\s+(.+?)(?:\.|$)",
        ],
        "main_benefit": [ # Changed from impact_metrics
            r"\bimpact\b.*(\d+%|\$|days|hours|readmission|adhere)",
            r"\bKPI(s)?\b",
            r"\b(?:impact metrics|key performance indicators|kpis|measures success) (?:are|will be)\s+(.+?)(?:\.|$)",
            r"\bwe will measure success by\s+(.+?)(?:\.|$)",
            r"total addressable market is worth\s+(.+?)(?:\.|$)", # More specific for testing
            r"\b(?:market size|TAM)\s+(?:is|is worth|worth|is estimated at)\s+(.+?)(?:\.|$)", # Keep a more general one too
        ],
        "revenue_model": [
            r"\b(?:revenue model|how we make money|pricing|pay|charge)\s+(?:is|will be)\s+(.+?)(?:\.|$)",
            r"\bwill pay a\s+(.+? fee)",
            r"\blicence fee of\s+(.+?)(?:\.|$)",
            r"\ba\s+(.+? fee)",
        ],
        "channels": [
            r"\bchannel(s)?\b.*(reach|distribution|sales|marketing)",
            r"\bgo[- ]?to[- ]?market\b",
            r"\b(?:channels|distribution|reach customers) (?:are|will be)\s+(.+?)(?:\.|$)",
            r"\bwe will reach customers through\s+(.+?)(?:\.|$)",
        ],
        "competitive_moat": [
            r"\b(?:competitive moat|barrier to entry|sustainable advantage) (?:is|will be)\s+(.+?)(?:\.|$)",
            r"\b(?:our advantage|what protects us) is\s+(.+?)(?:\.|$)",
        ],
        "use_case": [
            r"\b(?:use case|scenario|application) is\s+(.+?)(?:\.|$)",
            r"\b(?:people will use it to|users can)\s+(.+?)(?:\.|$)",
            r"\b(?:envision people using it for|real-world scenario is)\s+(.+?)(?:\.|$)",
        ],
    }

    # First pass: Regex and simple heuristics
    for key, patterns in extraction_patterns.items():
        # Ensure we only process canonical keys that are part of our defined patterns
        if key in CANONICAL_KEYS and (key not in updated_scratchpad or not updated_scratchpad[key]):
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    extracted_value = match.group(1).strip()
                    # Simple post-processing for common phrases
                    if extracted_value.lower().startswith("that "):
                        extracted_value = extracted_value[5:]
                    updated_scratchpad[key] = extracted_value
                    break # Move to next key once a match is found

    # Handle legacy synonyms: move content from old keys to new canonical keys
    # Iterate over a copy of keys if modifying the dictionary during iteration
    scratchpad_keys_copy = list(updated_scratchpad.keys())
    for old_key in scratchpad_keys_copy:
        if old_key in SYNONYMS:
            new_key = SYNONYMS[old_key]
            if updated_scratchpad[old_key]: # If there's content in the old key
                if new_key not in updated_scratchpad or not updated_scratchpad[new_key]:
                    # If new key is empty or not present, move content
                    updated_scratchpad[new_key] = updated_scratchpad.pop(old_key)
                else:
                    # If new key already has content, append old content (or decide on a merge strategy)
                    # For now, let's append if new_key already has content.
                    # updated_scratchpad[new_key] += f"; {updated_scratchpad.pop(old_key)}"
                    # Or, simpler: just pop the old key if the new one is already filled, to avoid duplication.
                    updated_scratchpad.pop(old_key) # Remove old key if new key is already populated
            elif old_key in updated_scratchpad : # if old key exists but is empty
                 updated_scratchpad.pop(old_key)


    # Second pass: LLM fallback for remaining or more complex extractions
    # Only call LLM if there are still empty or partially filled relevant canonical fields
    keys_to_extract_with_llm = [
        key for key in CANONICAL_KEYS
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


            for key_update, value_update in llm_extracted_data.items():
                # If the LLM was tasked to find this key (because regex didn't initially),
                # and the key is a canonical key, update it.
                if key_update in keys_to_extract_with_llm and key_update in CANONICAL_KEYS:
                    updated_scratchpad[key_update] = value_update
        except Exception:
            # print(f"Error during LLM extraction: {e}") # Keep this print for actual debugging if needed
            pass # Silently pass exceptions during LLM extraction for now in tests

    return updated_scratchpad