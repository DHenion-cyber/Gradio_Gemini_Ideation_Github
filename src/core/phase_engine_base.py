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

    @abstractmethod
    def handle_response(self, user_input: str) -> dict:
        """
        Processes the user's response.
        Classifies intent, calls persona methods, and determines the next step.
        Returns a dictionary: {"next_phase": str | None, "reply": str}
        "next_phase" is the name of the next phase, or None to stay in the current phase.
        "reply" is the bot's response to the user.
        """
        raise NotImplementedError("Subclasses must implement handle_response.")

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
        Basic intent classification.
        Subclasses can override for more sophisticated intent parsing.
        """
        user_input_lower = user_input.lower().strip()
        if user_input_lower in ["yes", "yep", "yeah", "correct", "ok", "okay", "sure", "sounds good"]:
            return "affirm"
        if user_input_lower in ["no", "nope", "incorrect", "not really"]:
            return "negative"
        if "example" in user_input_lower or "suggestion" in user_input_lower or "help" in user_input_lower or "idea" in user_input_lower:
            return "ask_suggestion"
        # Add more sophisticated intent classification here if needed (e.g., using NLU)
        return "unclear"

    def _handle_unexpected_input(self, user_input: str) -> dict:
        """
        Handles unexpected or unclear user input.
        """
        log_event("unexpected_input", phase_name=self.phase_name, user_input=user_input, workflow_name=self.workflow_name)
        self.debug_log(step="unexpected_input", user_input=user_input)
        reply = self.coach_persona.get_clarification_prompt(user_input=user_input)
        return {"next_phase": None, "reply": reply}