# src/coach_persona.py

import re

class BehaviorEngine:
    """
    Provides reusable, topic-agnostic behaviors and utilities for chatbot conversation.
    """

    def assess_idea_maturity(self, user_input: str) -> str:
        """
        Assess if the user's input is specific/insightful or broad/generic.
        Returns "advanced" or "novice".
        """
        if len(user_input.split()) > 10 and any(kw in user_input.lower() for kw in ["because", "which leads", "so that"]):
            return "advanced"
        if re.search(r"\b(specific|for example|such as|like)\b", user_input.lower()):
            return "advanced"
        return "novice"

    def detect_user_stance(self, user_input: str, context_step: str = "") -> str:
        """
        Detects user's stance:
        - "interest": showing enthusiasm, ready to move on
        - "uncertain": signals confusion or asks for help
        - "open": wants suggestions or is exploring
        - "decided": makes a clear choice/decision
        """
        input_lower = user_input.lower()
        if any(kw in input_lower for kw in ["not sure", "don't know", "unsure", "maybe", "help", "confused"]):
            return "uncertain"
        if any(kw in input_lower for kw in ["open", "suggest", "advice", "recommend", "explore", "looking for options"]):
            return "open"
        if any(kw in input_lower for kw in ["i have decided", "i want to", "my answer is", "definitely", "for sure", "absolutely"]):
            return "decided"
        if any(kw in input_lower for kw in ["interested", "like to", "want to know more", "keen to"]):
            return "interest"
        # Heuristic: if input is brief and clear, likely decided; if verbose and vague, likely open/uncertain
        if len(input_lower.split()) <= 5:
            return "decided"
        return "interest"

    def active_listening(self, user_input: str) -> str:
        """
        Generates a brief active listening statement.
        """
        return f"I hear you—'{user_input.strip()}'."

    def diplomatic_acknowledgement(self, stance: str) -> str:
        """
        Returns a diplomatic statement based on detected stance.
        """
        templates = {
            "interest": "Great—got it. Let's keep the momentum going.",
            "uncertain": "No worries, it's normal to feel uncertain at this stage.",
            "open": "Love that openness. Let's explore together.",
            "decided": "Sounds like you know what you want. We'll move forward on that.",
        }
        return templates.get(stance, "")

    def offer_example(self, step: str) -> str:
        """
        Returns a generic example for a workflow step.
        """
        examples = {
            "problem": "For example: 'Patients miss appointments because reminders are buried.'",
            "target_user": "For example: 'Radiology schedulers often get overloaded with manual calls.'",
            "solution": "For example: 'A chatbot to automate appointment scheduling.'",
            "benefit": "For example: '10% fewer no-shows.'"
        }
        return examples.get(step, "")

    def offer_strategic_suggestion(self, step: str) -> str:
        """
        Returns a generic suggestion related to the workflow step.
        """
        suggestions = {
            "problem": "Would it help to clarify who is most affected and when?",
            "target_user": "Consider narrowing to one patient group for sharper impact.",
            "solution": "What if you started with a pilot in a single clinic?",
            "benefit": "Measurable outcomes help—want ideas for tracking?"
        }
        return suggestions.get(step, "Would you like a suggestion for this part?")
    def paraphrase_user_input(self, user_input: str, stance: str) -> str:
        """
        Paraphrases the user's input in a thoughtful, coach-like manner,
        avoiding direct verbatim quoting. The paraphrasing can subtly reflect
        the detected stance.
        LLM Behavior Guideline:
        - If stance is "decided": "So, you're thinking [paraphrased idea] for the [step]. That's a clear direction."
        - If stance is "uncertain": "It sounds like you're still exploring [paraphrased uncertainty] regarding the [step]."
        - If stance is "open": "You're open to considering different angles for [paraphrased openness] for the [step], that's great."
        - If stance is "interest": "You've expressed interest in [paraphrased interest] for the [step]."
        - If stance is "neutral" or other: "Okay, I understand you're saying [paraphrased input] regarding the [step]."
        - The core is to rephrase the essence of the user's statement, not just echo.
        """
        # This is a placeholder. Actual paraphrasing would ideally involve an LLM call
        # or more sophisticated NLP techniques. For now, a simple template.
        if stance == "decided":
            return f"So, you've landed on '{user_input.strip()}' as your focus. "
        elif stance == "uncertain":
            return f"It sounds like you're still working through your thoughts on '{user_input.strip()}'. "
        elif stance == "open":
            return f"You're considering options around '{user_input.strip()}'. "
        else:
            return f"I understand you're suggesting '{user_input.strip()}'. "

    def coach_on_decision(self, current_step: str, user_input: str) -> str:
        """
        Coaches the user after they've made a decision for a value proposition element.
        Assesses if the input is broad or specific and prompts accordingly, always
        encouraging further reflection, justification, or consideration of alternatives.

        LLM Behavior Guideline:
        - Assess maturity: Use `assess_idea_maturity(user_input)`.
        - If "novice" (broad):
            - Explain value of specificity: "That's a good starting point for the {current_step}. Often, getting more specific can make the idea stronger and easier to act on."
            - Suggest alternatives/prompt for narrowing: "For example, instead of 'everyone', could we narrow it down to a specific group that feels this problem most acutely? Or for a solution, could we define a key feature to start with?"
            - Ask user to choose: "Would you like to refine this to be more specific, perhaps considering [example specific alternative 1] or [example specific alternative 2], or would you prefer to stick with your current thought for now?"
        - If "advanced" (specific):
            - Affirm briefly: "That's a very specific and clear {current_step}."
            - Invite justification/reasoning: "Could you tell me a bit more about what led you to this particular {user_input}? What's the thinking or experience behind it?"
            - Offer to consider alternatives/broaden (if relevant, context-dependent): "While this is a strong direction, are there any alternative approaches you've considered or might want to explore briefly, just to ensure this is the most impactful path? Or do you feel confident this is the one to pursue?"
        - Always encourage reflection: The prompts should naturally lead to justification or considering alternatives.
        """
        maturity = self.assess_idea_maturity(user_input)
        # Placeholder for LLM-driven adaptive responses.
        # These would be dynamically generated by an LLM based on the guidelines.
        if maturity == "novice":
            # Simplified placeholder response
            return (
                f"That's a good starting point for the {current_step}: '{user_input}'. "
                f"To make it even stronger, could we try to make it more specific? "
                f"For example, if we're talking about the problem, who exactly experiences this most acutely? "
                f"Or if it's a solution, what's one key feature? "
                f"Would you like to refine this, or stick with the current idea?"
            )
        else: # "advanced"
            # Simplified placeholder response
            return (
                f"That's a very specific direction for the {current_step}: '{user_input}'. "
                f"What's the story or reasoning behind this particular choice? "
                f"And are there any alternatives you considered, or do you feel this is the strongest path?"
            )

    def provide_feedback(self, current_value_prop_elements: dict, user_request: str) -> str:
        """
        Provides critical, constructive feedback on the current value proposition elements,
        paired with brief affirmation if possible.

        LLM Behavior Guideline:
        - Analyze `current_value_prop_elements` (problem, target_user, solution, benefit, use_case).
        - Identify strengths: "I like how your [element e.g., solution] directly addresses the [problem/target user need]."
        - Identify areas for improvement/questions:
            - "One thing to consider is whether the [benefit] is compelling enough for the [target user]. Have you thought about [potential enhancement/alternative perspective]?"
            - "Your [problem] statement is clear, but could the [solution] be too broad initially? Perhaps focusing on a core feature first might be more feasible."
            - "The connection between your [target user] and the [benefit] could be stronger. How does [solution] uniquely deliver that for them?"
        - Offer actionable advice: "Maybe we could brainstorm ways to quantify the [benefit]?"
        - Maintain a constructive, supportive tone.
        """
        # Placeholder for LLM-driven adaptive feedback.
        # This would be dynamically generated by an LLM.
        problem = current_value_prop_elements.get("problem", "not yet defined")
        solution = current_value_prop_elements.get("solution", "not yet defined")
        # Simplified placeholder response
        return (
            f"Okay, let's look at what we have. You've identified the problem as '{problem}' and the solution as '{solution}'. "
            f"That's a good start. One area we could explore is how uniquely the solution addresses the problem. "
            f"For example, are there aspects of the solution that could be refined to be even more targeted? "
            f"What are your thoughts on its current specificity?"
        )

    def generate_ideas(self, current_value_prop_elements: dict, user_request: str) -> str:
        """
        Analyzes current input and offers thoughtful, actionable suggestions.

        LLM Behavior Guideline:
        - Review all `current_value_prop_elements`.
        - Identify gaps or areas for development: "Given your focus on [problem] for [target user], have you considered solutions that involve [technology/approach X] or address [related pain point Y]?"
        - Suggest concrete next steps or alternative angles:
            - "If the benefit is [benefit], perhaps a use case focusing on [specific scenario] would highlight that well."
            - "For the solution [solution], an interesting angle could be to integrate [feature/service Z] which might appeal to [target user segment]."
        - Base suggestions on the existing elements to ensure relevance.
        - Avoid generic advice; aim for specific, actionable ideas.
        """
        # Placeholder for LLM-driven adaptive idea generation.
        # This would be dynamically generated by an LLM.
        problem = current_value_prop_elements.get("problem", "N/A")
        target_user = current_value_prop_elements.get("target_user", "N/A")
        # Simplified placeholder response
        return (
            f"Thinking about the problem you've described as '{problem}' for '{target_user}', "
            f"perhaps we could brainstorm some specific features for your solution. "
            f"For instance, if the core issue is [aspect of problem], a feature that [does X] might be valuable. "
            f"Another idea could be to explore [alternative approach/technology]. What sparks your interest more?"
        )
