from src.coach_persona import BehaviorEngine

class ValuePropWorkflow:
    def __init__(self, context=None):
        self.context = context or {}
        self.behavior = BehaviorEngine()
        self.current_step = "problem"  # Initial step
        self.scratchpad = {
            "problem": "",
            "target_customer": "", # Changed from target_user
            "solution": "",
            "main_benefit": "", # Changed back to main_benefit
            "differentiator": "",
            "use_case": "", # Will store natural language description of use case(s)
            "research_requests": [] # List of strings or dicts
        }
        self.completed = False
        self.intake_complete = False  # Flag for the initial intake message

    def suggest_next_step(self, user_input=None):
        """
        Suggest the next most relevant step based on current scratchpad content and user intent.
        Allow user to revisit or expand previous steps if desired.
        """
        steps = ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]
        # If the user input clearly refers to a previous or later step, honor that
        # (you can use simple keyword matching or a more advanced intent detector)
        if user_input:
            for step in steps:
                if step in user_input.lower(): # Simple keyword matching
                    self.current_step = step
                    return step
        # Otherwise, suggest the next incomplete step, but do not force it
        for step in steps:
            if not self.scratchpad.get(step):
                self.current_step = step
                return step
        # If all steps have content, remain flexible and ask what the user wants to focus on next
        self.current_step = "review"
        return "review"

    def process_user_input(self, user_input: str):
        preliminary_messages = []
        user_input_stripped = user_input.strip()
        core_response = ""
        is_intro_only_turn = False

        # 1. Handle intake-to-ideation transition message (once at the beginning)
        if self.current_step == "problem" and not self.intake_complete:
            preliminary_messages.append(
                "Thanks for sharing! I'll help you develop and vet your ideas now. "
                "I will continue to ask you questions, but you're welcome to ask me for ideas, analysis, or feedback at any point."
            )
            self.intake_complete = True

        # 2. Handle dedicated step introductions
        # Show intro if it's the differentiator step, main_benefit is filled, and differentiator in scratchpad is still empty.
        if self.current_step == "differentiator" and \
           self.scratchpad.get("main_benefit") and \
           not self.scratchpad.get("differentiator"):
            differentiator_intro_message = (
                "Let's define what makes your solution unique. "
                "This helps clarify your competitive advantage and will later help to position your idea effectively.\n"
                "What specific aspects set your solution apart from alternatives?"
            )
            if not preliminary_messages or differentiator_intro_message not in preliminary_messages[-1]:
                 preliminary_messages.append(differentiator_intro_message)
            if not user_input_stripped:
                is_intro_only_turn = True # Intro is the main response for this turn

        # Show intro if it's the use_case step, differentiator is filled, and use_case in scratchpad is still empty.
        elif self.current_step == "use_case" and \
             self.scratchpad.get("differentiator") and \
             not self.scratchpad.get("use_case"):
            use_case_intro_message = (
                "Now let's think about specific use cases. "
                "How do you envision people using your solution in real-world scenarios?"
            )
            if not preliminary_messages or use_case_intro_message not in preliminary_messages[-1]:
                preliminary_messages.append(use_case_intro_message)
            if not user_input_stripped:
                is_intro_only_turn = True # Intro is the main response for this turn
        
        if not is_intro_only_turn:
            # 3. Handle empty user input if not an intro-only response and current step needs input
            if not user_input_stripped:
                # Check if the current step is genuinely awaiting input (i.e., not yet filled in scratchpad).
                if not self.scratchpad.get(self.current_step) and \
                   (self.current_step != "problem" or self.intake_complete):
                    step_display_name = self.current_step.replace("_", " ")
                    article = "an" if step_display_name.lower().startswith(("a", "e", "i", "o", "u")) else "a"
                    prompt_message = (
                        f"It seems we're working on defining {article} {step_display_name}, "
                        f"but I didn't receive your input for it. Could you please share your thoughts on the {step_display_name}?"
                    )
                    core_response = prompt_message
                # else: user_input_stripped is empty, but no specific prompt needed (e.g., step filled, or problem before intake)
                # core_response remains empty, preliminary_messages (if any) will be shown.
            else: # user_input_stripped is NOT empty
                # 4. General stance handling and coaching
                stance = self.behavior.detect_user_stance(user_input_stripped, self.current_step)

                # Store user input based on stance and step
                if stance == "decided":
                    self.scratchpad[self.current_step] = user_input_stripped
                elif self.current_step == "differentiator" and \
                     self.scratchpad.get("main_benefit") and \
                     user_input_stripped and \
                     not self.scratchpad.get("differentiator"):
                    self.scratchpad["differentiator"] = user_input_stripped
                    if stance != "decided": stance = "decided" # Treat as decided for coaching
                elif self.current_step == "use_case" and \
                     self.scratchpad.get("differentiator") and \
                     user_input_stripped and \
                     not self.scratchpad.get("use_case"):
                    self.scratchpad["use_case"] = user_input_stripped
                    if stance != "decided": stance = "decided" # Treat as decided for coaching

                if stance == "decided":
                    core_response = self.behavior.coach_on_decision(self.current_step, user_input_stripped)
                else: # uncertain, open, interest, neutral
                    core_response = self.behavior.paraphrase_user_input(user_input_stripped, stance, self.current_step)

        # Combine preliminary_messages and core_response
        full_response_parts = []
        if preliminary_messages:
            full_response_parts.extend(preliminary_messages)
        
        if core_response: # Only add core_response if it's not empty and not redundant with preliminary
            # Avoid adding core_response if it's identical to the last preliminary message (e.g. intro was the core)
            if not (preliminary_messages and preliminary_messages[-1] == core_response):
                 full_response_parts.append(core_response)

        final_response_str = "\n\n".join(filter(None, full_response_parts)).strip()

        reflection_prompt = "\n\nWhat do you think? Would you like to explore this direction, or focus on another aspect?"
        if final_response_str: # Only add reflection if there's a base response
            return final_response_str + reflection_prompt
        return "" # Return empty string if nothing was generated

    def add_research_request(self, step: str, details: str = ""):
        self.scratchpad["research_requests"].append({"step": step, "details": details})

    def actionable_recommendations(self):
        recs = []
        for req in self.scratchpad.get("research_requests", []):
            # Ensuring natural language for recommendations
            if isinstance(req, dict):
                 recs.append(f"It's recommended to research the {req.get('step', 'relevant area')} further, focusing on: {req.get('details', 'specific aspects not yet defined')}.")
            elif isinstance(req, str):
                 recs.append(f"Further research is suggested for: {req}.")
            else:
                 recs.append("Additional research may be beneficial.")
        if not recs:
            return "" # Return empty string if no recommendations, to be handled by generate_summary
        return "\n".join(recs)

    def generate_summary(self):
        # Generates a structured summary string with a main paragraph, use cases, and recommendations.
        # This method now constructs the final user-facing summary directly.

        problem_desc = self.scratchpad.get('problem')
        target_user_desc = self.scratchpad.get('target_customer') # Corrected: target_customer
        solution_desc = self.scratchpad.get('solution')
        benefit_desc = self.scratchpad.get('main_benefit') # Corrected: main_benefit
        differentiator_desc = self.scratchpad.get('differentiator')
        use_case_desc = self.scratchpad.get('use_case')

        summary_parts = []

        # 1. Main Summary Paragraph
        # Only include elements if they are defined.
        # Using more natural phrasing.
        main_summary_elements = []
        if problem_desc:
            main_summary_elements.append(f"The core problem being addressed is {problem_desc}.")
        if target_user_desc:
            main_summary_elements.append(f"This primarily affects {target_user_desc}.")
        if solution_desc:
            main_summary_elements.append(f"The proposed solution involves {solution_desc}.")
        if benefit_desc:
            main_summary_elements.append(f"The key benefit this offers is {benefit_desc}.")
        if differentiator_desc:
            main_summary_elements.append(f"What sets this apart is {differentiator_desc}.")
        
        if main_summary_elements:
            summary_paragraph = " ".join(main_summary_elements)
            summary_parts.append(summary_paragraph)
        else:
            summary_parts.append("The value proposition is still under development.")

        # 2. Use Case Section
        if use_case_desc:
            # Ensure natural language, not bullets.
            # If use_case_desc might contain multiple points, they should already be in natural language.
            summary_parts.append(f"\n\n**Use Case(s):**\n{use_case_desc}")
        else:
            summary_parts.append("\n\n**Use Case(s):**\nNot yet defined.")


        # 3. Actionable Recommendations Section
        recommendations_text = self.actionable_recommendations()
        if recommendations_text:
            summary_parts.append(f"\n\n**Actionable Recommendations:**\n{recommendations_text}")
        
        return "".join(summary_parts).strip()

    def is_complete(self):
        return self.completed

    def get_step(self):
        return self.current_step