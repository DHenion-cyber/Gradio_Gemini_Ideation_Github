from src import conversation_phases # Import conversation_phases

class ValuePropWorkflow:
    """Skeleton workflow: will collect problem / user / solution / benefit in P3"""
    name = "value_prop"

    def step(self, user_msg, scratchpad):
        # If problem is not in scratchpad, ask the first question.
        if not scratchpad.get("problem"):
            return "What single problem are we solving?", "exploration"
        
        # If problem is already in scratchpad (e.g. from intake),
        # delegate to the standard exploration phase handler.
        # This allows the conversation to proceed through other value prop elements.
        if user_msg: # Ensure there's a user message to process
             return conversation_phases.handle_exploration(user_msg, scratchpad)
        
        # Fallback or if there's no user_msg but problem exists (should be rare here)
        return "Great. (Full workflow logic will be added next iteration.)", "development"