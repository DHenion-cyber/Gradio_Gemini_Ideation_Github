"""Defines the WORKFLOWS registry for mapping string keys to workflow classes."""

from .value_prop import ValuePropWorkflow
from .market_analysis import MarketAnalysisWorkflow
from .business_model import BusinessModelWorkflow
from .planning_growth import PlanningGrowthWorkflow
from .beta_testing import BetaTestingWorkflow
from .pitch_prep import PitchPrepWorkflow

WORKFLOWS = {
    "value_prop": ValuePropWorkflow,
    "market_analysis": MarketAnalysisWorkflow,
    "business_model": BusinessModelWorkflow,
    "planning_growth": PlanningGrowthWorkflow,
    "beta_testing": BetaTestingWorkflow,
    "pitch_prep": PitchPrepWorkflow,
}

# Ensure all abstract methods are implemented in subclasses (checked by Python's ABC)