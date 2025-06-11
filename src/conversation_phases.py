import streamlit as st
from .utils.scratchpad_extractor import update_scratchpad
from .constants import EMPTY_SCRATCHPAD, CANONICAL_KEYS
from .llm_utils import query_openai, propose_next_conversation_turn # Import query_openai and propose_next_conversation_turn
import json
import textwrap
EXPLORATION_PROMPT = textwrap.dedent("""
You are a strategy coach. The ONLY goal of the exploration phase
is to lock in a concise VALUE PROPOSITION:

• problem (one line)
• target user
• proposed solution
• one measurable core benefit

Rules:
1. Give a MAXIMUM of **one** short acknowledgment sentence.
2. Ask **one** focused question to fill the FIRST missing slot.
3. If all four slots are already answered, RESTATE the value prop in
   ≤50 words, ask “Is this correct?” and stop brainstorming.
4. No features or rabbit holes until the value prop is confirmed.
""").strip()

def handle_exploration(user_message: str, scratchpad: dict) -> tuple[str, str]:
    if scratchpad.get("value_prop_confirmed"):
        return "", "development"
    # Existing scratchpad update can remain if it's generally useful
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    st.session_state["scratchpad"] = updated_scratchpad

    # Construct the messages for the LLM call using the new EXPLORATION_PROMPT
    # The conversation history should be managed carefully here.
    # For this specific prompt, we might not need extensive history,
    # but rather the current user_message and the scratchpad contents.

    # For simplicity, let's assume the EXPLORATION_PROMPT is a system message
    # and the user_message is the user's latest input.
    # The llm_utils.query_openai function needs to be adapted or a new one created
    # if it doesn't directly support this structure or the new prompt's rules.
    # For now, I'll use query_openai as it's available.
    
    # We need to build a history or context for the LLM.
    # The EXPLORATION_PROMPT itself defines the persona and task.
    # We should pass the current user_message and relevant scratchpad info.
    
    # Simplified context for the LLM based on the new prompt's focus:
    # The prompt implies the LLM should look at the scratchpad for value prop elements.
    
    # Let's prepare the input for the LLM based on the new prompt's rules.
    # The prompt is quite specific about how the LLM should behave.
    
    # The `query_openai` function is imported but its signature is not visible here.
    # Assuming it takes a list of messages (system, user, assistant).
    
    # Create a representation of the current value proposition from the scratchpad
    # to help the LLM follow Rule 3.
    value_prop_elements = {
        "problem": updated_scratchpad.get("problem", "Not yet defined"),
        "target user": updated_scratchpad.get("customer_segment", "Not yet defined"),
        "proposed solution": updated_scratchpad.get("solution", "Not yet defined"),
        "core benefit": updated_scratchpad.get("value_proposition", "Not yet defined") # Corrected key from CANONICAL_KEYS
    }
    
    # Construct a user message that includes the current state for the LLM
    # This is a way to feed current state to the LLM if it doesn't directly access scratchpad
    contextual_user_message = f"""
Current User Input: {user_message}

Current Value Proposition Status:
- Problem: {value_prop_elements['problem']}
- Target User: {value_prop_elements['target user']}
- Proposed Solution: {value_prop_elements['proposed solution']}
- Core Benefit: {value_prop_elements['core benefit']}
"""

    messages = [
        {"role": "system", "content": EXPLORATION_PROMPT},
        {"role": "user", "content": contextual_user_message.strip()}
    ]

    try:
        # Assuming query_openai returns the assistant's message text directly.
        # Adjust if it returns a more complex object.
        assistant_reply = query_openai(messages=messages) # Removed phase="exploration"
    except Exception as e:
        st.error(f"Error querying LLM in exploration: {e}")
        assistant_reply = "I encountered an issue. Could you please try rephrasing?"

    # The phase remains "exploration" unless the LLM indicates a change or rules are met.
    # The new prompt's Rule 3 implies the LLM itself handles the "Is this correct?" part.
    # The `value_prop_confirmed` flag will be set by `route_conversation` in `conversation_manager.py`
    # based on user's affirmative response.
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
