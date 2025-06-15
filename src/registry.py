"""
Registry for Workflows and Personas.

This module provides a centralized way to register and retrieve workflow and persona
classes using string names. This allows for dynamic instantiation based on user
selection or configuration.

How to add a new Workflow:
1. Create your workflow class, inheriting from a base workflow class if applicable.
   (e.g., in `src/workflows/my_new_workflow.py`)
   ```python
   class MyNewWorkflow:
       def __init__(self, params):
           self.params = params
       # ... other methods
   ```
2. In this file (`src/registry.py`), import your new workflow class:
   ```python
   from .workflows.my_new_workflow import MyNewWorkflow
   ```
3. Register your workflow in the `populate_registries()` function:
   ```python
   register_workflow("My New Workflow Name", MyNewWorkflow)
   ```
   The "My New Workflow Name" is the string that will be used to look up this
   workflow class.

How to add a new Persona:
1. Create your persona class.
   (e.g., in `src/personas/my_new_persona.py`)
   ```python
   class MyNewPersona:
       def __init__(self, config):
           self.config = config
       # ... other methods
   ```
2. In this file (`src/registry.py`), import your new persona class:
   ```python
   from .personas.my_new_persona import MyNewPersona
   ```
3. Register your persona in the `populate_registries()` function:
   ```python
   register_persona("My New Persona Name", MyNewPersona)
   ```
   The "My New Persona Name" is the string that will be used to look up this
   persona class.
"""
from typing import Type, Dict, Any, Callable

# Workflow Imports
from .workflows.beta_testing import BetaTestingWorkflow
from .workflows.business_plan import BusinessPlanWorkflow
from .workflows.market_analysis import MarketAnalysisWorkflow
from .workflows.pitch_prep import PitchPrepWorkflow
from .workflows.planning_growth import PlanningGrowthWorkflow
from .workflows.value_prop import ValuePropWorkflow

# Persona Imports
from .personas.coach import CoachPersona
from .personas.investor import InvestorPersona
from .personas.tester import TesterPersona

# Define types for clarity
WorkflowClass = Type[Any]  # Replace Any with your base Workflow class if you have one
PersonaClass = Type[Any]   # Replace Any with your base Persona class if you have one

WORKFLOW_REGISTRY: Dict[str, WorkflowClass] = {}
PERSONA_REGISTRY: Dict[str, PersonaClass] = {}

def register_workflow(name: str, cls: WorkflowClass) -> None:
    """Registers a workflow class with the given name."""
    if name in WORKFLOW_REGISTRY:
        # Potentially raise an error or log a warning if re-registering
        print(f"Warning: Workflow '{name}' is being re-registered.")
    WORKFLOW_REGISTRY[name] = cls

def get_workflow(name: str) -> WorkflowClass | None:
    """Retrieves a workflow class by its registered name."""
    return WORKFLOW_REGISTRY.get(name)

def register_persona(name: str, cls: PersonaClass) -> None:
    """Registers a persona class with the given name."""
    if name in PERSONA_REGISTRY:
        # Potentially raise an error or log a warning if re-registering
        print(f"Warning: Persona '{name}' is being re-registered.")
    PERSONA_REGISTRY[name] = cls

def get_persona(name: str) -> PersonaClass | None:
    """Retrieves a persona class by its registered name."""
    return PERSONA_REGISTRY.get(name)

def get_available_workflows() -> list[str]:
    """Returns a list of names of all registered workflows."""
    return list(WORKFLOW_REGISTRY.keys())

def get_available_personas() -> list[str]:
    """Returns a list of names of all registered personas."""
    return list(PERSONA_REGISTRY.keys())

# Placeholder for a function to populate registries.
# This function will be called, for example, at application startup.
def populate_registries() -> None:
    """
    Imports and registers all available workflows and personas.
    This function should be called once at the application's startup.
    """
    # Register Workflows
    register_workflow("Beta Testing", BetaTestingWorkflow)
    register_workflow("Business Plan", BusinessPlanWorkflow)
    register_workflow("Market Analysis", MarketAnalysisWorkflow)
    register_workflow("Pitch Prep", PitchPrepWorkflow)
    register_workflow("Planning Growth", PlanningGrowthWorkflow)
    register_workflow("Value Proposition", ValuePropWorkflow)

    # Register Personas
    register_persona("Coach", CoachPersona)
    register_persona("Investor", InvestorPersona)
    register_persona("Tester", TesterPersona)

# It's common practice to call populate_registries() when the module is imported,
# or to have a dedicated initialization step in your application that calls it.
# For now, we'll define it and it can be called explicitly from elsewhere.

if __name__ == '__main__':
    # Example usage and test
    class SampleWorkflow:
        def __init__(self, data):
            self.data = data
        def run(self):
            print(f"Running SampleWorkflow with {self.data}")

    class SamplePersona:
        def __init__(self, name):
            self.name = name
        def greet(self):
            print(f"Hello from SamplePersona {self.name}")

    # Simulate populating
    register_workflow("Sample Workflow", SampleWorkflow)
    register_persona("Sample Persona", SamplePersona)

    # Test retrieval
    RetrievedWorkflow = get_workflow("Sample Workflow")
    RetrievedPersona = get_persona("Sample Persona")

    if RetrievedWorkflow:
        wf_instance = RetrievedWorkflow("test_data")
        wf_instance.run()
    else:
        print("Sample Workflow not found.")

    if RetrievedPersona:
        ps_instance = RetrievedPersona("Tester")
        ps_instance.greet()
    else:
        print("Sample Persona not found.")

    print("\nAvailable Workflows:", get_available_workflows())
    print("Available Personas:", get_available_personas())

    # Example of populating (if called directly)
    # populate_registries()
    # print("\nAfter populate_registries (if implemented):")
    # print("Available Workflows:", get_available_workflows())
    # print("Available Personas:", get_available_personas())