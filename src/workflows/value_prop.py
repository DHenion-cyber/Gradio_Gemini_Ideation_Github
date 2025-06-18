"""
Value Proposition Workflow
--------------------------

This file previously contained the state machine logic for the Value Proposition workflow.
That logic has now been refactored into individual PhaseEngineBase subclasses
located in the `src/workflows/value_prop/phases/` directory.

The `ValuePropCoachPersona` is defined in `src/workflows/value_prop/persona.py`.

The sequence of phases and scratchpad keys are defined in `src/workflows/value_prop/__init__.py`.

The main application (`streamlit_app.py`) will use `WorkflowManager` to get the
current workflow and phase, and then dynamically instantiate and use the
appropriate PhaseEngine from the `phases` directory.
"""

# This file can be used to define any workflow-specific helper functions or
# configurations that don't fit into the persona or individual phase engines.
# For now, it primarily serves as a marker for the 'value_prop' workflow module.

# Example: If there were complex, shared utility functions ONLY for value_prop,
# they could live here.

# from .base import WorkflowBase # If ValuePropWorkflow class was still needed for some reason
# from typing import Dict, Any

# class ValuePropWorkflowDefinition(WorkflowBase): # If a container class is still desired
#     workflow_slug = "value_prop"
#     display_name = "Value Proposition"

#     def __init__(self, context: Dict[str, Any] = None):
#         super().__init__(context)
#         # Potentially load persona or specific configs if not handled by streamlit_app
#         pass

#     # Methods like get_phase, set_phase, process_user_input, generate_summary
#     # are now largely handled by the combination of:
#     # 1. streamlit_app.py (main loop, phase engine instantiation)
#     # 2. src/core/phase_engine_base.py (individual phase logic)
#     # 3. src/workflows/value_prop/persona.py (persona-specific responses)
#     # 4. src/workflow_manager.py (workflow and phase definitions, state reset)

#     def get_initial_phase(self) -> str:
#         from . import PHASE_ORDER # Dynamically import from __init__.py
#         return PHASE_ORDER[0] if PHASE_ORDER else None

#     def get_phase_engine_class(self, phase_name: str):
#         # This would be part of the dynamic loading logic, likely in streamlit_app.py
#         # or a helper in workflow_manager.
#         # Example:
#         # module_name = f"src.workflows.value_prop.phases.{phase_name}"
#         # class_name = "".join([part.capitalize() for part in phase_name.split('_')]) + "Phase"
#         # module = __import__(module_name, fromlist=[class_name])
#         # return getattr(module, class_name)
#         raise NotImplementedError("Dynamic phase engine loading is handled by the application.")

# No active code needed here if streamlit_app.py handles dynamic loading of phases
# based on workflow_manager.py and the __init__.py definitions.

# Keeping the file for module structure integrity.
