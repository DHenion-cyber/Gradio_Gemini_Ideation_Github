"""
Defines the CoachPersona class, providing an enhanced conversation style and coaching behavior.

Core Enhancements Summary (June 2025):
- Single Question Focus: Chatbot asks at most one question per turn.
- Strongest Element Prioritization: Identifies and focuses on the most developed, unvetted idea.
- Contextual Recap: Briefly recaps relevant user-provided details before new questions.
- Nuanced Input Assessment: Rates input depth/clarity on a sliding scale (vague, developing, specific, expert-level) instead of binary novice/advanced. Adapts support accordingly.
- Flexible User Cue Detection: Identifies "open," "decided," "uncertain," or "curious" user cues.
- Collaborative Ideation: Offers users a chance to approve, revise, or suggest alternatives for chatbot-led suggestions.
- User Request Prioritization: (Assumed to be handled by ConversationManager) Always prioritizes direct user requests.
- Reflective Summaries: Periodically provides "Here’s where we are..." summaries for user validation.
- Micro-validation: Affirms user effort on complex/detailed answers.
- Transparent Next Steps: Communicates the next planned step to the user.
- Permission-Based Tips: Asks for permission before offering unsolicited tips/examples.
"""
import re
import logging # Added import
from src.llm_utils import query_openai # Updated import

class CoachPersona: # Renamed from BehaviorEngine
    """
    Provides reusable, topic-agnostic behaviors and utilities for chatbot conversation,
    embodying an enhanced coaching persona.
    """

    def assess_input_clarity_depth(self, user_input: str) -> str:
        """
        Assesses the depth and clarity of the user's input on a sliding scale.
        Returns "vague", "developing", "specific", or "expert-level".
        """
        input_lower = user_input.lower()
        words = user_input.split()
        length = len(words)

        # Keywords for depth/reasoning
        expert_keywords = ["therefore", "consequently", "furthermore", "in-depth", "systematic"]
        specific_keywords = ["because", "which leads to", "so that", "for example", "specifically", "in detail"]
        developing_keywords = ["maybe", "perhaps", "I think", "could be"]
        
        if any(kw in input_lower for kw in expert_keywords) and length > 15:
            return "expert-level"
        if (any(kw in input_lower for kw in specific_keywords) and length > 10) or \
           (re.search(r"\b(my analysis shows|based on data|the key insight is)\b", input_lower) and length > 8):
            return "specific"
        if (any(kw in input_lower for kw in developing_keywords) and length > 5) or \
           (length > 7 and not any(kw in input_lower for kw in specific_keywords + expert_keywords)):
            return "developing"
        if length <= 5 and not any(kw in input_lower for kw in specific_keywords + expert_keywords + developing_keywords):
            return "vague" # Short, non-specific answers
        return "developing" # Default catch-all

    def detect_user_cues(self, user_input: str, context_step: str = "") -> str:
        """
        Detects user's conversational cues:
        - "decided": makes a clear choice/decision or expresses strong conviction.
        - "open": wants suggestions, is exploring, or asks "what if" type questions.
        - "uncertain": signals confusion, asks for help, uses hesitant language.
        - "curious": asks for more information, expresses desire to learn/understand.
        - "neutral": if no strong cues are detected.
        """
        input_lower = user_input.lower()

        if any(kw in input_lower for kw in ["i've decided", "i want to proceed with", "my choice is", "definitely", "for sure", "absolutely", "i will go with"]):
            return "decided"
        if any(kw in input_lower for kw in ["what if", "tell me more about", "how does that work", "i'm interested in learning", "explain further", "why is that"]):
            return "curious"
        if any(kw in input_lower for kw in ["not sure", "don't know", "unsure", "help", "confused", "i'm hesitant", "i'm finding this difficult"]):
            return "uncertain"
        if any(kw in input_lower for kw in ["open to ideas", "suggest something", "what do you recommend", "explore options", "any advice", "what are the alternatives"]):
            return "open"
        
        # Heuristic for decided if short and affirmative, but less strong than explicit keywords
        if len(input_lower.split()) <= 5 and any(kw in input_lower for kw in ["yes", "agree", "that's right", "sounds good"]):
            return "decided"
            
        return "neutral" # Default if no strong cues

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

    def _build_contextual_recap_prompt_segment(self, scratchpad: dict, current_step: str) -> str:
        """
        Builds a prompt segment to recap relevant details from the scratchpad.
        """
        recap_parts = []
        if not scratchpad:
            return ""

        # Prioritize recapping elements closely related to the current_step or recently discussed
        # This is a simplified logic; a more sophisticated approach might track discussion flow.
        related_keys = {
            "problem": [],
            "target_user": ["problem"],
            "solution": ["problem", "target_user"],
            "main_benefit": ["solution", "target_user"],
            "differentiator": ["solution", "main_benefit"],
            "use_case": ["solution", "target_user", "main_benefit"]
        }

        elements_to_recap = {}
        if current_step in related_keys:
            for key in related_keys[current_step]:
                if scratchpad.get(key):
                    elements_to_recap[key] = scratchpad[key]
        
        # Always include the element just before the current one if available and not already included
        # This requires knowing the workflow order, simplified here.
        # A more robust way would be to pass the workflow order or previous step.
        workflow_order = ["problem", "target_user", "solution", "main_benefit", "differentiator", "use_case"]
        if current_step in workflow_order:
            current_idx = workflow_order.index(current_step)
            if current_idx > 0:
                prev_step = workflow_order[current_idx - 1]
                if scratchpad.get(prev_step) and prev_step not in elements_to_recap:
                     elements_to_recap[prev_step] = scratchpad[prev_step]
        
        if not elements_to_recap and scratchpad: # Fallback to last filled item if no direct relation
            # Get the last non-empty item from a defined order or just the scratchpad
            for key in reversed(workflow_order):
                if scratchpad.get(key):
                    elements_to_recap[key] = scratchpad[key]
                    break
        
        if elements_to_recap:
            recap_parts.append("Just to recap, so far we've discussed:")
            for key, value in elements_to_recap.items():
                recap_parts.append(f"- For '{key.replace('_', ' ')}', you mentioned: '{str(value)[:100]}...'") # Truncate for brevity
            return " ".join(recap_parts) + " Now, focusing on the current step: "
        return ""

    def offer_example(self, step: str, user_input_for_context: str = "") -> str:
        """
        Asks the user if they want an example, then can generate it if requested.
        For now, this method will be updated to frame the LLM call to ask first.
        The actual delivery of the example upon user confirmation would ideally be a separate step/call.
        """
        # This prompt now instructs the LLM to ask first.
        system_prompt_base = f"""You are a helpful coaching assistant. The user is working on the '{step}' step.
First, ask the user if they would like an example for this step. Phrase it like: 'Would you like an example for the {step}, or do you have some initial thoughts?' or 'Sometimes an example can be helpful for the {step} step. Would you like one, or are you ready to share your ideas?'
If their prior input ('{user_input_for_context}') was very vague, you can be slightly more direct: 'I can offer an example for {step} to help clarify, if you'd like. Would that be helpful?'
Only provide the question asking if they want an example. Do not provide the example itself yet.
Your response should be ONLY the question.
"""
        # The user_prompt is minimal as the system_prompt guides the LLM to ask the permission question.
        user_prompt = f"The user is on step: {step}. Their previous input was: '{user_input_for_context}'. Ask if they want an example."

        messages = [
            {"role": "system", "content": system_prompt_base},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # This call now expects the LLM to return the question "Would you like an example?"
            response = query_openai(messages=messages, max_tokens=70, temperature=0.6)
            return response
        except Exception as e:
            print(f"Error in offer_example (permission asking) LLM call: {e}")
            return f"Would you like an example for the {step} step?" # Fallback question

    def provide_actual_example(self, step: str) -> str:
        """
        Generates and provides a concrete example for a given workflow step using an LLM.
        This method is called *after* the user has agreed to see an example.
        """
        system_prompt_base = """You are a helpful assistant. Your goal is to provide a single, concise, and relevant example for the given workflow step to help the user understand the type of input expected. Do not use quotation marks or list multiple examples. The example should be illustrative.
        Base the example on common scenarios but keep it brief and focused on the step's purpose.
        """
        user_prompt = f"The current workflow step is '{step}'. Please provide one clear and concise example for this step."

        # Step-specific guidance for the LLM (can be enhanced)
        if step == "problem":
            system_prompt = system_prompt_base + " For 'problem', an example could be: 'Patients often miss follow-up appointments because they forget or find scheduling inconvenient.'"
        elif step == "target_user":
            system_prompt = system_prompt_base + " For 'target_user', an example could be: 'Busy working parents who struggle to find time for their own healthcare appointments.'"
        elif step == "solution":
            system_prompt = system_prompt_base + " For 'solution', an example could be: 'An AI-powered chatbot that proactively reminds patients and allows easy rescheduling via text.'"
        elif step == "main_benefit":
            system_prompt = system_prompt_base + " For 'main_benefit', an example could be: 'Reduces no-show rates by 15% and frees up 5 hours of admin staff time per week.'"
        elif step == "differentiator":
            system_prompt = system_prompt_base + " For 'differentiator', an example could be: 'Unlike basic reminder systems, our solution uses personalized timing and empathetic language, increasing engagement.'"
        elif step == "use_case":
            system_prompt = system_prompt_base + " For 'use_case', an example could be: 'A patient receives a reminder 2 days before, confirms, then gets a day-of reminder with a map link. If they need to reschedule, they can do so with two text replies.'"
        else:
            system_prompt = system_prompt_base + f" Provide a clear, illustrative example for the '{step}' step."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=100, temperature=0.5)
            return response
        except Exception as e:
            print(f"Error in provide_actual_example LLM call: {e}")
            return f"For instance, for the {step}, one might consider..." # Fallback example

    def offer_strategic_suggestion(self, step: str, user_input_for_context: str = "") -> str:
        """
        Asks the user if they want a strategic suggestion for a workflow step.
        The actual delivery of the suggestion upon user confirmation would ideally be a separate step/call.
        """
        system_prompt_base = f"""You are a helpful coaching assistant. The user is working on the '{step}' step.
Their previous input was: '{user_input_for_context}'.
First, ask the user if they would like a strategic tip or a question to consider for this step.
Phrase it like: 'I have a strategic thought for the {step} step, if you're interested?' or 'Would a quick tip or a thought-provoking question be helpful as you consider the {step}?'
Your response should be ONLY the question asking if they want a suggestion. Do not provide the suggestion itself yet.
"""
        user_prompt = f"The user is on step: {step}. Their previous input was: '{user_input_for_context}'. Ask if they want a strategic suggestion."

        messages = [
            {"role": "system", "content": system_prompt_base},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=70, temperature=0.6)
            return response
        except Exception as e:
            print(f"Error in offer_strategic_suggestion (permission asking) LLM call: {e}")
            return f"Would you like a strategic tip for the {step} step?" # Fallback

    def provide_actual_strategic_suggestion(self, step: str) -> str:
        """
        Generates and provides a concrete strategic suggestion for a given workflow step using an LLM.
        This method is called *after* the user has agreed to hear a suggestion.
        """
        system_prompt_base = "You are a helpful assistant. Offer one strategic suggestion to help the user clarify or advance the current workflow step. The suggestion should be a question or a gentle prompt, not a direct command. Explain briefly why this suggestion could be helpful."
        user_prompt = f"The current workflow step is '{step}'. Please provide one strategic suggestion for this step, explaining its potential benefit."

        if step == "problem":
            system_prompt = system_prompt_base + " For 'problem', you could prompt: 'Have you considered the root cause versus the symptoms of this problem? Focusing on the root cause can lead to more impactful solutions.'"
        elif step == "target_user":
            system_prompt = system_prompt_base + " For 'target_user', you could suggest: 'Could narrowing your target user further help create a more compelling, tailored message? Sometimes a very specific niche is powerful.'"
        elif step == "solution":
            system_prompt = system_prompt_base + " For 'solution', you could ask: 'What's the absolute minimum viable version of your solution that could deliver value? Starting small can help test assumptions quickly.'"
        elif step == "main_benefit":
            system_prompt = system_prompt_base + " For 'main_benefit', you could mention: 'How could you quantify this benefit? Measurable outcomes are often very persuasive.'"
        elif step == "differentiator":
            system_prompt = system_prompt_base + " For 'differentiator', you could ask: 'Is your differentiator sustainable, or could competitors easily replicate it? Thinking about long-term advantage is key.'"
        elif step == "use_case":
            system_prompt = system_prompt_base + " For 'use_case', you could ask: 'Does this use case clearly demonstrate the main benefit and differentiator in action? A strong narrative here can be very effective.'"
        else:
            system_prompt = system_prompt_base + f" Offer a helpful, strategic suggestion relevant to the '{step}' step, framed as a question or gentle prompt, and explain its benefit."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=120, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error in provide_actual_strategic_suggestion LLM call: {e}")
            return f"For the {step}, one strategic angle to consider is..." # Fallback

    def paraphrase_user_input(self, user_input: str, user_cue: str, current_step: str = "the current topic", scratchpad: dict = None, search_results: list = None) -> str: # Added search_results
        """
        Paraphrases the user's input using an LLM, reflecting the detected user_cue
        and current step, and provides initial context-aware feedback.
        Can optionally use search_results to inform the LLM.
        Now accepts scratchpad for richer context.
        """
        clarity_depth = self.assess_input_clarity_depth(user_input)
        scratchpad = scratchpad or {}

        system_prompt_base = f"""You are a helpful coaching assistant. Your goal is to help the user develop a strong value proposition. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input, culminating in a single question if a question is needed. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
The current step is '{current_step}'. The user's input for this step is: '{user_input}'.
The current state of their value proposition development (scratchpad) is: {scratchpad}.
Your response should have two parts:
1. First, acknowledge and briefly paraphrase the user's input for '{current_step}'. Do not use direct quotation. Refer to their input conceptually, for example, as 'your idea about {current_step} being {user_input[:30]}...' or 'your thoughts on {current_step} focusing on [paraphrased essence]'.
2. Second, provide brief, context-aware feedback based on their input's specificity and its relevance to the '{current_step}', potentially drawing context from the scratchpad.
"""
        if search_results:
            system_prompt_base += f"\nRelevant search results for context: {search_results}\n"

        # Feedback based on clarity_depth
        if clarity_depth == "vague":
            system_prompt_base += (
                f"The user's input '{user_input}' for '{current_step}' seems quite general. "
                f"In your feedback part, explain briefly why more detail for '{current_step}' (related to their idea of '{user_input}') would be beneficial. For example: 'Thanks for sharing that initial thought on {current_step}. To really dig into this, could we explore [specific aspect] in a bit more detail? This helps ensure we're building a solid foundation.'\n"
            )
        elif clarity_depth == "developing":
            system_prompt_base += (
                f"The user's input '{user_input}' for '{current_step}' is starting to take shape. "
                f"In your feedback part, acknowledge the progress and gently probe for more specifics. For example: 'That's an interesting direction for {current_step} with your idea of \"{user_input[:30]}...\". To build on that, perhaps we could clarify [a specific point]?'\n"
            )
        elif clarity_depth == "specific":
            system_prompt_base += (
                f"The user's input '{user_input}' for '{current_step}' is quite specific. "
                f"In your feedback part, affirm this (e.g., 'That's a clear and specific direction for {current_step} regarding \"{user_input[:30]}...\".'). "
                f"You might also briefly note how this specificity is helpful.\n"
            )
        elif clarity_depth == "expert-level":
             system_prompt_base += (
                f"The user's input '{user_input}' for '{current_step}' is very detailed and insightful. "
                f"In your feedback part, acknowledge this strongly (e.g., 'That's a very thorough and well-articulated point on {current_step} concerning \"{user_input[:30]}...\". This level of detail is excellent!').\n"
            )

        # Cue-specific additions to the prompt (these will guide the *tone* and *framing* of the two-part response)
        if user_cue == "decided":
            system_prompt = system_prompt_base + f"Frame your two-part response (paraphrase + feedback) with confidence, acknowledging their clear direction regarding '{user_input[:30]}...' for {current_step}."
        elif user_cue == "uncertain":
            system_prompt = system_prompt_base + f"Frame your two-part response gently and reassuringly, acknowledging they are exploring ideas like '{user_input[:30]}...' for {current_step} and might be unsure."
        elif user_cue == "open":
            system_prompt = system_prompt_base + f"Frame your two-part response encouragingly, noting their openness to exploring ideas like '{user_input[:30]}...' for {current_step}."
        elif user_cue == "curious":
            system_prompt = system_prompt_base + f"Frame your two-part response by acknowledging their curiosity about '{user_input[:30]}...' for {current_step} and indicating a willingness to explore or explain."
        else: # neutral or other
            system_prompt = system_prompt_base + f"Frame your two-part response with clear, neutral acknowledgement of their input '{user_input[:30]}...' for {current_step}."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please provide your coaching paraphrase and initial feedback."}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=150, temperature=0.7) # Increased tokens
            
            # Micro-validation for detailed input
            clarity_depth = self.assess_input_clarity_depth(user_input)
            if clarity_depth in ["specific", "expert-level"] and user_input and len(user_input.split()) > 15 : # Arbitrary length for "detailed"
                micro_validation = "That's a very clear and detailed response, thank you for putting that thought into it! "
                response = micro_validation + response

            # Ensure single question if response doesn't naturally end with one
            if not response.strip().endswith("?"):
                response += " What are your thoughts on this?" # Generic follow-up

            return response
        except Exception as e:
            print(f"Error in paraphrase_user_input LLM call: {e}")
            # Fallback that still tries to reference the input
            if user_input:
                 return f"I've noted your thoughts on {current_step}: '{user_input[:50]}...'. Let's consider how to refine this. What's one aspect you'd like to focus on next?"
            return f"I'm processing your thoughts on {current_step}. What's the next point you'd like to discuss?"

    def coach_on_decision(self, current_step: str, user_input: str, scratchpad: dict = None, user_cue: str = "decided", search_results: list = None) -> str: # Added search_results
        """
        Coaches the user after they've made a decision (or expressed a strong cue), using an LLM,
        referencing their specific input and explaining the 'why' of feedback.
        Adapts based on input clarity and provides a single follow-up question.
        Can optionally use search_results to inform the LLM.
        Now accepts scratchpad and an explicit user_cue.
        """
        clarity_depth = self.assess_input_clarity_depth(user_input)
        scratchpad = scratchpad or {}
        
        system_prompt_base = f"""You are a helpful coaching assistant. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input, culminating in a single, focused question. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
        The user has expressed a '{user_cue}' cue for the '{current_step}'. Their input was conceptually about '{user_input}'.
        The current state of their value proposition development (scratchpad) is: {scratchpad}.
        Your task is to provide feedback. DO NOT quote the user's input '{user_input}' directly. Instead, refer to it as 'your decision about {current_step}', 'your idea of {user_input[:30]}...', or 'your focus on [paraphrased essence of user_input]'. Explain *why* your feedback or suggestions are helpful for them to build a strong value proposition.
        Conclude with a single, clear question to move the conversation forward.
        """
        if search_results:
            system_prompt_base += f"\nRelevant search results for context: {search_results}\n"

        # Tailor feedback and follow-up question based on clarity_depth
        if clarity_depth == "vague":
            system_prompt = system_prompt_base + (
                f"The user's input for '{current_step}', around '{user_input}', is a bit general. "
                f"Acknowledge their direction. Explain that adding more detail to '{user_input}' for '{current_step}' can make their value proposition much stronger by clarifying [mention a specific benefit like target audience or unique value]. "
                f"Suggest one way they could add detail. For example, if '{current_step}' is 'problem' and they said 'inefficiency', you might suggest: 'For 'inefficiency', could you describe a specific scenario where this inefficiency occurs and who it impacts most? That would help us zero in on the core issue.' "
                f"End by asking a single question inviting them to elaborate on that specific suggestion or a related aspect. For example: 'Would you like to explore that specific scenario of inefficiency, or is there another angle you're considering?'"
            )
        elif clarity_depth == "developing":
            system_prompt = system_prompt_base + (
                f"The user's input for '{current_step}', which is '{user_input}', is developing well. "
                f"Acknowledge their idea. Explain that building on this with a bit more specificity for '{current_step}' regarding '{user_input}' will help solidify [mention a benefit like solution focus or benefit articulation]. "
                f"Offer a concrete suggestion for refinement. For example, if '{current_step}' is 'solution' and they mentioned 'a new app', you could suggest: 'With the 'new app' idea, what's one key feature that directly tackles the problem we discussed? Focusing on that can make its value very clear.' "
                f"End by asking a single question inviting them to elaborate on that key feature or how it connects. For example: 'What are your thoughts on that key feature, or how do you see it directly solving the problem?'"
            )
        elif clarity_depth == "specific":
            system_prompt = system_prompt_base + (
                f"The user's input for '{current_step}', which is '{user_input}', is quite specific and clear. "
                f"Affirm this (e.g., 'Your focus on {user_input[:30]}... for {current_step} is very clear and specific. That's great!'). "
                f"Explain briefly why this specificity is valuable (e.g., 'This level of detail for {current_step} is excellent because it helps us [mention benefit like tailor next steps or ensure alignment].'). "
                f"Then, ask a single, focused question to build on their specific input. For example: 'What's the primary motivation or experience that led you to this specific idea for {current_step}?' or 'How do you see this specific point connecting to [next logical element, e.g., the main benefit]?'"
            )
        elif clarity_depth == "expert-level":
            system_prompt = system_prompt_base + (
                f"The user's input for '{current_step}', '{user_input}', is exceptionally clear and insightful. "
                f"Strongly affirm their detailed thinking (e.g., 'That's a very well-thought-out and comprehensive perspective on {current_step} with your idea of {user_input[:30]}...! The depth here is impressive.'). "
                f"Briefly state how this advanced input is beneficial (e.g., 'This allows us to move quite effectively to [related concept or next step].'). "
                f"Ask a single, high-level strategic question that respects their expertise. For example: 'Given this detailed understanding of {current_step}, what do you foresee as the biggest challenge or opportunity in implementing this?' or 'How might this detailed insight into {current_step} influence our approach to [a broader strategic area]?'"
            )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please provide your coaching feedback on my decision."}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=180, temperature=0.7) # Increased tokens
            
            # Micro-validation for detailed input
            clarity_depth = self.assess_input_clarity_depth(user_input)
            if clarity_depth in ["specific", "expert-level"] and user_input and len(user_input.split()) > 15 :
                micro_validation = "Thanks for sharing such a detailed perspective on that! "
                response = micro_validation + response
            
            # Ensure single question if response doesn't naturally end with one
            if not response.strip().endswith("?"):
                 response += " What are your thoughts on this approach?"

            return response
        except Exception as e:
            print(f"Error in coach_on_decision LLM call: {e}")
            # Fallback that still tries to reference the input
            if user_input:
                return f"That's an interesting decision for {current_step} regarding '{user_input[:50]}...'. What's the primary reason you landed on that?"
            return f"That's an interesting decision for {current_step}. Could you share a bit more about your thinking?"

    def provide_feedback(self, current_value_prop_elements: dict, user_request: str, scratchpad: dict) -> str:
        """
        Provides critical, constructive feedback on the current value proposition elements using an LLM.
        Includes contextual recap and ensures a single, focused follow-up question.
        """
        problem_summary = current_value_prop_elements.get("problem", "not yet defined")
        target_user_summary = current_value_prop_elements.get("target_user", "not yet defined")
        solution_summary = current_value_prop_elements.get("solution", "not yet defined")
        benefit_summary = current_value_prop_elements.get("main_benefit", "not yet defined")
        differentiator_summary = current_value_prop_elements.get("differentiator", "not yet defined")
        use_case_summary = current_value_prop_elements.get("use_case", "not yet defined")

        recap_segment = self._build_contextual_recap_prompt_segment(scratchpad, "feedback_stage")

        system_prompt = f"""You are a helpful coaching assistant. Your goal is to provide critical, constructive feedback on the user's current value proposition elements to help them build a strong and compelling one. The chatbot must choose the *single most relevant and context-appropriate* response or follow-up per user input, culminating in a single focused question. The chatbot must not combine, batch, or list multiple options or suggestions in one response. Base your response only on what the user has shared, unless you need to offer a *single* specific example to clarify a vague input. Do not invent unrelated details.
        {recap_segment}
        When referring to the user's input for each element (problem, target user, solution, etc.), paraphrase it conceptually (e.g., 'Regarding the problem you've identified as affecting X...' or 'Your proposed solution involving Y...'). Do not quote their input directly. Avoid generic terms like 'the problem' and instead refer to 'the problem you described concerning Z'.
        Your feedback should:
        1. Identify one key strength, connecting it to how it contributes to a strong value proposition.
        2. Pinpoint one primary area for improvement or a key question to consider. Explain *why* addressing this point would strengthen their value proposition.
        3. Offer one piece of concrete, actionable advice related to the area of improvement. Explain how this advice helps.
        Maintain a constructive, supportive tone throughout.
        Conclude with a single, focused question inviting the user to respond to the key piece of feedback or to choose a direction for refinement. For example: 'What are your thoughts on [key feedback point], or would you prefer to focus on [alternative aspect] next?'
        """
        
        user_prompt_for_llm = (
            f"Here's the current value proposition for feedback, based on my request '{user_request}':\n"
            f"- Problem: {problem_summary}\n"
            f"- Target User: {target_user_summary}\n"
            f"- Solution: {solution_summary}\n"
            f"- Main Benefit: {benefit_summary}\n"
            f"- Differentiator: {differentiator_summary}\n"
            f"- Use Case: {use_case_summary}\n"
            "Please provide your focused, constructive feedback, explaining the 'why' behind your points, and end with a single question."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=300, temperature=0.7) # Increased max_tokens
            if not response.strip().endswith("?"):
                response += " What are your initial thoughts on this feedback?"
            return response
        except Exception as e:
            print(f"Error in provide_feedback LLM call: {e}")
            return "That's an interesting set of ideas. Let's think about how they fit together. What's one area you'd like to discuss first?" # Fallback

    def generate_ideas(self, current_value_prop_elements: dict, user_request: str, scratchpad: dict) -> str:
        """
        Analyzes current input and offers one thoughtful, actionable suggestion using an LLM.
        Ensures suggestions are collaborative and culminate in a single question.
        """
        problem_summary = current_value_prop_elements.get("problem", "not defined yet")
        target_user_summary = current_value_prop_elements.get("target_user", "not defined yet")
        solution_summary = current_value_prop_elements.get("solution", "not defined yet")
        benefit_summary = current_value_prop_elements.get("main_benefit", "not defined yet")
        differentiator_summary = current_value_prop_elements.get("differentiator", "not defined yet")
        use_case_summary = current_value_prop_elements.get("use_case", "not defined yet")

        recap_segment = self._build_contextual_recap_prompt_segment(scratchpad, "idea_generation_stage")

        system_prompt = f"""You are a helpful coaching assistant. Your goal is to generate one thoughtful, actionable suggestion based on the user's current value proposition elements, helping them to strengthen it. The chatbot must offer only a *single* suggestion or idea per turn. Base your response only on what the user has shared.
        {recap_segment}
        When referring to the user's input for each element, paraphrase it conceptually. Do not quote their input directly.
        Your suggestion should:
        1. Be directly based on their existing elements to ensure relevance.
        2. Identify one potential gap or area for further development, explaining *why* exploring this could be beneficial.
        3. Suggest one concrete next step or alternative angle. Explain *how* it could help them build a more compelling value proposition.
        Aim for a specific, actionable idea, not generic advice. Frame the suggestion collaboratively.
        Conclude by offering the user a chance to approve, revise, or suggest an alternative to your idea, phrased as a single question. For example: 'One thought is to explore [your suggested idea] – how does that sound? Or would you prefer to tweak it or consider another direction?'
        """
        
        user_prompt_for_llm = (
            f"Based on my request '{user_request}' and the current value proposition:\n"
            f"- Problem: {problem_summary}\n"
            f"- Target User: {target_user_summary}\n"
            f"- Solution: {solution_summary}\n"
            f"- Main Benefit: {benefit_summary}\n"
            f"- Differentiator: {differentiator_summary}\n"
            f"- Use Case: {use_case_summary}\n"
            "Please generate one key idea or suggestion, explain how it could help, and ask for my input on it with a single question."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_llm}
        ]
        
        try:
            response = query_openai(messages=messages, max_tokens=300, temperature=0.75) # Increased max_tokens
            if not response.strip().endswith("?"):
                response += " What do you think of this suggestion?"
            return response
        except Exception as e:
            print(f"Error in generate_ideas LLM call: {e}")
            return "Let's brainstorm some possibilities. What's one area you feel could be stronger?" # Fallback

    def get_intake_to_ideation_transition_message(self) -> str:
        """
        Returns the introductory message for transitioning from intake to ideation.
        """
        return (
            "That's a great starting point! We've completed the initial intake. "
            "Now, we'll move into the ideation phase to explore and refine your value proposition. "
            "I'm here to help you brainstorm and develop your ideas."
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

    def generate_value_prop_summary(self, scratchpad: dict, for_reflection: bool = False) -> str:
        """
        Generates a structured summary string with a main paragraph, use cases, and recommendations
        based on the provided scratchpad. This method formats the data and does not call an LLM.
        If for_reflection is True, it prefaces with "Here's where we are now...".
        """
        problem_desc = scratchpad.get('problem')
        target_user_desc = scratchpad.get('target_user') # Corrected key from target_customer
        solution_desc = scratchpad.get('solution')
        benefit_desc = scratchpad.get('main_benefit')
        differentiator_desc = scratchpad.get('differentiator')
        use_case_desc = scratchpad.get('use_case')
        research_requests = scratchpad.get("research_requests", [])

        summary_parts = []
        if for_reflection:
            summary_parts.append("Okay, let's pause for a moment and see where we are. Based on our conversation:\n")

        # 1. Main Summary Paragraph
        main_summary_elements = []
        if problem_desc:
            main_summary_elements.append(f"It sounds like the core problem you're focusing on is '{problem_desc}'.")
        if target_user_desc:
            main_summary_elements.append(f"And the primary group affected by this, your target user, appears to be '{target_user_desc}'.")
        if solution_desc:
            main_summary_elements.append(f"To address this, your solution idea revolves around '{solution_desc}'.")
        if benefit_desc:
            main_summary_elements.append(f"The main benefit this aims to provide is '{benefit_desc}'.")
        if differentiator_desc:
            main_summary_elements.append(f"And what makes it unique, your differentiator, could be '{differentiator_desc}'.")
        
        if main_summary_elements:
            summary_paragraph = " ".join(main_summary_elements)
            summary_parts.append(summary_paragraph)
        elif not for_reflection :
            summary_parts.append("The value proposition is still under development.")
        elif not main_summary_elements and for_reflection:
             summary_parts.append("We're just getting started, so no major elements defined yet!")


        # 2. Use Case Section
        if use_case_desc:
            summary_parts.append(f"\n\n**A potential Use Case you've described is:**\n{use_case_desc}")
        elif 'use_case' in scratchpad and for_reflection: # if key exists but is empty, for reflection
             summary_parts.append("\n\nWe haven't detailed specific use cases yet.")
        elif 'use_case' in scratchpad and not for_reflection: # if key exists but is empty, for formal summary
            summary_parts.append("\n\n**Use Case(s):**\nNot yet defined.")


        # 3. Actionable Recommendations Section (only for formal summary, not brief reflection)
        if not for_reflection and research_requests:
            recs_text_parts = []
            for req in research_requests:
                if isinstance(req, dict):
                    recs_text_parts.append(f"- It's recommended to research the {req.get('step', 'relevant area')} further, focusing on: {req.get('details', 'specific aspects not yet defined')}.")
                elif isinstance(req, str):
                    recs_text_parts.append(f"- Further research is suggested for: {req}.")
            
            if recs_text_parts:
                recommendations_text = "\n".join(recs_text_parts)
                summary_parts.append(f"\n\n**Actionable Recommendations:**\n{recommendations_text}")
        
        return "".join(summary_parts).strip()

    def offer_reflective_summary(self, scratchpad: dict) -> str:
        """
        Provides a brief, reflective progress summary ("Here’s where we are now…")
        and invites user validation or course correction with a single question.
        """
        summary = self.generate_value_prop_summary(scratchpad, for_reflection=True)
        if not summary or summary.strip() == "Okay, let's pause for a moment and see where we are. Based on our conversation:":
            return "We're still in the early stages of shaping your idea. What aspect feels most important to tackle next?"

        question = "\n\nHow does that summary resonate with you? Does it accurately capture our progress, or is there anything you'd like to adjust or add before we continue?"
        return summary + question

    def communicate_next_step(self, completed_step: str, next_step: str, scratchpad: dict) -> str:
        """
        Transparently communicates the next step to the user after an element/phase is completed.
        Includes a brief recap of the completed step and ends with a single question.
        """
        completed_step_value = scratchpad.get(completed_step, "that last point we discussed")
        # Simplified recap; could be more dynamic
        recap = f"Great, we've established a good direction for '{completed_step.replace('_', ' ')}' with your thoughts around '{str(completed_step_value)[:75]}...'."
        
        if next_step:
            message = f"{recap} Now, a logical next area to explore is the '{next_step.replace('_', ' ')}'. Does that sound like a good next step, or is there something else you'd prefer to focus on?"
        else: # End of a major phase or workflow
            message = f"{recap} That covers the main elements we planned for this phase! We could review everything in more detail, or perhaps explore how these pieces fit into a larger picture. What feels most valuable to you right now?"
        return message

    def present_recommendations_and_ask_next(self, recommendation_content: str, scratchpad: dict) -> str:
        """
        Presents the generated recommendations and asks the user for the next action.
        """
        # In a real scenario, this might involve more sophisticated formatting or LLM usage.
        # For now, it just combines the content with a question.
        question = "\n\nWhat are your thoughts on these recommendations? We can iterate on them, or if you're ready, move to a summary."
        return f"{recommendation_content}{question}"

    def prompt_after_recommendations(self, scratchpad: dict) -> str:
        """
        Provides a prompt to the user after recommendations have been shown,
        if the user provides empty input.
        """
        # Based on ValuePropWorkflow logic:
        # core_response = "The recommendations have been provided. What would you like to do next? We can iterate, revisit previous steps, or proceed to the summary."
        return "The recommendations have been provided. What would you like to do next? We can iterate, revisit previous steps, or proceed to the summary."

    def introduce_iteration_phase(self, scratchpad: dict) -> str:
        """
        Introduces the iteration phase to the user.
        """
        # Based on ValuePropWorkflow logic:
        # core_response = "We are now in the iteration phase. You can revise parts of your value proposition, ask to re-run recommendations, or move to the summary. What would you like to do?"
        return "We are now in the iteration phase. You can revise parts of your value proposition, ask to re-run recommendations, or move to the summary. What would you like to do?"

    def generate_short_summary(self, text: str) -> str:
        """
        Sends text to OpenAI to create a short (<=100-token) summary.
        """
        summary_prompt = f"Summarize the following text in 100 tokens or less:\n\n{text}"
        # Use a slightly lower temperature for summarization to get more concise results
        # query_openai is available via from ..llm_utils import query_openai
        summary = query_openai(messages=[{"role": "user", "content": summary_prompt}], temperature=0.5, max_tokens=100)
        return summary

    def greet_and_explain_value_prop_process(self) -> str:
        """
        Provides an initial greeting and explanation of the value proposition workflow.
        """
        # This is the method ValuePropWorkflow expects for the initial greeting.
        return "Welcome to the Value Proposition Workflow! We'll start by defining the problem you're aiming to solve. What problem are you focusing on?"

    def propose_next_conversation_turn(self, intake_answers: list, scratchpad: dict, phase: str, conversation_history: list = None) -> str:
        """
        Uses the LLM to propose the next natural conversation turn based on intake, scratchpad, phase, and conversation history.
        Aims for peer coaching, brainstorming, and conversational EQ.
        """
        # client is available via from ..llm_utils import client
        system_prompt_content = """You are a peer coach, and I am helping the user brainstorm new digital health innovations. My goal is to help them surface promising business ideas. I should build on any aspect of their prior answers (from intake) that shows potential, creativity, or relevance, but for the *very first question of the 'ideation' phase*, I need to be particularly open-ended.

Specifically for the first turn of 'ideation':
- Acknowledge key themes from their intake answers briefly.
- Ask a broad, inviting question to explore initial thoughts for their value proposition. Avoid making specific assumptions about the direction they want to take, even if their background suggests a particular area. For example, instead of asking "Given your nursing background, how about an app for X?", ask something like "Drawing from your experiences, what initial thoughts or areas are you most excited to explore for your value proposition?" or "What kind of problems are you most passionate about solving right now?"
- Use "I" and "you" pronouns to make the conversation direct and personal. For example, "I can help you explore..." or "What are you thinking about...". Avoid "we" unless it's about a shared, immediate action like "Let's brainstorm."

For all other interactions (and subsequent turns in 'ideation'):
- I am not a therapist, but I am very emotionally intelligent and always bring conversational energy and warmth.
- I should never just repeat the user’s last answer. I always move the conversation forward, build excitement, and keep things open-ended.
- If the user says ‘no’, ‘I don’t know’, or gives a one-word answer, I should gently prompt them to revisit an earlier idea, suggest a new direction, or validate that it’s normal to feel stuck.

Example interaction (general, not first ideation turn):
User: I care about cost savings and rapid deployment.
Assistant: I hear you - so quick wins and low friction matter. I could help you brainstorm ideas for settings where speed makes a huge difference, or we could dive into ways to get to value quickly. Would you like to explore those, or is there another angle you’re curious about?"""

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
1.  **Scan** all intake responses, scratchpad fields (paying attention to which are filled and how detailed they are), and recent conversation history.
2.  **Identify the single strongest or most developed element** from the scratchpad (e.g., 'problem', 'target_user', 'solution') that appears to be the **least vetted or explored in the recent conversation history**. "Least vetted" means it hasn't been the focus of recent questions or detailed discussion. If multiple elements are strong but not fully vetted, choose the one that seems most foundational or pivotal for the user's idea.
3.  **Briefly recap relevant details** already provided by the user for this chosen element, drawing from the scratchpad and conversation history. This sets context.
4.  **Express enthusiasm or acknowledge the user's current thinking** on this specific element in a natural, peer-like way.
5.  **Ask a single, focused, open-ended question** to further vet, develop, or deepen the understanding of *this specific element*. The question should encourage the user to elaborate, clarify, consider implications, or think about next steps for that element. Examples: "That's an interesting point about [element X]. Could you tell me more about [specific aspect of X]?" or "Building on your idea for [element Y], what's one challenge you foresee in that area?" or "You've got a good start on [element Z]. What feels like the most important next thought to explore for it?"
6.  **Ensure your entire response culminates in this single, focused question.** Do not ask multiple questions or offer a list of options to choose from.
7.  If previous user responses were very brief, negative ("no"), or indicated uncertainty ("I don't know"), gently pivot. You can do this by acknowledging their response, then perhaps revisiting the chosen "strongest, least vetted element" with a slightly different angle or by offering to break it down further.
8.  Maintain a friendly, peer-like tone, using mild humor and warmth when appropriate. Always aim to move the conversation forward constructively on the chosen element.

--- Example Scenarios (Revised Focus) ---

Scenario 1: Focusing on a strong, less-vetted element
Context:
  Scratchpad: Problem: "Students lack accessible mental wellness resources." Target_User: "University undergraduates." Solution: (empty)
  Recent History: User just finished defining Target_User.
Your Output: "Okay, focusing on university undergraduates as the target user for the problem of lacking accessible mental wellness resources is a solid direction. We haven't really dug into what a solution might look like yet. What are your initial thoughts on how we could start to solve that accessibility issue for them?"

Scenario 2: Handling "no" and refocusing on a developed but unvetted element
Context:
  Scratchpad: Problem: "High stress for nurses." Solution: "AI tool for scheduling." Differentiator: (empty)
  Recent History:
    Assistant: "...Want to explore how the AI tool's interface might look?"
    User: "No."
Your Output: "No problem at all! We can set aside the interface for now. We have a clear problem (high stress for nurses) and a potential solution (AI tool for scheduling). I'm curious, what do you think makes this AI scheduling tool different or better than other approaches nurses might currently use or other tools out there? Exploring that could really highlight its unique value."

Scenario 3: User is uncertain, guide towards a developed element
Context:
  Scratchpad: Problem: "Patients forget medication." Target_User: "Elderly patients with multiple prescriptions." Solution: "Smart pillbox." Main_Benefit: (empty)
  Recent History:
    Assistant: "What's the main benefit of the smart pillbox?"
    User: "I'm not sure yet."
Your Output: "That's perfectly okay, figuring out the main benefit can take some thought! We know the smart pillbox is for elderly patients with multiple prescriptions who tend to forget their medication. Thinking about that specific group and problem, what's the most significant positive change or outcome they would experience from using the smart pillbox consistently?"

--- Now, generate your response for the current user based on their information, focusing on one key element. ---
What is your proposed next conversational turn? (Ensure it's a single, focused question)
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

    def assist_with_brainstorming(self, user_input: str, scratchpad: dict, intake_answers: list) -> str:
        """
        Helps the user brainstorm ideas when they explicitly ask for help.
        Uses an LLM to generate 2-3 diverse ideas or a clarifying question.
        """
        system_prompt = """You are a helpful brainstorming assistant. I am helping the user develop a value proposition.
The user has asked for help generating some ideas.
Your goal is to provide 2-3 diverse, high-level ideas or approaches they could consider, or if their request and context are too vague, ask one clarifying question to help narrow down the area of interest before generating ideas.
Use "I" and "you" pronouns. For example, "I can help you think about..." or "Have you considered...?".
Keep the tone encouraging and collaborative.
"""

        user_prompt_parts = ["--- User's Request for Brainstorming ---", user_input]

        if intake_answers:
            user_prompt_parts.append("\n--- Context from Intake ---")
            for answer_item in intake_answers:
                if isinstance(answer_item, dict) and 'text' in answer_item and answer_item['text']:
                    user_prompt_parts.append(f"- {answer_item['text']}")
                elif isinstance(answer_item, str) and answer_item:
                    user_prompt_parts.append(f"- {answer_item}")
            user_prompt_parts.append("--------------------------")

        if scratchpad and any(scratchpad.values()):
            user_prompt_parts.append("\n--- Current Scratchpad ---")
            for key, value in scratchpad.items():
                if value: # Only include filled scratchpad items
                    user_prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            user_prompt_parts.append("--------------------------")
        
        user_prompt_parts.append("\n--- Your Task ---")
        user_prompt_parts.append("Based on the user's request and any available context, please generate 2-3 diverse, high-level ideas or approaches for their value proposition, OR if the request is too vague, ask a single clarifying question to help them focus. Frame your response directly to the user.")

        full_user_prompt = "\n".join(user_prompt_parts)

        try:
            response = query_openai(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_user_prompt}
                ],
                temperature=0.8, # Higher temperature for more creative brainstorming
                max_tokens=200
            )
            return response
        except Exception as e:
            logging.error(f"Error in assist_with_brainstorming LLM call: {e}")
            return "I'm having a little trouble generating ideas right now. Could you perhaps tell me a bit more about what general area you're interested in?" # Fallback

    # TODO: add behavior methods (paraphrase, feedback, etc.) - These seem to be well covered above.