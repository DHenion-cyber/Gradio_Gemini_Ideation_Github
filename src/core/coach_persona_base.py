from abc import ABC, abstractmethod

class CoachPersonaBase(ABC):
    """
    Base class for all coach personas.
    Defines the interface for persona methods that PhaseEngines will call.
    """

    @abstractmethod
    def micro_validate(self, user_input: str, **kwargs) -> str:
        """
        Provides a micro-validation or immediate feedback on the user's input.
        Example: "That's a good start for defining the problem."
        """
        raise NotImplementedError("Subclasses must implement micro_validate.")

    @abstractmethod
    def suggest_examples(self, user_input: str, **kwargs) -> str:
        """
        Suggests examples or provides hints if the user is stuck or input is unclear.
        Example: "For instance, a problem could be 'university students struggle to find affordable off-campus housing'."
        """
        raise NotImplementedError("Subclasses must implement suggest_examples.")

    @abstractmethod
    def summarise_intake(self, user_input: str, **kwargs) -> str:
        """
        Summarises the user's input in a structured way, often to confirm understanding.
        Example: "So, to confirm, the core problem you're addressing is X, and it affects Y. Is that right?"
        """
        raise NotImplementedError("Subclasses must implement summarise_intake.")

    @abstractmethod
    def get_step_intro_message(self, **kwargs) -> str:
        """
        Returns the introductory message or question for the current phase/step.
        Example: "Let's start by defining the problem. What specific problem are you trying to solve?"
        """
        raise NotImplementedError("Subclasses must implement get_step_intro_message.")

    def get_clarification_prompt(self, user_input: str, **kwargs) -> str:
        """
        Asks for clarification when user input is ambiguous or insufficient.
        Default implementation, can be overridden.
        """
        return "I'm not sure I fully understand. Could you please rephrase or provide more detail?"

    def get_positive_affirmation_response(self, user_input: str, **kwargs) -> str:
        """
        Responds to a positive affirmation from the user (e.g., "yes", "correct").
        Default implementation, can be overridden.
        """
        return "Great! Let's move on."

    def get_negative_affirmation_response(self, user_input: str, **kwargs) -> str:
        """
        Responds to a negative affirmation from the user (e.g., "no", "incorrect").
        Default implementation, can be overridden.
        """
        return "Okay, let's try that again."