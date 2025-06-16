"""Defines the different phases of conversation and their handling logic."""
import streamlit as st
from utils.scratchpad_extractor import update_scratchpad
from constants import EMPTY_SCRATCHPAD, CANONICAL_KEYS
from llm_utils import query_openai, build_conversation_messages # Removed propose_next_conversation_turn
from workflows.value_prop import ValuePropWorkflow # Import ValuePropWorkflow
import json
# CHECKLIST, EXPLORATION_PROMPT, and missing_items are removed as this logic is centralized
# or handled by llm_utils, personas, or workflows.

# def missing_items(sp): # Removed
#     # This function might be deprecated if step checking is fully handled by workflows/personas
#     checklist = ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]
#     return [k for k in checklist if not sp.get(k)]

# The handle_exploration function is now removed as its logic has been integrated into ValuePropWorkflow.
# All legacy phase functions have been removed.
# This file can now be deleted.
