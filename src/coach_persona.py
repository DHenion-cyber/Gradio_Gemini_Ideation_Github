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
