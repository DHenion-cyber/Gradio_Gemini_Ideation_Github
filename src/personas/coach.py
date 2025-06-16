"""Defines the CoachPersona class, providing conversation style and coaching behavior."""
import re
from llm_utils import query_openai # Updated import

class CoachPersona: # Renamed from BehaviorEngine
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
        system_prompt = "You are a helpful and encouraging assistant. Your task is to acknowledge the user's input by briefly paraphrasing or summarizing its essence in a natural, warm, and conversational way. Avoid direct quotation. Your aim is to make the user feel heard and understood. For example, 'Okay, I'm with you on that...' or 'That's clear, so you're thinking about...'"
        
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
            system_prompt = system_prompt_base + "The user is showing interest. Convey enthusiasm and readiness to keep the momentum going. For example, 'That's great to hear! Sounds like we're on the same page. Ready to explore what's next?'"
        elif stance == "uncertain":
            system_prompt = system_prompt_base + "The user seems uncertain. Offer reassurance and normalize this feeling. For example, 'No problem at all, it's completely normal to feel a bit unsure sometimes. We can take a moment to clarify, or look at it from a different angle – whatever helps!'"
        elif stance == "open":
            system_prompt = system_prompt_base + "The user is open to suggestions. Express appreciation for their openness and willingness to explore. For example, 'That's a fantastic approach! Being open to different ideas is key. What aspects are you most curious to explore first?'"
        elif stance == "decided":
            system_prompt = system_prompt_base + "The user seems to have made a decision. Acknowledge their clarity and indicate readiness to proceed based on their decision. For example, 'Excellent, that's a clear direction. We can definitely build on that. What's the next step in your mind, or would you like a suggestion?'"
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
        system_prompt_base = """You are a helpful assistant. Your goal is to provide a single, concise, and relevant example for the given workflow step to help the user understand the type of input expected for this step. Do not use quotation marks or list multiple examples. The example should be illustrative. The chatbot should only reference general examples (e.g., wait times, overbooking) if the user's input is so vague as to require an example, and even then, provide only one, clearly tied to the user's case. Do not invent unrelated details."""
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

    def paraphrase_user_input(self, user_input: str, stance: str, current_step: str = "the current topic", scratchpad: dict = None, search_results: list = None) -> str: # Added search_results
        """
        Paraphrases the user's input using an LLM, reflecting the detected stance
        and current step, and provides initial context-aware feedback.
        Can optionally use search_results to inform the LLM.
        Now accepts scratchpad for richer context.
        """
        maturity = self.assess_idea_maturity(user_input)
        scratchpad = scratchpad or {}

        system_prompt_base = f"""You are a helpful coaching assistant. Your goal is to help the user develop a strong value proposition. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
The current step is '{current_step}'. The user's input for this step is: '{user_input}'.
The current state of their value proposition development (scratchpad) is: {scratchpad}.
Your response should have two parts:
1. First, acknowledge and briefly paraphrase the user's input for '{current_step}'. Do not use direct quotation. Refer to their input conceptually, for example, as 'your idea about {current_step} being {user_input[:30]}...' or 'your thoughts on {current_step} focusing on [paraphrased essence]'.
2. Second, provide brief, context-aware feedback based on their input's specificity and its relevance to the '{current_step}', potentially drawing context from the scratchpad.
"""
        if search_results:
            system_prompt_base += f"\nRelevant search results for context: {search_results}\n"

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

    def coach_on_decision(self, current_step: str, user_input: str, scratchpad: dict = None, stance: str = "decided", search_results: list = None) -> str: # Added search_results
        """
        Coaches the user after they've made a decision, using an LLM,
        referencing their specific input and explaining the 'why' of feedback.
        Can optionally use search_results to inform the LLM.
        Now accepts scratchpad and an explicit stance.
        """
        maturity = self.assess_idea_maturity(user_input)
        scratchpad = scratchpad or {}
        
        system_prompt_base = f"""You are a helpful coaching assistant. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
The user has made a decision for the '{current_step}' (stance: {stance}). Their input was conceptually about '{user_input}'.
The current state of their value proposition development (scratchpad) is: {scratchpad}.
Your task is to provide feedback. DO NOT quote the user's input '{user_input}' directly. Instead, refer to it as 'your decision about {current_step}', 'your idea of {user_input[:30]}...', or 'your focus on [paraphrased essence of user_input]'. Explain *why* your feedback or suggestions are helpful for them to build a strong value proposition.
"""
        if search_results:
            system_prompt_base += f"\nRelevant search results for context: {search_results}\n"

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

        system_prompt = f"""You are a helpful coaching assistant. Your goal is to provide critical, constructive feedback on the user's current value proposition elements to help them build a strong and compelling one. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
When referring to the user's input for each element (problem, target user, solution, etc.), paraphrase it conceptually (e.g., 'Regarding the problem you've identified as affecting X...' or 'Your proposed solution involving Y...'). Do not quote their input directly. Avoid generic terms like 'the problem' and instead refer to 'the problem you described concerning Z'.
Your feedback should:
1. Identify specific strengths, connecting them to how they contribute to a strong value proposition (e.g., 'The way you've defined the target user as [paraphrased user input] is strong because it allows for highly focused messaging.').
2. Pinpoint specific areas for improvement or further questions. For each, explain *why* addressing this point would strengthen their value proposition (e.g., 'Considering your solution idea of [paraphrased user input], have you thought about how it directly addresses the core pain point of [paraphrased problem]? Clarifying this link will make the benefit more obvious.').
3. Offer concrete, actionable advice. Explain how this advice helps them achieve a better value proposition (e.g., 'To make the benefit of [paraphrased benefit] more impactful, perhaps we could brainstorm ways to quantify it. This helps demonstrate clear value to your target user of [paraphrased target user].').
Maintain a constructive, supportive tone throughout.
"""
        
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

        system_prompt = f"""You are a helpful coaching assistant. Your goal is to generate thoughtful, actionable suggestions based on the user's current value proposition elements, helping them to strengthen it. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
When referring to the user's input for each element, paraphrase it conceptually (e.g., 'Given your focus on the problem of [paraphrased problem] for the target user you described as [paraphrased target user]...'). Do not quote their input directly. Avoid generic terms like 'the solution' and instead refer to 'your solution idea concerning X'.
Your suggestions should:
1. Be directly based on their existing elements to ensure relevance.
2. Identify potential gaps or areas for further development, explaining *why* exploring these could be beneficial (e.g., 'Considering the problem of [paraphrased problem] and your solution idea of [paraphrased solution], exploring how [specific aspect] could address an unmet need for your [paraphrased target user] might make your differentiator clearer.').
3. Suggest concrete next steps or alternative angles. For each suggestion, explain *how* it could help them build a more compelling value proposition (e.g., 'If the main benefit you're aiming for is [paraphrased benefit], and a primary use case involves [paraphrased use case], perhaps exploring [specific feature/aspect] would strengthen that connection by making the benefit more tangible in that scenario. This could make your idea more persuasive.').
Aim for specific, actionable ideas, not generic advice. Frame suggestions as collaborative exploration.
"""
        
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

    def get_intake_to_ideation_transition_message(self) -> str:
        """
        Returns the introductory message for transitioning from intake to ideation.
        """
        return (
            "Thanks for sharing! I'll help you develop and vet your ideas now. "
            "I will continue to ask you questions, but you're welcome to ask me for ideas, analysis, or feedback at any point."
        )

    def get_step_intro_message(self, current_step: str, scratchpad: dict) -> str:
        """
        Returns a step-specific introduction message if appropriate, otherwise empty string.
        """
        if current_step == "differentiator" and \
           scratchpad.get("main_benefit") and \
           not scratchpad.get("differentiator"):
            return (
                "Let's define what makes your solution unique. "
                "This helps clarify your competitive advantage and will later help to position your idea effectively.\n"
                "What specific aspects set your solution apart from alternatives?"
            )
        elif current_step == "use_case" and \
             scratchpad.get("differentiator") and \
             not scratchpad.get("use_case"):
            return (
                "Now let's think about specific use cases. "
                "How do you envision people using your solution in real-world scenarios?"
            )
        return ""

    def get_prompt_for_empty_input(self, current_step: str) -> str:
        """
        Returns a prompt when the user provides empty input for a step that needs it.
        """
        step_display_name = current_step.replace("_", " ")
        article = "an" if step_display_name.lower().startswith(("a", "e", "i", "o", "u")) else "a"
        return (
            f"It seems we're working on defining {article} {step_display_name}, "
            f"but I didn't receive your input for it. Could you please share your thoughts on the {step_display_name}?"
        )

    def get_reflection_prompt(self) -> str:
        """
        Returns a standard reflection prompt to append to responses.
        """
        return "\n\nWhat do you think? Would you like to explore this direction, or focus on another aspect?"

    def generate_value_prop_summary(self, scratchpad: dict) -> str:
        """
        Generates a structured summary string with a main paragraph, use cases, and recommendations
        based on the provided scratchpad. This method formats the data and does not call an LLM.
        """
        problem_desc = scratchpad.get('problem')
        target_user_desc = scratchpad.get('target_customer')
        solution_desc = scratchpad.get('solution')
        benefit_desc = scratchpad.get('main_benefit')
        differentiator_desc = scratchpad.get('differentiator')
        use_case_desc = scratchpad.get('use_case')
        research_requests = scratchpad.get("research_requests", [])

        summary_parts = []

        # 1. Main Summary Paragraph
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
            summary_parts.append(f"\n\n**Use Case(s):**\n{use_case_desc}")
        else:
            summary_parts.append("\n\n**Use Case(s):**\nNot yet defined.")

        # 3. Actionable Recommendations Section (formerly actionable_recommendations method)
        recs_text_parts = []
        if research_requests:
            for req in research_requests:
                if isinstance(req, dict):
                    recs_text_parts.append(f"It's recommended to research the {req.get('step', 'relevant area')} further, focusing on: {req.get('details', 'specific aspects not yet defined')}.")
                elif isinstance(req, str):
                    recs_text_parts.append(f"Further research is suggested for: {req}.")
                else:
                    recs_text_parts.append("Additional research may be beneficial.")
        
        if recs_text_parts:
            recommendations_text = "\n".join(recs_text_parts)
            summary_parts.append(f"\n\n**Actionable Recommendations:**\n{recommendations_text}")
        
        return "".join(summary_parts).strip()

    def generate_short_summary(self, text: str) -> str:
        """
        Sends text to OpenAI to create a short (<=100-token) summary.
        """
        summary_prompt = f"Summarize the following text in 100 tokens or less:\n\n{text}"
        # Use a slightly lower temperature for summarization to get more concise results
        # query_openai is available via from ..llm_utils import query_openai
        summary = query_openai(messages=[{"role": "user", "content": summary_prompt}], temperature=0.5, max_tokens=100)
        return summary

    def propose_next_conversation_turn(self, intake_answers: list, scratchpad: dict, phase: str, conversation_history: list = None) -> str:
        """
        Uses the LLM to propose the next natural conversation turn based on intake, scratchpad, phase, and conversation history.
        Aims for peer coaching, brainstorming, and conversational EQ.
        """
        # client is available via from ..llm_utils import client
        system_prompt_content = """You are a peer coach brainstorming new digital health innovations with the user. You help them surface promising business ideas by building on any aspect of their prior answers that shows potential, creativity, or relevance.

You are not a therapist, but you are very emotionally intelligent and always bring conversational energy and warmth.

Never just repeat the user’s last answer. Always move the conversation forward, build excitement, and keep things open-ended.

If the user says ‘no’, ‘I don’t know’, or gives a one-word answer, gently prompt them to revisit an earlier idea, suggest a new direction, or validate that it’s normal to feel stuck.

Example interaction:
User: I care about cost savings and rapid deployment.
Assistant: Love it—so quick wins and low friction matter. We could brainstorm ideas for settings where speed makes a huge difference, or dive into ways to get to value quickly. Want to riff on those, or is there another angle you’re curious about?"""

        user_prompt_parts = []
        user_prompt_parts.append(f"Current Conversation Phase: {phase}")

        if intake_answers:
            user_prompt_parts.append("\n--- Intake Answers ---")
            for answer_item in intake_answers:
                if isinstance(answer_item, dict) and 'text' in answer_item and answer_item['text']:
                    user_prompt_parts.append(f"- {answer_item['text']}")
                elif isinstance(answer_item, str) and answer_item:
                    user_prompt_parts.append(f"- {answer_item}")
            user_prompt_parts.append("----------------------")

        if scratchpad and any(scratchpad.values()):
            user_prompt_parts.append("\n--- Current Scratchpad ---")
            for key, value in scratchpad.items():
                if value:
                    user_prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            user_prompt_parts.append("--------------------------")

        if conversation_history:
            user_prompt_parts.append("\n--- Recent Conversation History (last 3 turns) ---")
            for turn in conversation_history[-3:]:
                role = turn.get('role', 'unknown').title()
                text = turn.get('text', '')
                if text:
                    user_prompt_parts.append(f"{role}: {text}")
            user_prompt_parts.append("----------------------------------------------------")


        user_prompt_parts.append("\n--- Your Task ---")
        user_prompt_parts.append("""Based on all the information above (intake, scratchpad, phase, and recent history):
1. Scan all intake responses and scratchpad fields.
2. Identify 2–3 elements with the most potential, novelty, or relevance to valuable business ideas (considering excitement, user impact, originality, etc.).
3. Briefly express enthusiasm about 1–2 of these elements (e.g., "I love how you mentioned X…" or "It’s cool that you’re interested in Y…").
4. Ask the user if they want to brainstorm more about any of these identified elements, OR suggest a related angle.
5. If previous responses were bland, “no”, or unclear, gently pivot with curiosity, encouragement, or by surfacing something previously mentioned.
6. Never repeat the same phrase or get stuck on a single answer. Never just restate a prior user reply as a question.
7. Always keep the conversation moving naturally, with a friendly, peer-like tone, using mild humor and warmth when appropriate.

--- Example Scenarios ---

Scenario 1: Surfacing multiple elements, peer excitement
Context:
  Intake: "I'm passionate about mental wellness for students." "I think technology can make support more accessible." "Maybe something with AI."
  Scratchpad: Problem_Statement: "Students lack accessible mental wellness resources."
Your Output: "This is great! I'm really picking up on your passion for student mental wellness and the idea of using tech, especially AI, to make support more accessible. That's a super relevant area. Would you like to brainstorm some specific ways AI could play a role here, or perhaps explore different student populations that might see the main benefit most?"

Scenario 2: Handling "no" gracefully, suggesting new angle
Context:
  Recent History:
    Assistant: "...Want to explore AI for personalized coaching or for early detection?"
    User: "No."
Your Output: "No worries at all! Sometimes an idea just doesn't click. How about we pivot a bit? You also mentioned making support 'more accessible' earlier (from intake/scratchpad). That's a big one. We could think about what 'accessible' really means – is it about cost, time, overcoming stigma, or something else? Or, is there another aspect of student mental wellness that's on your mind?"

Scenario 3: Handling bland reply ("Dunno"), encouraging revisit
Context:
  Recent History:
    Assistant: "...Interested in brainstorming around gamification for engagement, or focusing on data privacy?"
    User: "Dunno."
  Intake/Scratchpad contains: "User mentioned unique pressures faced by graduate students."
Your Output: "Hey, it's totally fine to feel a bit unsure – sometimes the best ideas take a little while to surface! You know, earlier you had a really interesting thought about the unique pressures faced by graduate students. Maybe we could circle back to that for a moment? Or, if you're feeling like a completely fresh angle, we can totally do that too!"

--- Now, generate your response for the current user based on their information. ---
What is your proposed next conversational turn?
""")

        full_user_prompt = "\n".join(user_prompt_parts)

        # query_openai is available via from ..llm_utils import query_openai
        # client is also available from llm_utils if direct client call is preferred
        response = query_openai(
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": full_user_prompt}
            ],
            temperature=0.75,
            max_tokens=250
        )
        return response # query_openai already strips
    # TODO: add behavior methods (paraphrase, feedback, etc.) - These seem to be well covered above.