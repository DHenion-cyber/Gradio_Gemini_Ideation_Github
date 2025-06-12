class ValuePropWorkflow:
    """Skeleton workflow: will collect problem / user / solution / benefit in P3"""
    name = "value_prop"

    def step(self, user_msg, scratchpad):
        # For now just ask the first question.
        if not scratchpad.get("problem"):
            return "What single problem are we solving?", "exploration"
        return "Great. (Full workflow logic will be added next iteration.)", "development"