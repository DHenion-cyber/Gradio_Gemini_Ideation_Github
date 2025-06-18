from abc import ABC, abstractmethod
import streamlit as st
from src.core.logger import get_logger
from src.analytics import log_event
from src.core.coach_persona_base import CoachPersonaBase

logger = get_logger(__name__)

class PhaseEngineBase(ABC):
    """
    Base class for all phase engines.
    Implements core behavior, logging, and intent parsing.
    """
    phase_name: str = "Unnamed Phase" # Subclasses should override this

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str):
        self.coach_persona = coach_persona
        self.workflow_name = workflow_name
        self._is_complete = False
        if not hasattr(self, 'phase_name') or self.phase_name == "Unnamed Phase":
            logger.warning(f"PhaseEngine subclass {self.__class__.__name__} should define a 'phase_name'.")
            self.phase_name = self.__class__.__name__.replace("Phase", "")


    def enter(self) -> str:
        """
        Called when entering this phase.
        Returns an introductory string/question for the user.
        Logs the phase_enter event.
        """
        self.debug_log(step="enter_phase")
        log_event("phase_enter", phase_name=self.phase_name, workflow_name=self.workflow_name)
        self._is_complete = False # Reset completion status on entry
        return self.coach_persona.get_step_intro_message(phase_name=self.phase_name)

    def handle_response(self, user_input: str) -> dict:
        """
        Processes the user's response based on classified intent.
        Handles content validation, phase completion, and persona interactions.
        Returns a dictionary: {"next_phase": str | None, "reply": str}
        """
        self.debug_log(step="handle_response_start", user_input=user_input)
        intent = self.classify_intent(user_input)
        log_event("intent_classified", phase_name=self.phase_name, workflow_name=self.workflow_name, user_input=user_input, intent=intent)

        reply: str = ""
        next_phase_decision: str | None = None
        user_input_stripped = user_input.strip()
        
        # Store for potential use by subclass logic in get_next_phase_... methods
        st.session_state["last_user_input"] = user_input_stripped
        st.session_state["last_intent_classified"] = intent

        if not user_input_stripped and intent != "unclear": # Ensure genuinely empty strings are treated as unclear
            intent = "unclear" # Reclassify
            st.session_state["last_intent_classified"] = intent # Update stored intent
            log_event("intent_reclassified_empty", phase_name=self.phase_name, original_intent=st.session_state["last_intent_classified"])


        if intent in ["provide_detail", "affirm"]:
            # For "affirm", micro_validate will check if it's a standalone vague affirmation (e.g. "ok")
            # or part of actual content.
            is_valid_content = self.coach_persona.micro_validate(user_input_stripped, phase_name=self.phase_name)
            if is_valid_content:
                self.store_input_to_scratchpad(user_input_stripped)
                # self.mark_complete() # Removed: Subclass's get_next_phase_after_completion will decide if phase is fully done.
                reply = self.coach_persona.get_acknowledgement_message(phase_name=self.phase_name, user_input=user_input_stripped)
                next_phase_decision = self.get_next_phase_after_completion() # This method might call self.mark_complete()
            else:
                # micro_validate returned False (e.g., "ok", "sure" alone, too short, or not specific enough)
                reply = self.coach_persona.get_clarification_prompt(user_input=user_input_stripped, phase_name=self.phase_name, reason="validation_failed")
                # Do not complete
        elif intent == "unclear":
            reply = self.coach_persona.get_clarification_prompt(user_input=user_input_stripped, phase_name=self.phase_name, reason="unclear_input")
            # Do not complete
        elif intent == "ask_suggestion":
            reply = self.coach_persona.suggest_examples(phase_name=self.phase_name, user_input=user_input_stripped)
            # Do not complete
        elif intent == "skip":
            self.store_input_to_scratchpad("") # Store empty string for this phase
            reply = self.coach_persona.get_skip_confirmation_message(phase_name=self.phase_name)
            # This phase is skipped (self.complete remains False), but we allow progression.
            next_phase_decision = self.get_next_phase_after_skip()
            log_event("phase_skipped", phase_name=self.phase_name, workflow_name=self.workflow_name)
        elif intent == "negative":
            reply = self.coach_persona.handle_negative_feedback(user_input=user_input_stripped, phase_name=self.phase_name)
            # Do not complete
        else: # Should not happen if classify_intent is comprehensive
            logger.warning(f"Unhandled intent '{intent}' for input '{user_input_stripped}' in phase '{self.phase_name}'. Falling back to unexpected input.")
            reply = self._handle_unexpected_input(user_input_stripped) # Uses persona's get_clarification_prompt

        self.debug_log(step="handle_response_end", reply_len=len(reply), next_phase=next_phase_decision, completed=self.complete)
        return {"next_phase": next_phase_decision, "reply": reply}

    @abstractmethod
    def store_input_to_scratchpad(self, user_input: str):
        """Stores the validated user input to the session scratchpad.
        Subclasses must implement this to define the scratchpad key and storage logic."""
        raise NotImplementedError

    @abstractmethod
    def get_next_phase_after_completion(self) -> str | None:
        """Determines the next phase name after successful completion.
        Subclasses must implement this. Return None if this is the last phase."""
        raise NotImplementedError

    @abstractmethod
    def get_next_phase_after_skip(self) -> str | None:
        """Determines the next phase name after skipping the current phase.
        Subclasses must implement this. Return None if this is the last phase or skipping is not allowed to progress."""
        raise NotImplementedError

    @property
    def complete(self) -> bool:
        """
        Indicates if this phase has been completed.
        """
        return self._is_complete

    def mark_complete(self):
        """
        Marks the phase as complete and logs the event.
        """
        self._is_complete = True
        log_event("phase_complete", phase_name=self.phase_name, workflow_name=self.workflow_name)
        self.debug_log(step="mark_complete")


    def debug_log(self, step: str, **kwargs):
        """
        Helper for logging debug information.
        """
        logger.debug(f"Workflow: {self.workflow_name}, Phase: {self.phase_name}, Step: {step}", extra=kwargs)

    def classify_intent(self, user_input: str) -> str:
        """
        Classifies user input into predefined intents.
        Order of checks matters.
        """
        user_input_lower = user_input.lower().strip()

        # 1. Handle empty or blank input first
        if not user_input_lower:
            return "unclear"

        # 2. Specific keywords for "skip" (explicit skip terms)
        skip_keywords = ["skip", "not applicable", "n/a", "na"]
        if user_input_lower in skip_keywords:
            return "skip"

        # 3. Specific keywords for "ask_suggestion"
        # Includes "not sure" as per task requirements.
        suggestion_keywords_exact = ["not sure", "notsure", "help me", "any ideas", "give me an example", "what should i write", "can you suggest"]
        suggestion_keywords_contain = ["example", "suggestion", "help", "idea", "suggest", "ideas for"]
        if user_input_lower in suggestion_keywords_exact or \
           any(keyword in user_input_lower for keyword in suggestion_keywords_contain):
            # Avoid classifying "no help needed" as ask_suggestion
            if "no help" in user_input_lower or "don't need help" in user_input_lower:
                 pass # Let it fall through to other classifications
            else:
                return "ask_suggestion"

        # 4. Specific keywords for "unclear" (beyond blank)
        # Includes "idk" as per task requirements.
        unclear_keywords = ["?", "idk", "i don't know", "i dont know", "dunno", "huh", "what"]
        if user_input_lower in unclear_keywords:
            return "unclear"
        
        # 5. Specific keywords for "affirm"
        # "ok", "sure" are included here for intent. micro_validate will check if they are sufficient as content.
        affirm_keywords = [
            "yes", "yep", "yeah", "correct", "ok", "okay", "sure", "sounds good",
            "affirmative", "agree", "exactly", "precisely", "fine", "alright", "got it"
        ]
        if user_input_lower in affirm_keywords:
            return "affirm"

        # 6. Specific keywords for "negative"
        negative_keywords = [
            "no", "nope", "incorrect", "not really", "negative", "disagree",
            "wrong", "not correct", "don't agree"
        ]
        if user_input_lower in negative_keywords:
            return "negative"

        # 7. If non-empty and not matched above, it's "provide_detail"
        # This is the primary intent for user providing substantive content.
        return "provide_detail"

    def _handle_unexpected_input(self, user_input: str) -> str:
        """
        Handles unexpected or unclear user input.
        """
        log_event("unexpected_input", phase_name=self.phase_name, user_input=user_input, workflow_name=self.workflow_name)
        self.debug_log(step="unexpected_input", user_input=user_input)
        reply = self.coach_persona.get_clarification_prompt(user_input=user_input)
        return {"next_phase": None, "reply": reply}