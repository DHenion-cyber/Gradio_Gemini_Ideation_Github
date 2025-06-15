import streamlit as st
from .utils.scratchpad_extractor import update_scratchpad
from .constants import EMPTY_SCRATCHPAD, CANONICAL_KEYS
from .llm_utils import query_openai, propose_next_conversation_turn, build_conversation_messages
from .value_prop_workflow import ValuePropWorkflow # Import ValuePropWorkflow
import json
import textwrap
# Updated CHECKLIST to align with new scratchpad keys
CHECKLIST = ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]
def missing_items(sp):
    return [k for k in CHECKLIST if not sp.get(k)]
EXPLORATION_PROMPT = textwrap.dedent("""
You are a strategy coach. The ONLY goal of the exploration phase
is to lock in a concise VALUE PROPOSITION:

• problem (one line)
• target_customer
• proposed solution
• one measurable main benefit
• differentiator
• use_case

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
    # Value prop elements and contextual_user_message construction (lines 64-90)
    # are removed as build_conversation_messages now handles context creation.
    # The EXPLORATION_PROMPT is also no longer directly passed to this LLM call.

    try:
        # Assuming query_openai returns the assistant's message text directly.
        # Adjust if it returns a more complex object.
        messages_for_llm = build_conversation_messages(
            scratchpad=updated_scratchpad,
            latest_user_input=user_message,
            current_phase="exploration"  # Phase for build_conversation_messages
        )
        assistant_reply = query_openai(messages=messages_for_llm)
        if not assistant_reply or not assistant_reply.strip():
            assistant_reply = "I'm processing that. Could you tell me a bit more, or perhaps we can explore another angle?"
            # Log this occurrence for debugging
            st.warning("LLM returned an empty or whitespace-only response in exploration phase.")
            print("DEBUG: LLM returned empty/whitespace response in handle_exploration.")
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
    needed = missing_items(scratchpad)
    if needed:
        next_item = needed[0]
        prompts = {
            "problem": "What single problem are we solving?",
            "target_customer": "Who feels that pain the most?", # Changed to target_customer
            "solution": "Describe the one-sentence solution.",
            "main_benefit": "What core benefit or metric proves value?", # Changed back to main_benefit
            "use_case": "How do you envision people using your solution in real-world scenarios?"
        }
        return prompts[next_item], "development"
    else:
        return "Great, let's refine wording.", "refinement"

def handle_summary(user_message: str, scratchpad: dict, vp_workflow_instance: ValuePropWorkflow = None) -> tuple[str, str]:
    assistant_reply = ""
    next_phase = "summary" # Default to stay in summary phase

    if vp_workflow_instance and vp_workflow_instance.is_complete():
        # generate_summary() now returns the full, formatted string including recommendations
        assistant_reply = vp_workflow_instance.generate_summary()
        
        # Append interaction prompts based on user_message
        if user_message:
            user_message_lower = user_message.lower()
            if any(kw in user_message_lower for kw in ["yes", "correct", "looks good", "proceed", "next"]):
                # User confirms summary, perhaps offer to refine or end.
                # For now, let's assume this means they are ready to move on from the summary.
                # The UI/streamlit_app.py will handle final feedback prompts.
                # We can transition to a conceptual "post_summary" or "end" phase if needed,
                # or simply let the UI handle the next steps.
                # For now, let's keep it simple and stay in "summary" but indicate completion.
                assistant_reply += "\n\nThis concludes the value proposition development. You can review the summary and recommendations. What would you like to do next? (e.g., start a new idea, or provide feedback on this session)"
                # next_phase could be 'refinement' if we want to allow further iteration,
                # or a new phase like 'conclusion'. For now, stay in 'summary'.
            elif any(kw in user_message_lower for kw in ["no", "change", "edit", "revisit"]):
                assistant_reply += "\n\nWhat part would you like to revisit or change? We can go back to any step of the value proposition."
                # To allow revisiting, we might need to reset vp_workflow_instance.completed = False
                # and set its current_step. This is more complex than current scope.
                # For now, we'll just acknowledge.
            else: # General comment on summary
                 assistant_reply += "\n\nThanks for your feedback. You can review the summary and recommendations. What would you like to do next?"
        else: # No user message, just presenting the summary
            assistant_reply += "\n\nDoes this capture your idea? You can ask to refine any part, or we can conclude this section."

    else:
        # Fallback if vp_workflow_instance is not available or not complete (should not happen if logic in conversation_manager is correct)
        assistant_reply = "I'm ready to generate a summary, but it seems the value proposition isn't fully complete yet. "
        # Ensure the checklist items here match the updated CHECKLIST
        assistant_reply += f"Let's ensure all steps ({', '.join(CHECKLIST)}) are covered."
        # Attempt to find the current step from scratchpad if VP workflow failed.
        # This is a defensive measure.
        missing = missing_items(scratchpad) # missing_items uses the updated CHECKLIST
        if missing:
            next_phase = missing[0] # Try to go back to the first missing step
            assistant_reply += f" It looks like we still need to define the '{next_phase}'. Shall we work on that?"
        else: # All items seem present in scratchpad, but workflow isn't complete.
            next_phase = "exploration" # Fallback to general exploration
            assistant_reply += " Let's try to refine the value proposition."


    # The old logic for transitioning to "refinement" via propose_next_conversation_turn
    # is removed as the ValuePropWorkflow now handles the ideation flow.
    # The 'summary' phase is now more about presenting the completed VP.
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
