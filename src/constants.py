MAX_PERPLEXITY_CALLS = 3
# Define the keys for the scratchpad based on the idea maturity rubric
# This ensures consistency across modules.
# (Assuming RUBRIC is defined in src.utils.idea_maturity)
# To avoid circular import, we'll define the keys explicitly here for now.
# If RUBRIC changes, this list must be updated.
_rubric_keys = [
    "problem", "customer_segment", "solution", "differentiator",
    "impact_metrics", "revenue_model", "channels", "competitive_moat"
    # Add other keys from RUBRIC["elements"] if they exist
]
INITIAL_SCRATCHPAD = {key: "" for key in _rubric_keys}