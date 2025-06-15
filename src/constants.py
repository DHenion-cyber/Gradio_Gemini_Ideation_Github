REQUIRED_SCRATCHPAD_KEYS = [
    "problem",
    "target_user",
    "solution",
    "benefit",
    "differentiator",
    "use_case", # Will be a string, potentially holding multiple use cases described in natural language
    "research_requests" # Will be a list of strings or dicts
]

# Initialize with correct types
EMPTY_SCRATCHPAD = {
    "problem": "",
    "target_user": "",
    "solution": "",
    "benefit": "",
    "differentiator": "",
    "use_case": "",
    "research_requests": []
}

MAX_PERPLEXITY_CALLS = 3