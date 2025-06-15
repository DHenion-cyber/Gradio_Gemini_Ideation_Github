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
        LLM Behavior Guideline:
        - Acknowledge the user's input by paraphrasing or summarizing its essence naturally and conversationally.
        - Avoid direct quotation of the user's input.
        """
        return "Behavioral instruction: Acknowledge the user's input by paraphrasing or summarizing its essence naturally and conversationally, without direct quotation. For example, 'Okay, I understand you're saying...' or 'Got it, so the main point is...'"

    def diplomatic_acknowledgement(self, stance: str) -> str:
        """
        Returns a diplomatic statement based on detected stance.
        LLM Behavior Guideline:
        - Based on the user's stance, provide an appropriate diplomatic acknowledgement.
        - "interest": Convey enthusiasm and readiness to continue.
        - "uncertain": Offer reassurance and normalize the feeling of uncertainty.
        - "open": Express appreciation for their openness and willingness to explore.
        - "decided": Acknowledge their clarity and indicate readiness to proceed.
        - Default: Offer a neutral, encouraging acknowledgement.
        """
        if stance == "interest":
            return "Behavioral instruction: The user is showing interest. Convey enthusiasm and readiness to keep the momentum going. For example, 'Great—got it. Let's keep the momentum going.'"
        elif stance == "uncertain":
            return "Behavioral instruction: The user seems uncertain. Offer reassurance and normalize this feeling. For example, 'No worries, it's normal to feel uncertain at this stage.'"
        elif stance == "open":
            return "Behavioral instruction: The user is open to suggestions. Express appreciation for their openness and willingness to explore. For example, 'Love that openness. Let's explore together.'"
        elif stance == "decided":
            return "Behavioral instruction: The user seems to have made a decision. Acknowledge their clarity and indicate readiness to proceed based on their decision. For example, 'Sounds like you know what you want. We'll move forward on that.'"
        else:
            return "Behavioral instruction: Offer a neutral, encouraging acknowledgement of the user's input."

    def offer_example(self, step: str) -> str:
        """
        Returns a generic example for a workflow step.
        LLM Behavior Guideline:
        - Offer a single, concise, relevant example for the given workflow `step`.
        - Do not use quotation marks or list multiple examples.
        - The example should be illustrative and help the user understand the type of input expected.
        """
        if step == "problem":
            return "Behavioral instruction: Offer a single, concise, relevant example for the 'problem' step, without quotes. For instance, you could describe a common issue like patients missing appointments due to overlooked reminders."
        elif step == "target_user":
            return "Behavioral instruction: Offer a single, concise, relevant example for the 'target_user' step, without quotes. For example, mention a specific group like radiology schedulers who often get overloaded with manual calls."
        elif step == "solution":
            return "Behavioral instruction: Offer a single, concise, relevant example for the 'solution' step, without quotes. For instance, suggest a tool like a chatbot to automate appointment scheduling."
        elif step == "main_benefit":
            return "Behavioral instruction: Offer a single, concise, relevant example for the 'main_benefit' step, without quotes. For example, state a quantifiable outcome like achieving 10% fewer no-shows."
        elif step == "differentiator":
            return "Behavioral instruction: Offer a single, concise, relevant example for the 'differentiator' step, without quotes. For example, mention a unique feature like AI-powered personalization that sets the solution apart."
        elif step == "use_case":
            return "Behavioral instruction: Offer a single, concise, relevant example for the 'use_case' step, without quotes. For example, describe a scenario like a busy professional using the solution to quickly find healthy meal options during their lunch break."
        return "Behavioral instruction: Offer a single, concise, relevant example appropriate for the current context, without using quotes."

    def offer_strategic_suggestion(self, step: str) -> str:
        """
        Returns a generic suggestion related to the workflow step.
        LLM Behavior Guideline:
        - Offer a strategic suggestion to help the user clarify or advance the current workflow `step`.
        - The suggestion should be a question or a gentle prompt, not a direct command.
        - Avoid quoting examples within the suggestion.
        """
        if step == "problem":
            return "Behavioral instruction: Offer a strategic suggestion for the 'problem' step. For example, prompt them to consider who is most affected and when, or ask if clarifying that would be helpful."
        elif step == "target_user":
            return "Behavioral instruction: Offer a strategic suggestion for the 'target_user' step. For example, suggest considering narrowing to one patient group for sharper impact."
        elif step == "solution":
            return "Behavioral instruction: Offer a strategic suggestion for the 'solution' step. For example, ask what if they started with a pilot in a single clinic."
        elif step == "main_benefit":
            return "Behavioral instruction: Offer a strategic suggestion for the 'main_benefit' step. For example, mention that measurable outcomes help and ask if they want ideas for tracking."
        elif step == "differentiator":
            return "Behavioral instruction: Offer a strategic suggestion for the 'differentiator' step. For example, ask if they've considered how their solution addresses unmet needs better than existing alternatives."
        elif step == "use_case":
            return "Behavioral instruction: Offer a strategic suggestion for the 'use_case' step. For example, ask if they've considered how different user segments might have distinct primary use cases for the solution, or if detailing a specific scenario would help clarify its value."
        return "Behavioral instruction: Offer a helpful, strategic suggestion relevant to the current step, framed as a question or gentle prompt."

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
        # LLM Behavior Guideline is in the docstring.
        # This method constructs the instruction for the LLM.
        # The `[paraphrased ...]` parts in the original guideline are for the LLM to fill.
        # The `[step]` placeholder here should be replaced by the actual current step name if available,
        # or the LLM should infer it from context if not explicitly passed.
        # For now, we'll assume `context_step` might be available or LLM infers.

        base_instruction = "Behavioral instruction: Paraphrase the user's input naturally and conversationally, without direct quotation. Rephrase the essence of their statement. "

        if stance == "decided":
            return base_instruction + "They seem to have a clear direction. You could say something like: 'So, you're thinking [paraphrase of user's idea]. That's a clear direction.' or 'Okay, so your focus is on [paraphrase of user's idea].'"
        elif stance == "uncertain":
            return base_instruction + "They sound like they're still exploring or unsure. You could say something like: 'It sounds like you're still exploring [paraphrase of user's uncertainty].' or 'Okay, so you're working through your thoughts on [paraphrase of user's idea].'"
        elif stance == "open":
            return base_instruction + "They seem open to considering different angles. You could say something like: 'You're open to considering different angles for [paraphrase of user's openness], that's great.' or 'Okay, so you're looking at options around [paraphrase of user's idea].'"
        elif stance == "interest":
            return base_instruction + "They've expressed interest. You could say something like: 'You've expressed interest in [paraphrase of user's interest].' or 'Got it, you're interested in [paraphrase of user's idea].'"
        else: # neutral or other
            return base_instruction + "Acknowledge their input clearly. You could say something like: 'Okay, I understand you're saying [paraphrase of user's input].' or 'Understood, your point is [paraphrase of user's input].'"

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
        # LLM Behavior Guideline is in the docstring.
        # This method constructs the instruction for the LLM.

        # The user's actual input (`user_input`) should NOT be quoted in the LLM's response.
        # The LLM should refer to "your idea for the {current_step}" or similar.

        if maturity == "novice":
            return (
                f"Behavioral instruction: The user has made a decision for the {current_step}. "
                "Their input seems like a good starting point but could be more specific. "
                "Explain the value of specificity (e.g., 'Often, getting more specific can make the idea stronger...'). "
                "Suggest they refine it by offering an example of how to be more specific in this context "
                "(e.g., 'For example, instead of a general group, could we identify a specific user segment? Or for a solution, a key starting feature?'). "
                "Then, ask if they'd like to refine their idea to be more specific, perhaps suggesting one or two hypothetical alternatives (without quoting their input), or if they prefer to stick with their current thought. "
                "Do not directly quote their original input."
            )
        else:  # "advanced"
            return (
                f"Behavioral instruction: The user has made a decision for the {current_step}, and their input is quite specific and clear. "
                "Affirm this briefly (e.g., 'That's a very specific and clear direction.'). "
                "Then, invite them to share more about their reasoning or the experience behind their choice (e.g., 'Could you tell me a bit more about what led you to this particular idea?'). "
                "You might also gently offer to explore alternatives if it seems appropriate, to ensure this is the most impactful path (e.g., 'Are there any alternative approaches you considered, or do you feel confident this is the one to pursue?'), "
                "or simply ask if they are ready to move to the next step. "
                "Do not directly quote their original input."
            )

    def provide_feedback(self, current_value_prop_elements: dict, user_request: str) -> str:
        """
        Provides critical, constructive feedback on the current value proposition elements,
        paired with brief affirmation if possible.

        LLM Behavior Guideline:
        - Analyze `current_value_prop_elements` (problem, target_user, solution, main_benefit, differentiator, use_case).
        - Identify strengths: "I like how your [element e.g., solution] directly addresses the [problem/target user need]."
        - Identify areas for improvement/questions:
            - "One thing to consider is whether the [main_benefit] is compelling enough for the [target user]. Have you thought about [potential enhancement/alternative perspective]?"
            - "Your [problem] statement is clear, but could the [solution] be too broad initially? Perhaps focusing on a core feature first might be more feasible."
            - "The connection between your [target user] and the [main_benefit] could be stronger. How does [solution] uniquely deliver that for them?"
        - Offer actionable advice: "Maybe we could brainstorm ways to quantify the [main_benefit]?"
        - Maintain a constructive, supportive tone.
        """
        # LLM Behavior Guideline is in the docstring.
        # This method constructs the instruction for the LLM.
        # The LLM should paraphrase the elements, not quote them.

        # Create a summary of current elements for the LLM's context, but instruct it to paraphrase.
        problem_summary = current_value_prop_elements.get("problem", "not yet defined")
        target_user_summary = current_value_prop_elements.get("target_user", "not yet defined")
        solution_summary = current_value_prop_elements.get("solution", "not yet defined")
        benefit_summary = current_value_prop_elements.get("main_benefit", "not yet defined")
        differentiator_summary = current_value_prop_elements.get("differentiator", "not yet defined")
        use_case_summary = current_value_prop_elements.get("use_case", "not yet defined")

        instruction = (
            "Behavioral instruction: Provide critical, constructive feedback on the current value proposition. "
            f"The user has described the problem as: '{problem_summary}'; "
            f"target user as: '{target_user_summary}'; "
            f"solution as: '{solution_summary}'; "
            f"main benefit as: '{benefit_summary}'; "
            f"differentiator as: '{differentiator_summary}'; "
            f"and use case as: '{use_case_summary}'. "
            "In your response, paraphrase these elements. Do not quote them directly. "
            "Identify strengths (e.g., 'I like how your solution seems to address the stated problem, and the use case clearly illustrates its application.'). "
            "Identify areas for improvement or questions (e.g., 'One thing to consider is whether the main benefit is compelling enough for the target user in that specific use case. Have you thought about...?'). "
            "Offer actionable advice (e.g., 'Maybe we could brainstorm ways to quantify the main benefit as experienced in that use case?'). "
            "Maintain a constructive, supportive tone."
        )
        return instruction

    def generate_ideas(self, current_value_prop_elements: dict, user_request: str) -> str:
        """
        Analyzes current input and offers thoughtful, actionable suggestions.

        LLM Behavior Guideline:
        - Review all `current_value_prop_elements`.
        - Identify gaps or areas for development: "Given your focus on [problem] for [target user], have you considered solutions that involve [technology/approach X] or address [related pain point Y]?"
        - Suggest concrete next steps or alternative angles:
            - "If the main benefit is [main_benefit], perhaps a use case focusing on [specific scenario] would highlight that well."
            - "For the solution [solution], an interesting angle could be to integrate [feature/service Z] which might appeal to [target user segment]."
        - Base suggestions on the existing elements to ensure relevance.
        - Avoid generic advice; aim for specific, actionable ideas.
        """
        # LLM Behavior Guideline is in the docstring.
        # This method constructs the instruction for the LLM.
        # The LLM should paraphrase the elements, not quote them.

        problem_summary = current_value_prop_elements.get("problem", "not defined yet")
        target_user_summary = current_value_prop_elements.get("target_user", "not defined yet")
        solution_summary = current_value_prop_elements.get("solution", "not defined yet")
        benefit_summary = current_value_prop_elements.get("main_benefit", "not defined yet")
        differentiator_summary = current_value_prop_elements.get("differentiator", "not defined yet")
        use_case_summary = current_value_prop_elements.get("use_case", "not defined yet")

        instruction = (
            "Behavioral instruction: Generate thoughtful, actionable suggestions based on the current value proposition elements. "
            f"Context: Problem is '{problem_summary}', target user is '{target_user_summary}', solution is '{solution_summary}', main benefit is '{benefit_summary}', differentiator is '{differentiator_summary}', use case is '{use_case_summary}'. "
            "In your response, paraphrase these current elements. Do not quote them directly. "
            "Review these elements and identify gaps or areas for development (e.g., 'Given your focus on the problem for this target user, and the described use case, have you considered solutions that involve...?'). "
            "Suggest concrete next steps or alternative angles (e.g., 'If the main benefit is X, and a primary use case is Y, perhaps exploring [specific feature/aspect] would strengthen the connection.'). "
            "Base suggestions on the existing elements to ensure relevance. Avoid generic advice; aim for specific, actionable ideas. "
            "For example, you could say: 'Thinking about the problem you've described for the target user and the use case, perhaps we could brainstorm specific features for your solution. For instance, if a core issue is [aspect of problem] highlighted in the use case, a feature that [does X] might be valuable. Another idea could be to explore [alternative approach/technology] for that use case. What sparks your interest more?'"
        )
        return instruction
