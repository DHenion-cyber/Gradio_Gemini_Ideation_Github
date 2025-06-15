# src/coach_persona.py

import re
from .llm_utils import query_openai # Import query_openai

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
        Generates a brief active listening statement using an LLM.
        """
        system_prompt = "You are a helpful assistant. Your task is to acknowledge the user's input by paraphrasing or summarizing its essence naturally and conversationally. Avoid direct quotation of the user's input. For example, 'Okay, I understand you're saying...' or 'Got it, so the main point is...'"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=50, temperature=0.7)
            return response
        except Exception as e:
            # Log the error e.g., using logging.error(f"Error in active_listening: {e}")
            print(f"Error in active_listening LLM call: {e}") # Basic error printing
            return "I've noted that." # Fallback response

    def diplomatic_acknowledgement(self, stance: str, user_input: str = "") -> str:
        """
        Generates a diplomatic statement based on detected stance using an LLM.
        """
        system_prompt_base = "You are a helpful assistant. Based on the user's stance, provide an appropriate diplomatic acknowledgement. "
        user_context = f"The user's stance is '{stance}'."
        if user_input:
            user_context += f" Their input was: '{user_input}'"

        if stance == "interest":
            system_prompt = system_prompt_base + "The user is showing interest. Convey enthusiasm and readiness to keep the momentum going. For example, 'Great—got it. Let's keep the momentum going.'"
        elif stance == "uncertain":
            system_prompt = system_prompt_base + "The user seems uncertain. Offer reassurance and normalize this feeling. For example, 'No worries, it's normal to feel uncertain at this stage.'"
        elif stance == "open":
            system_prompt = system_prompt_base + "The user is open to suggestions. Express appreciation for their openness and willingness to explore. For example, 'Love that openness. Let's explore together.'"
        elif stance == "decided":
            system_prompt = system_prompt_base + "The user seems to have made a decision. Acknowledge their clarity and indicate readiness to proceed based on their decision. For example, 'Sounds like you know what you want. We'll move forward on that.'"
        else: # neutral
            system_prompt = system_prompt_base + "Offer a neutral, encouraging acknowledgement of the user's input."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_context} # Provide context for the LLM
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=60, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error in diplomatic_acknowledgement LLM call: {e}")
            return "Understood." # Fallback response

    def offer_example(self, step: str) -> str:
        """
        Generates a generic example for a workflow step using an LLM.
        """
        system_prompt_base = "You are a helpful assistant. Offer a single, concise, relevant example for the given workflow step. Do not use quotation marks or list multiple examples. The example should be illustrative and help the user understand the type of input expected for this step. "
        user_prompt = f"The current workflow step is '{step}'. Please provide an example for this step."

        if step == "problem":
            system_prompt = system_prompt_base + "For the 'problem' step, you could describe a common issue like patients missing appointments due to overlooked reminders."
        elif step == "target_user": # Corrected from target_customer to target_user to match other uses
            system_prompt = system_prompt_base + "For the 'target_user' step, you could mention a specific group like radiology schedulers who often get overloaded with manual calls."
        elif step == "solution":
            system_prompt = system_prompt_base + "For the 'solution' step, you could suggest a tool like a chatbot to automate appointment scheduling."
        elif step == "main_benefit":
            system_prompt = system_prompt_base + "For the 'main_benefit' step, you could state a quantifiable outcome like achieving 10% fewer no-shows."
        elif step == "differentiator":
            system_prompt = system_prompt_base + "For the 'differentiator' step, you could mention a unique feature like AI-powered personalization that sets the solution apart."
        elif step == "use_case":
            system_prompt = system_prompt_base + "For the 'use_case' step, you could describe a scenario like a busy professional using the solution to quickly find healthy meal options during their lunch break."
        else:
            system_prompt = system_prompt_base + "Offer a single, concise, relevant example appropriate for the current context, without using quotes."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=70, temperature=0.5)
            return response
        except Exception as e:
            print(f"Error in offer_example LLM call: {e}")
            return f"For example, for the {step}, you might consider..." # Fallback

    def offer_strategic_suggestion(self, step: str) -> str:
        """
        Generates a generic suggestion related to the workflow step using an LLM.
        """
        system_prompt_base = "You are a helpful assistant. Offer a strategic suggestion to help the user clarify or advance the current workflow step. The suggestion should be a question or a gentle prompt, not a direct command. Avoid quoting examples within the suggestion. "
        user_prompt = f"The current workflow step is '{step}'. Please provide a strategic suggestion for this step."

        if step == "problem":
            system_prompt = system_prompt_base + "For the 'problem' step, you could prompt them to consider who is most affected and when, or ask if clarifying that would be helpful."
        elif step == "target_user": # Corrected from target_customer
            system_prompt = system_prompt_base + "For the 'target_user' step, you could suggest considering narrowing to one patient group for sharper impact."
        elif step == "solution":
            system_prompt = system_prompt_base + "For the 'solution' step, you could ask what if they started with a pilot in a single clinic."
        elif step == "main_benefit":
            system_prompt = system_prompt_base + "For the 'main_benefit' step, you could mention that measurable outcomes help and ask if they want ideas for tracking."
        elif step == "differentiator":
            system_prompt = system_prompt_base + "For the 'differentiator' step, you could ask if they've considered how their solution addresses unmet needs better than existing alternatives."
        elif step == "use_case":
            system_prompt = system_prompt_base + "For the 'use_case' step, you could ask if they've considered how different user segments might have distinct primary use cases for the solution, or if detailing a specific scenario would help clarify its value."
        else:
            system_prompt = system_prompt_base + "Offer a helpful, strategic suggestion relevant to the current step, framed as a question or gentle prompt."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=80, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error in offer_strategic_suggestion LLM call: {e}")
            return f"Have you considered how to best approach the {step}?" # Fallback

    def paraphrase_user_input(self, user_input: str, stance: str, current_step: str = "the current topic") -> str:
        """
        Paraphrases the user's input using an LLM, reflecting the detected stance
        and current step.
        """
        system_prompt_base = f"You are a helpful assistant. Paraphrase the user's input naturally and conversationally, without direct quotation. Rephrase the essence of their statement regarding '{current_step}'. "
        
        if stance == "decided":
            system_prompt = system_prompt_base + f"The user seems to have a clear direction for {current_step}. You could say something like: 'So, you're thinking [paraphrase of user's idea] for the {current_step}. That's a clear direction.' or 'Okay, so your focus for {current_step} is on [paraphrase of user's idea].'"
        elif stance == "uncertain":
            system_prompt = system_prompt_base + f"The user sounds like they're still exploring or unsure about {current_step}. You could say something like: 'It sounds like you're still exploring [paraphrase of user's uncertainty] regarding the {current_step}.' or 'Okay, so you're working through your thoughts on [paraphrase of user's idea] for {current_step}.'"
        elif stance == "open":
            system_prompt = system_prompt_base + f"The user seems open to considering different angles for {current_step}. You could say something like: 'You're open to considering different angles for [paraphrase of user's openness] for the {current_step}, that's great.' or 'Okay, so you're looking at options around [paraphrase of user's idea] for {current_step}.'"
        elif stance == "interest":
            system_prompt = system_prompt_base + f"The user has expressed interest in {current_step}. You could say something like: 'You've expressed interest in [paraphrase of user's interest] for the {current_step}.' or 'Got it, you're interested in [paraphrase of user's idea] for {current_step}.'"
        else: # neutral or other
            system_prompt = system_prompt_base + f"Acknowledge their input clearly regarding {current_step}. You could say something like: 'Okay, I understand you're saying [paraphrase of user's input] regarding the {current_step}.' or 'Understood, your point about {current_step} is [paraphrase of user's input].'"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=80, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error in paraphrase_user_input LLM call: {e}")
            return f"I'm processing your thoughts on {current_step}." # Fallback

    def coach_on_decision(self, current_step: str, user_input: str) -> str:
        """
        Coaches the user after they've made a decision, using an LLM.
        """
        maturity = self.assess_idea_maturity(user_input)
        system_prompt_base = f"You are a helpful coaching assistant. The user has made a decision for the '{current_step}'. Their input was: '{user_input}'. Do not directly quote their original input in your response; refer to it as 'your idea for the {current_step}' or similar. "

        if maturity == "novice":
            system_prompt = system_prompt_base + (
                "Their input seems like a good starting point but could be more specific. "
                "Explain the value of specificity (e.g., 'Often, getting more specific can make the idea stronger...'). "
                "Suggest they refine it by offering an example of how to be more specific in this context "
                "(e.g., 'For example, instead of a general group, could we identify a specific user segment? Or for a solution, a key starting feature?'). "
                "Then, ask if they'd like to refine their idea to be more specific, perhaps suggesting one or two hypothetical alternatives, or if they prefer to stick with their current thought."
            )
        else:  # "advanced"
            system_prompt = system_prompt_base + (
                "Their input is quite specific and clear. "
                "Affirm this briefly (e.g., 'That's a very specific and clear direction.'). "
                "Then, invite them to share more about their reasoning or the experience behind their choice (e.g., 'Could you tell me a bit more about what led you to this particular idea?'). "
                "You might also gently offer to explore alternatives if it seems appropriate, to ensure this is the most impactful path (e.g., 'Are there any alternative approaches you considered, or do you feel confident this is the one to pursue?'), "
                "or simply ask if they are ready to move to the next step."
            )
        
        # User prompt can be simple, as the main context is in the system prompt
        user_prompt_for_llm = f"Considering my decision for {current_step}, what are your thoughts or next questions?"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=150, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error in coach_on_decision LLM call: {e}")
            return f"That's an interesting decision for {current_step}. What's your reasoning behind it?" # Fallback

    def provide_feedback(self, current_value_prop_elements: dict, user_request: str) -> str:
        """
        Provides critical, constructive feedback on the current value proposition elements using an LLM.
        """
        problem_summary = current_value_prop_elements.get("problem", "not yet defined")
        target_user_summary = current_value_prop_elements.get("target_user", "not yet defined") # Corrected key
        solution_summary = current_value_prop_elements.get("solution", "not yet defined")
        benefit_summary = current_value_prop_elements.get("main_benefit", "not yet defined") # Corrected key
        differentiator_summary = current_value_prop_elements.get("differentiator", "not yet defined")
        use_case_summary = current_value_prop_elements.get("use_case", "not yet defined")

        system_prompt = (
            "You are a helpful coaching assistant. Provide critical, constructive feedback on the current value proposition. "
            "In your response, paraphrase the elements provided by the user. Do not quote them directly. "
            "Identify strengths (e.g., 'I like how your solution seems to address the stated problem, and the use case clearly illustrates its application.'). "
            "Identify areas for improvement or questions (e.g., 'One thing to consider is whether the main benefit is compelling enough for the target user in that specific use case. Have you thought about...?'). "
            "Offer actionable advice (e.g., 'Maybe we could brainstorm ways to quantify the main benefit as experienced in that use case?'). "
            "Maintain a constructive, supportive tone."
        )
        
        user_prompt_for_llm = (
            f"Here's the current value proposition for feedback, based on my request '{user_request}':\n"
            f"- Problem: {problem_summary}\n"
            f"- Target User: {target_user_summary}\n"
            f"- Solution: {solution_summary}\n"
            f"- Main Benefit: {benefit_summary}\n"
            f"- Differentiator: {differentiator_summary}\n"
            f"- Use Case: {use_case_summary}\n"
            "Please provide your feedback."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=200, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error in provide_feedback LLM call: {e}")
            return "That's an interesting set of ideas. Let's think about how they fit together." # Fallback

    def generate_ideas(self, current_value_prop_elements: dict, user_request: str) -> str:
        """
        Analyzes current input and offers thoughtful, actionable suggestions using an LLM.
        """
        problem_summary = current_value_prop_elements.get("problem", "not defined yet")
        target_user_summary = current_value_prop_elements.get("target_user", "not defined yet") # Corrected key
        solution_summary = current_value_prop_elements.get("solution", "not defined yet")
        benefit_summary = current_value_prop_elements.get("main_benefit", "not defined yet") # Corrected key
        differentiator_summary = current_value_prop_elements.get("differentiator", "not defined yet")
        use_case_summary = current_value_prop_elements.get("use_case", "not defined yet")

        system_prompt = (
            "You are a helpful coaching assistant. Generate thoughtful, actionable suggestions based on the current value proposition elements. "
            "In your response, paraphrase these current elements. Do not quote them directly. "
            "Review these elements and identify gaps or areas for development (e.g., 'Given your focus on the problem for this target user, and the described use case, have you considered solutions that involve...?'). "
            "Suggest concrete next steps or alternative angles (e.g., 'If the main benefit is X, and a primary use case is Y, perhaps exploring [specific feature/aspect] would strengthen the connection.'). "
            "Base suggestions on the existing elements to ensure relevance. Avoid generic advice; aim for specific, actionable ideas. "
            "For example, you could say: 'Thinking about the problem you've described for the target user and the use case, perhaps we could brainstorm specific features for your solution. For instance, if a core issue is [aspect of problem] highlighted in the use case, a feature that [does X] might be valuable. Another idea could be to explore [alternative approach/technology] for that use case. What sparks your interest more?'"
        )
        
        user_prompt_for_llm = (
            f"Based on my request '{user_request}' and the current value proposition:\n"
            f"- Problem: {problem_summary}\n"
            f"- Target User: {target_user_summary}\n"
            f"- Solution: {solution_summary}\n"
            f"- Main Benefit: {benefit_summary}\n"
            f"- Differentiator: {differentiator_summary}\n"
            f"- Use Case: {use_case_summary}\n"
            "Please generate some ideas or suggestions."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=250, temperature=0.75) # Increased max_tokens for idea generation
            return response
        except Exception as e:
            print(f"Error in generate_ideas LLM call: {e}")
            return "Let's brainstorm some possibilities for your idea." # Fallback
