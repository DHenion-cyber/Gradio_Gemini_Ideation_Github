# Defines the phase order and scratchpad keys for the Value Proposition workflow.

# The order of phases as they should appear and be processed.
# These names should correspond to the phase_name attribute of the PhaseEngineBase subclasses
# and the filenames in the src/workflows/value_prop/phases/ directory (e.g., use_case.py).
PHASE_ORDER = [
    "intake",
    "problem",
    "target_customer",
    "solution",
    "main_benefit",
    "differentiator",
    "use_case",
    "recommendation", # Handles showing recommendations
    "iteration",      # Top-level iteration phase (might contain sub-phases like revise, rerun)
    "summary"         # Final summary phase
]

# Scratchpad keys specific to the Value Proposition workflow.
# These are the keys that will be initialized in st.session_state.scratchpad
# when this workflow is started.
SCRATCHPAD_KEYS = [
    "vp_background",
    "vp_interests",
    "vp_problem_motivation",
    "vp_anything_else",
    "vp_use_case", # Renamed from use_case for consistency and to match intake keys
    "problem", # Assuming this remains unprefixed as per original structure for other phases
    "target_customer",
    "solution",
    "main_benefit",
    "differentiator",
    "research_requests", # from original ValuePropWorkflow
    "cached_recommendations", # from original ValuePropWorkflow, used by RecommendationPhase
    "final_summary" # from original ValuePropWorkflow, used by SummaryPhase
]

# Optional: Define sub-phases for iteration if it's managed as a distinct set of engines
ITERATION_SUB_PHASES = [
    "revise",       # User chooses what to revise
    "revise_detail",# User provides new text for the chosen item
    "rerun"         # Triggers re-running recommendations
]
# If iteration is a single complex PhaseEngine that manages these states internally,
# then ITERATION_SUB_PHASES might not be needed here but within that engine.
# For now, listing them for clarity as they were distinct states.

# Mapping of phase names to their class names (optional, for dynamic loading if needed)
# PHASE_CLASS_MAP = {
#     "use_case": "UseCasePhase",
#     "problem": "ProblemPhase",
#     # ... and so on
#     "iteration": "IterationPhase", # This could be a parent phase for revise, revise_detail, rerun
# }

# Note: The actual PhaseEngine classes will be in src/workflows/value_prop/phases/
# e.g., src/workflows/value_prop/phases/use_case.py will contain UseCasePhase.