import streamlit as st
from .utils.scratchpad_extractor import update_scratchpad
from .constants import EMPTY_SCRATCHPAD, CANONICAL_KEYS
from .llm_utils import query_openai, propose_next_conversation_turn # Import query_openai and propose_next_conversation_turn
import json

def handle_exploration(user_message: str, scratchpad: dict) -> tuple[str, str]:
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    st.session_state["scratchpad"] = updated_scratchpad

    exploration_turns = st.session_state.get("exploration_turns", 0)
    intake_answers = st.session_state.get("intake_answers", [])

    # After several exploration turns, check readiness to move to development
    if exploration_turns >= 4 and any(word in user_message.lower() for word in ["ready", "next", "move forward", "develop", "yes"]):
        st.session_state["exploration_turns"] = 0  # reset for next phase
        assistant_reply = propose_next_conversation_turn(
            intake_answers=st.session_state.get("intake_answers", []),
            scratchpad=updated_scratchpad,
            phase="development", # Transitioning to development
            conversation_history=st.session_state.get("conversation_history", [])
        )
        next_phase = "development"
    else:
        # For non-transition turns within exploration, we might still use a simpler prompt or LLM call
        # For now, let's use propose_next_conversation_turn to keep it consistent,
        # or we can refine this if it feels too heavy for every turn.
        assistant_reply = propose_next_conversation_turn(
            intake_answers=st.session_state.get("intake_answers", []),
            scratchpad=updated_scratchpad,
            phase="exploration", # Still in exploration
            conversation_history=st.session_state.get("conversation_history", [])
        )
        st.session_state["exploration_turns"] = exploration_turns + 1
        next_phase = "exploration"

    return assistant_reply, next_phase

def handle_development(user_message: str, scratchpad: dict) -> tuple[str, str]:
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    st.session_state["scratchpad"] = updated_scratchpad

    development_turns = st.session_state.get("development_turns", 0)
    intake_answers = st.session_state.get("intake_answers", [])

    if development_turns >= 4 and any(word in user_message.lower() for word in ["summary", "complete", "finish", "wrap up"]):
        st.session_state["development_turns"] = 0  # reset for next phase
        assistant_reply = propose_next_conversation_turn(
            intake_answers=st.session_state.get("intake_answers", []),
            scratchpad=updated_scratchpad,
            phase="summary", # Transitioning to summary
            conversation_history=st.session_state.get("conversation_history", [])
        )
        next_phase = "summary"
    else:
        assistant_reply = propose_next_conversation_turn(
            intake_answers=st.session_state.get("intake_answers", []),
            scratchpad=updated_scratchpad,
            phase="development", # Still in development
            conversation_history=st.session_state.get("conversation_history", [])
        )
        st.session_state["development_turns"] = development_turns + 1
        next_phase = "development"

    return assistant_reply, next_phase

def handle_summary(user_message: str, scratchpad: dict) -> tuple[str, str]:
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    st.session_state["scratchpad"] = updated_scratchpad

    snapshot = {key: updated_scratchpad.get(key, "N/A") for key in [
        "problem", "customer_segment", "solution", "differentiator", "impact_metrics"
    ]}

    teaser = (
        "As you take this idea forward, consider exploring potential revenue streams, "
        "effective channels for reaching your audience, and how to establish a competitive advantage."
    )

    structured_summary = json.dumps(snapshot, indent=2)

    # For the transition from summary to refinement, use propose_next_conversation_turn
    assistant_reply = propose_next_conversation_turn(
        intake_answers=st.session_state.get("intake_answers", []),
        scratchpad=updated_scratchpad, # Pass the most current scratchpad
        phase="refinement", # Transitioning to refinement
        conversation_history=st.session_state.get("conversation_history", [])
    )
    # The structured_summary and teaser can be part of the context for the LLM if needed,
    # or displayed separately in the UI before this LLM-generated prompt.
    # For now, the LLM will generate the next turn based on the scratchpad.
    # We might want to prepend the JSON summary to the assistant_reply if it's crucial for the user to see it *before* the next question.
    # Example:
    # assistant_reply = f"Here's a concise summary of your refined idea:\n\n```json\n{structured_summary}\n```\n\n{teaser}\n\n{llm_proposed_next_turn}"

    next_phase = "refinement"
    return assistant_reply, next_phase

def handle_refinement(user_message: str, scratchpad: dict) -> tuple[str, str]:
    if "new idea" in user_message.lower():
        st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy()
        st.session_state["perplexity_calls"] = 0
        assistant_reply = "Fantastic! Let's start fresh. What's the new idea you'd like to explore?"
        return assistant_reply, "exploration"

    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    st.session_state["scratchpad"] = updated_scratchpad

    # For turns within refinement, or when transitioning from refinement (e.g., to new idea/exploration)
    assistant_reply = propose_next_conversation_turn(
        intake_answers=st.session_state.get("intake_answers", []),
        scratchpad=updated_scratchpad,
        phase="refinement", # Still in refinement, or LLM can suggest moving to exploration
        conversation_history=st.session_state.get("conversation_history", [])
    )
    next_phase = "refinement" # The LLM might guide to a different phase implicitly
    return assistant_reply, next_phase

handle_research = handle_refinement
