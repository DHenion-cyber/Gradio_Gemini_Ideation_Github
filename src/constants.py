"""Defines constants used throughout the application, such as scratchpad keys and API limits."""
REQUIRED_SCRATCHPAD_KEYS = [
    "problem",
    "target_customer", # Changed from target_user
    "solution",
    "main_benefit", # Changed from benefit
    "differentiator",
    "use_case", # Will be a string, potentially holding multiple use cases described in natural language
    "research_requests" # Will be a list of strings or dicts
]

# Initialize with correct types
EMPTY_SCRATCHPAD = {
    "problem": "",
    "target_customer": "", # Changed from target_user
    "solution": "",
    "main_benefit": "", # Changed from benefit
    "differentiator": "",
    "use_case": "",
    "research_requests": []
}

MAX_PERPLEXITY_CALLS = 3

# Canonical keys for scratchpad extraction
CANONICAL_KEYS = [
    "problem",
    "target_customer",
    "solution",
    "main_benefit",
    "differentiator",
    "revenue_model",
    "channels",
    "competitive_moat",
    "use_case"
]