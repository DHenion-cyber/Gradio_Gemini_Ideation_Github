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
You are a helpful assistant. Offer a single, concise, relevant example for the given workflow step. Do not use quotation marks or list multiple examples. The example should be illustrative and help the user understand the type of input expected for this step. The chatbot should only reference general examples (e.g., wait times, overbooking) if the user's input is so vague as to require an example, and even then, provide only one, clearly tied to the user's case. Do not invent unrelated details.
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
        and current step, and provides initial context-aware feedback.
        """
        maturity = self.assess_idea_maturity(user_input)

        system_prompt_base = (
You are a helpful coaching assistant. Your goal is to help the user develop a strong value proposition. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
The current step is '{current_step}'. The user's input for this step is: '{user_input}'.
Your response should have two parts:
1. First, acknowledge and briefly paraphrase the user's input for '{current_step}'. Do not use direct quotation. Refer to their input conceptually, for example, as 'your idea about {current_step} being {user_input[:30]}...' or 'your thoughts on {current_step} focusing on [paraphrased essence]'.
2. Second, provide brief, context-aware feedback based on their input's specificity and its relevance to the '{current_step}'.
        )

        if maturity == "novice":
            system_prompt_base += (
                f"The user's input '{user_input}' for '{current_step}' seems a bit general. "
                f"In your feedback part, explain briefly why more detail for '{current_step}' (related to their idea of '{user_input}') would be beneficial for building a compelling value proposition. For example: 'Getting more specific about your idea of \"{user_input[:30]}...\" for {current_step} can help us pinpoint exactly who it's for and what unique value it offers, which is key to a strong value proposition.'\n"
            )
        else: # advanced
            system_prompt_base += (
                f"The user's input '{user_input}' for '{current_step}' is quite specific. "
                f"In your feedback part, affirm this (e.g., 'That's a clear and specific direction for {current_step}.'). "
                f"You might also briefly note how this specificity is helpful (e.g., 'This level of detail regarding \"{user_input[:30]}...\" is great for ensuring {current_step} strongly supports the overall value proposition.').\n"
            )

        # Stance-specific additions to the prompt (these will guide the *tone* and *framing* of the two-part response)
        if stance == "decided":
            system_prompt = system_prompt_base + f"Frame your two-part response (paraphrase + feedback) with confidence, acknowledging their clear direction regarding '{user_input[:30]}...' for {current_step}."
        elif stance == "uncertain":
            system_prompt = system_prompt_base + f"Frame your two-part response gently, acknowledging they are exploring ideas like '{user_input[:30]}...' for {current_step}."
        elif stance == "open":
            system_prompt = system_prompt_base + f"Frame your two-part response encouragingly, noting their openness to exploring ideas like '{user_input[:30]}...' for {current_step}."
        elif stance == "interest":
            system_prompt = system_prompt_base + f"Frame your two-part response positively, reflecting their interest in ideas like '{user_input[:30]}...' for {current_step}."
        else: # neutral or other
            system_prompt = system_prompt_base + f"Frame your two-part response with clear acknowledgement of their input '{user_input[:30]}...' for {current_step}."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please provide your coaching paraphrase and initial feedback."}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=150, temperature=0.7) # Increased tokens
            return response
        except Exception as e:
            print(f"Error in paraphrase_user_input LLM call: {e}")
            # Fallback that still tries to reference the input
            if user_input:
                 return f"I've noted your thoughts on {current_step}: '{user_input[:50]}...'. Let's consider how to refine this."
            return f"I'm processing your thoughts on {current_step}."

    def coach_on_decision(self, current_step: str, user_input: str) -> str:
        """
        Coaches the user after they've made a decision, using an LLM,
        referencing their specific input and explaining the 'why' of feedback.
        """
        maturity = self.assess_idea_maturity(user_input)
        
        system_prompt_base = (
You are a helpful coaching assistant. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
The user has made a decision for the '{current_step}'. Their input was conceptually about '{user_input}'. Your task is to provide feedback. DO NOT quote the user's input '{user_input}' directly. Instead, refer to it as 'your decision about {current_step}', 'your idea of {user_input[:30]}...', or 'your focus on [paraphrased essence of user_input]'. Explain *why* your feedback or suggestions are helpful for them to build a strong value proposition.
        )

        if maturity == "novice":
            system_prompt = system_prompt_base + (
                f"The user's decision for '{current_step}', which is along the lines of '{user_input}', seems like a good starting point but could be more specific. "
                f"Explain that getting more specific about '{user_input}' for '{current_step}' can significantly strengthen their value proposition by, for example, making it easier to identify a precise target audience, tailor the solution, or articulate a unique benefit. "
                f"Offer a concrete suggestion for how they could refine their idea '{user_input}'. For example, if '{current_step}' is 'problem' and they said 'communication issues', you might suggest: 'For instance, with 'communication issues', could you pinpoint what kind of communication, for whom, and what the direct negative impact is? This helps ensure the solution is highly relevant.' "
                f"Then, ask if they'd like to refine their current idea about '{user_input}' to be more specific, or if they prefer to stick with it for now. You could also offer to brainstorm specific examples related to '{user_input}'."
            )
        else:  # "advanced"
            system_prompt = system_prompt_base + (
                f"The user's input for '{current_step}', which is '{user_input}', is quite specific and clear. "
                f"Affirm this (e.g., 'Your decision to focus on {user_input[:30]}... for {current_step} is very clear and specific.'). "
                f"Explain briefly why this level of specificity is valuable (e.g., 'This kind of detail for {current_step} is excellent because it allows for a more targeted approach to [next step/overall value prop element], making your overall value proposition more compelling.'). "
                f"Then, invite them to elaborate on the reasoning or experience that led them to '{user_input}' (e.g., 'Could you share a bit more about what brought you to this specific idea for {current_step}? Understanding your perspective can help us build on it effectively.'). "
                f"You could also ask if they see any potential challenges or refinements related to '{user_input}', or if they're ready to connect this to the next part of their value proposition."
            )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please provide your coaching feedback on my decision."}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=180, temperature=0.7) # Increased tokens
            return response
        except Exception as e:
            print(f"Error in coach_on_decision LLM call: {e}")
            # Fallback that still tries to reference the input
            if user_input:
                return f"That's an interesting decision for {current_step} regarding '{user_input[:50]}...'. What's your reasoning behind it?"
            return f"That's an interesting decision for {current_step}. What's your reasoning behind it?"

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
You are a helpful coaching assistant. Your goal is to provide critical, constructive feedback on the user's current value proposition elements to help them build a strong and compelling one. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
When referring to the user's input for each element (problem, target user, solution, etc.), paraphrase it conceptually (e.g., 'Regarding the problem you've identified as affecting X...' or 'Your proposed solution involving Y...'). Do not quote their input directly. Avoid generic terms like 'the problem' and instead refer to 'the problem you described concerning Z'.
Your feedback should:
1. Identify specific strengths, connecting them to how they contribute to a strong value proposition (e.g., 'The way you've defined the target user as [paraphrased user input] is strong because it allows for highly focused messaging.').
2. Pinpoint specific areas for improvement or further questions. For each, explain *why* addressing this point would strengthen their value proposition (e.g., 'Considering your solution idea of [paraphrased user input], have you thought about how it directly addresses the core pain point of [paraphrased problem]? Clarifying this link will make the benefit more obvious.').
3. Offer concrete, actionable advice. Explain how this advice helps them achieve a better value proposition (e.g., 'To make the benefit of [paraphrased benefit] more impactful, perhaps we could brainstorm ways to quantify it. This helps demonstrate clear value to your target user of [paraphrased target user].').
Maintain a constructive, supportive tone throughout.
        )
        
        user_prompt_for_llm = (
            f"Here's the current value proposition for feedback, based on my request '{user_request}':\n"
            f"- Problem: {problem_summary}\n"
            f"- Target User: {target_user_summary}\n"
            f"- Solution: {solution_summary}\n"
            f"- Main Benefit: {benefit_summary}\n"
            f"- Differentiator: {differentiator_summary}\n"
            f"- Use Case: {use_case_summary}\n"
            "Please provide your detailed, constructive feedback, explaining the 'why' behind your points."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=250, temperature=0.7) # Increased max_tokens
            return response
        except Exception as e:
            print(f"Error in provide_feedback LLM call: {e}")
            return "That's an interesting set of ideas. Let's think about how they fit together and how we can make them even stronger." # Fallback

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
You are a helpful coaching assistant. Your goal is to generate thoughtful, actionable suggestions based on the user's current value proposition elements, helping them to strengthen it. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
When referring to the user's input for each element, paraphrase it conceptually (e.g., 'Given your focus on the problem of [paraphrased problem] for the target user you described as [paraphrased target user]...'). Do not quote their input directly. Avoid generic terms like 'the solution' and instead refer to 'your solution idea concerning X'.
Your suggestions should:
1. Be directly based on their existing elements to ensure relevance.
2. Identify potential gaps or areas for further development, explaining *why* exploring these could be beneficial (e.g., 'Considering the problem of [paraphrased problem] and your solution idea of [paraphrased solution], exploring how [specific aspect] could address an unmet need for your [paraphrased target user] might make your differentiator clearer.').
3. Suggest concrete next steps or alternative angles. For each suggestion, explain *how* it could help them build a more compelling value proposition (e.g., 'If the main benefit you're aiming for is [paraphrased benefit], and a primary use case involves [paraphrased use case], perhaps exploring [specific feature/aspect] would strengthen that connection by making the benefit more tangible in that scenario. This could make your idea more persuasive.').
Aim for specific, actionable ideas, not generic advice. Frame suggestions as collaborative exploration.
        )
        
        user_prompt_for_llm = (
            f"Based on my request '{user_request}' and the current value proposition:\n"
            f"- Problem: {problem_summary}\n"
            f"- Target User: {target_user_summary}\n"
            f"- Solution: {solution_summary}\n"
            f"- Main Benefit: {benefit_summary}\n"
            f"- Differentiator: {differentiator_summary}\n"
            f"- Use Case: {use_case_summary}\n"
            "Please generate some ideas or suggestions, explaining how they could help improve my value proposition."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=280, temperature=0.75) # Increased max_tokens
            return response
        except Exception as e:
            print(f"Error in generate_ideas LLM call: {e}")
            return "Let's brainstorm some possibilities for your idea and see how we can enhance it." # Fallback
