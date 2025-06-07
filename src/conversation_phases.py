import streamlit as st
from .utils.scratchpad_extractor import update_scratchpad
from .constants import EMPTY_SCRATCHPAD, CANONICAL_KEYS
import json

def extract_best_idea(scratchpad: dict, intake_answers: list) -> str:
    """
    Review all prior user inputs (intake + scratchpad) to select the statement with the most potential, clarity, or emphasis.
    """
    candidates = []
    # Prioritize solution and problem (if substantive)
    for key in ["solution", "problem"]:
        value = scratchpad.get(key, "")
        if value and len(value.strip()) > 20:
            candidates.append(value.strip())
    # Search intake answers for the longest, most idea-like answer
    for ans in intake_answers:
        text = ans.get("text", "")
        if text and len(text.strip()) > 20:
            candidates.append(text.strip())
    # Return the longest (proxy for most substantial/idea-like)
    return max(candidates, key=len, default="your idea")

def generate_prompt(prompt_type: str, scratchpad: dict, intake_answers: list) -> str:
    best_idea = extract_best_idea(scratchpad, intake_answers)
    if prompt_type == "exploration":
        return (
            f"Let's explore your idea: \"{best_idea}\". "
            "What possible directions, uses, or user groups come to mind, or would you like to brainstorm some possibilities together?"
        )
    elif prompt_type == "development":
        return (
            f"Now that we've narrowed in on \"{best_idea}\", "
            "which aspect would you like to flesh out next—such as the core benefit, who it helps most, or how it could work in practice?"
        )
    return "Tell me more about your thoughts."

def handle_exploration(user_message: str, scratchpad: dict) -> tuple[str, str]:
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    st.session_state["scratchpad"] = updated_scratchpad

    exploration_turns = st.session_state.get("exploration_turns", 0)
    intake_answers = st.session_state.get("intake_answers", [])

    # After several exploration turns, check readiness to move to development
    if exploration_turns >= 4 and any(word in user_message.lower() for word in ["ready", "next", "move forward", "develop", "yes"]):
        st.session_state["exploration_turns"] = 0  # reset for next phase
        assistant_reply = "Great! Let's start organizing and refining your ideas further. Which specific aspect should we delve into first?"
        next_phase = "development"
    else:
        assistant_reply = generate_prompt("exploration", updated_scratchpad, intake_answers)
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
        assistant_reply = "You've developed a solid foundation! Let's review and summarize everything we've discussed."
        next_phase = "summary"
    else:
        assistant_reply = generate_prompt("development", updated_scratchpad, intake_answers)
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

    assistant_reply = (
        f"Here's a concise summary of your refined idea:\n\n```json\n{structured_summary}\n```\n\n{teaser} "
        "Would you like to refine any of these further or explore a new idea?"
    )

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

    assistant_reply = (
        "Let's refine your idea further. Is there a particular aspect you'd like to expand on or clarify more deeply?"
    )
    next_phase = "refinement"
    return assistant_reply, next_phase

handle_research = handle_refinement
