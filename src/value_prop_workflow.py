from src.coach_persona import BehaviorEngine

class ValuePropWorkflow:
    def __init__(self, context=None):
        self.context = context or {}
        self.behavior = BehaviorEngine()
        self.current_step = "problem"  # Initial step
        self.scratchpad = {
            "problem": "",
            "target_user": "",
            "solution": "",
            "benefit": "",
            "use_case": "",  # Added use_case
            "research_requests": []
        }
        self.completed = False
        self.intake_complete = False  # Flag for the initial intake message

    def next_step(self):
        steps = ["problem", "target_user", "solution", "benefit", "use_case"]
        try:
            current_idx = steps.index(self.current_step)
            if current_idx + 1 < len(steps):
                self.current_step = steps[current_idx + 1]
            else:
                self.completed = True
        except ValueError:
            self.completed = True # Should not happen if current_step is always valid

    def process_user_input(self, user_input: str):
        generated_response_parts = []
        user_input_stripped = user_input.strip()

        # 1. Handle intake-to-ideation transition message (once at the beginning)
        if self.current_step == "problem" and not self.intake_complete:
            generated_response_parts.append(
                "Thanks for sharing! I’ll help you develop and vet your ideas now. "
                "I will continue to ask you questions, but you’re welcome to ask me for ideas, analysis, or feedback at any point."
            )
            self.intake_complete = True

        # 2. Handle dedicated use case step introduction
        # Show intro if it's the use_case step, benefit is filled, and use_case in scratchpad is still empty.
        if self.current_step == "use_case" and \
           self.scratchpad.get("benefit") and \
           not self.scratchpad.get("use_case"):
            
            use_case_intro_message = (
                "Let’s define one or two real-world use cases for your idea. "
                "This helps clarify the value in a relatable way and will later help to engage stakeholders at all levels.\n"
                "Is there a story that inspired your vision or would you like my help creating one based on using a general scenario and verifiable findings?"
            )
            # Avoid adding intro if it was already the last part of the response (e.g. user sent empty message)
            if not generated_response_parts or use_case_intro_message not in generated_response_parts[-1]:
                 generated_response_parts.append(use_case_intro_message)
            
            # If user_input is empty after this intro, we are done for this turn.
            if not user_input_stripped:
                 return "\n\n".join(filter(None, generated_response_parts)).strip()

        # 3. General stance handling and coaching
        stance = self.behavior.detect_user_stance(user_input_stripped, self.current_step)
        
        # Store user input if it's a "decided" stance.
        # Also, if it's the use_case step and user provided input for it (and it's not yet in scratchpad).
        if stance == "decided":
            self.scratchpad[self.current_step] = user_input_stripped
        elif self.current_step == "use_case" and \
             self.scratchpad.get("benefit") and \
             user_input_stripped and \
             not self.scratchpad.get("use_case"):
            self.scratchpad["use_case"] = user_input_stripped
            # If stance wasn't 'decided' but we captured use_case, treat as 'decided' for coaching flow.
            if stance != "decided":
                stance = "decided"

        if stance == "uncertain":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(self.behavior.offer_example(self.current_step))
            generated_response_parts.append(
                f"Could you try to define the {self.current_step} more clearly, or would you like to brainstorm some ideas together for it?"
            )
        elif stance == "open":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(self.behavior.offer_strategic_suggestion(self.current_step))
            generated_response_parts.append(
                f"What are your thoughts on that suggestion, or would you like to explore other angles for the {self.current_step}?"
            )
        elif stance == "interest":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(
                f"It sounds like you're making good progress on the {self.current_step}. "
                "Would you like to refine this further, or shall we consider how this connects to the next part of your value proposition?"
            )
        elif stance == "decided":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(
                self.behavior.coach_on_decision(self.current_step, user_input_stripped)
            )
        else:  # Fallback for other/unclear stances
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, "neutral"))
            generated_response_parts.append(
                f"That's an interesting perspective on the {self.current_step}. "
                "Could you elaborate a bit more on your reasoning, or would you like to consider some alternative ways to approach this?"
            )
        
        return "\n\n".join(filter(None, generated_response_parts)).strip()
    def add_research_request(self, step: str, details: str = ""):
        self.scratchpad["research_requests"].append({"step": step, "details": details})

    def actionable_recommendations(self):
        recs = []
        for req in self.scratchpad["research_requests"]:
            recs.append(f"Suggested research for '{req['step']}': {req.get('details', 'TBD')}")
        if not recs:
            return "No additional research was requested."
        return "\n".join(recs)

    def generate_summary(self):
        summary = (
            f"{self.scratchpad.get('solution', 'A solution')} is proposed to address the problem: "
            f"{self.scratchpad.get('problem', 'N/A')} "
            f"for {self.scratchpad.get('target_user', 'the target users')}. "
            f"The anticipated benefit is: {self.scratchpad.get('benefit', 'N/A')}."
        )
        if self.scratchpad["research_requests"]:
            summary += (
                " Supporting evidence and further research were identified and can be reviewed in the actionable recommendations section."
            )
        return summary

    def is_complete(self):
        return self.completed

    def get_step(self):
        return self.current_step