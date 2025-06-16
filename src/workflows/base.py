"""Defines the abstract base class for all workflows in the application."""
from abc import ABC, abstractmethod

class WorkflowBase(ABC):
    """
    Abstract base class for all workflows.
    Defines the common interface that all specific workflows must implement.
    """

    @abstractmethod
    def __init__(self, context=None):
        """
        Initializes the workflow.

        Args:
            context: Optional context or initial data for the workflow.
        """
        pass

    @abstractmethod
    def suggest_next_step(self, user_input=None):
        """
        Suggests the next logical step or question for the user.

        Args:
            user_input: Optional user input from the previous step.

        Returns:
            A string suggesting the next step or question.
        """
        pass

    @abstractmethod
    def process_user_input(self, user_input):
        """
        Processes the user's input and updates the workflow state.

        Args:
            user_input: The input provided by the user.
        """
        pass

    @abstractmethod
    def generate_summary(self):
        """
        Generates a summary of the current state or outcome of the workflow.

        Returns:
            A string containing the summary.
        """
        pass

    @abstractmethod
    def is_complete(self):
        """
        Checks if the workflow has reached its completion state.

        Returns:
            True if the workflow is complete, False otherwise.
        """
        pass

    @abstractmethod
    def get_step(self):
        """
        Returns the current step or phase of the workflow.

        Returns:
            A string or identifier representing the current step.
        """
        pass