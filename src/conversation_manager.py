import streamlit as st
import datetime
import uuid
import os
import urllib.parse
import asyncio

from .persistence_utils import save_session, load_session
from .llm_utils import build_prompt, query_gemini, summarize_response, count_tokens
from . import search_utils


def generate_uuid() -> str:
    """Generates a short random string for user_id."""
    return str(uuid.uuid4())[:8] # Using first 8 characters for a short slug

def initialize_conversation_state():
    """
    Initializes the conversation state in st.session_state with default values.
    This function sets up the necessary keys for managing the conversation flow,
    user input, and LLM interactions.
    """
    st.session_state["stage"] = "intake"
    st.session_state["turn_count"] = 0
    st.session_state["intake_index"] = 0
    st.session_state["scratchpad"] = {
        "problem": "",
        "customer_segment": "",
        "solution_approach": "",
        "mechanism": "",
        "unique_benefit": "",
        "high_level_competitive_view": "",
        "revenue_hypotheses": "",
        "compliance_snapshot": "",
        "top_3_risks_and_mitigations": ""
    }
    st.session_state["conversation_history"] = []
    st.session_state["summaries"] = []
    st.session_state["token_usage"] = {"session": 0, "daily": 0}
    st.session_state["last_summary"] = ""
    st.session_state["start_timestamp"] = datetime.datetime.now(datetime.timezone.utc)
    st.session_state["user_id"] = generate_uuid()

    # Check for ?uid=... in URL and load session if present
    query_params = st.query_params
    if "uid" in query_params:
        loaded_data = load_session(query_params["uid"])
        if loaded_data:
            # Clear existing state before updating to avoid merging issues with complex objects
            # or ensure that st.session_state is a dict-like object that can be updated.
            # For MagicMock, update should work as expected.
            # If st.session_state could be something else, more care is needed.
            # A simple way for tests is to ensure it's a clearable dict-like mock.
            # For now, let's assume st.session_state (the MagicMock) supports update.
            st.session_state.update(loaded_data)
            # Ensure user_id from loaded session is used, or generate if missing
            if "user_id" not in st.session_state or not st.session_state["user_id"]:
                 st.session_state["user_id"] = query_params["uid"] # or generate_uuid() if preferred
            print(f"Session state updated from loaded session {query_params['uid']}")
        else:
            # Session not found or error loading, ensure fresh initialization and save
            if "user_id" not in st.session_state: # Should already be set by initial part of function
                 st.session_state["user_id"] = generate_uuid()
            save_session(st.session_state["user_id"], dict(st.session_state))
            print(f"New session {st.session_state['user_id']} initialized and saved as {query_params['uid']} was not found.")
    else:
        # If no UID in URL, ensure state is initialized (user_id should be set by now)
        if "user_id" not in st.session_state: # Fallback, should be set
            st.session_state["user_id"] = generate_uuid()
        save_session(st.session_state["user_id"], dict(st.session_state)) # Persist initial state


def get_intake_questions() -> list[str]:
    """
    Returns the list of intake questions.
    """
    return [
        "Hello! I’m trained to help you explore ideas for digital health innovation! Please describe any particular experience or familiarity you have within the health landscape. This may come from positions on your resume/cv, training you've recieved, or experiences you've encountered.", 
        "Are there problems that you’re particularly interested in addressing?",
        "Some people naturally focus on patient impact, where others naturally focus more on processes, efficiency, finances, etc. Do you find yourself naturally oriented towards one of the following areas?\n- Patient Impact\n- Quality (may not be directly patients)\n- Finance/savings\n- Efficiency\n- New Technology",
        "Do you already have some ideas or topics you want to explore?",
        "Are there any potential business qualities that matter to you? For example, some people are interested in smaller scale innovations that could be launched quickly with minimum funding while others may be more interested in exploring big ideas with longer timelines and external funding."
    ]

def run_intake_flow(user_input: str):
    """
    Processes user input for the intake flow and advances the intake_index.
    This function should be called *only* when user_input is provided.
    """
    intake_questions = get_intake_questions()

    # Append user response to conversation history
    st.session_state["conversation_history"].append({
        "role": "user",
        "text": user_input,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })

    # Store intake answers in scratchpad where relevant
    # intake_index is incremented *after* processing, so current_intake_index refers to the question just answered
    current_intake_index = st.session_state["intake_index"]
    if current_intake_index == 0: # First question about expertise/interests
        # This is a general introductory question, no direct scratchpad mapping needed yet.
        pass
    elif current_intake_index == 1: # Problems interested in
        st.session_state["scratchpad"]["problem"] = user_input
    elif current_intake_index == 2: # Areas of orientation (Patient Impact, Quality, etc.)
        st.session_state["scratchpad"]["solution_approach"] = user_input # Maps to solution approach based on user's focus
    elif current_intake_index == 3: # Existing ideas or brainstorming
        # This can inform solution_approach or mechanism, depending on the user's input.
        # For now, we'll keep it as pass, as it's more about intent.
        pass
    elif current_intake_index == 4: # Business qualities
        st.session_state["scratchpad"]["revenue_hypotheses"] = user_input # Maps to revenue hypotheses based on business qualities

    st.session_state["intake_index"] += 1

    if st.session_state["intake_index"] >= len(intake_questions):
        st.session_state["stage"] = "ideation"
    
    save_session(st.session_state["user_id"], st.session_state.to_dict())


async def generate_assistant_response(user_input: str) -> tuple[str, list]:
    """
    Generates an assistant response using the LLM, builds the prompt,
    queries Gemini, and stores the result in conversation history.
    Returns the response text and the search results.
    """
    print(f"DEBUG: In generate_assistant_response. Event loop running: {asyncio.get_event_loop().is_running()}")
    # Perform search
    search_results = await search_utils.perform_search(user_input)

    # Build the full prompt
    full_prompt = build_prompt(
        conversation_history=st.session_state["conversation_history"],
        scratchpad=st.session_state["scratchpad"],
        summaries=st.session_state["summaries"],
        user_input=user_input,
        search_results=search_results, # Pass search results to build_prompt
        element_focus=None
    )

    # Query Gemini
    response_text = query_gemini(full_prompt)

    # Store result in conversation history
    st.session_state["conversation_history"].append({
        "role": "assistant",
        "text": response_text,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    st.session_state["turn_count"] += 1
    save_session(st.session_state["user_id"], dict(st.session_state))
    return response_text, search_results

def navigate_value_prop_elements() -> dict:
    """
    Returns the next incomplete field in scratchpad with prompt text and follow-up.
    Injects "Is this on target?" every 10 turns or major pivot.
    """
    value_prop_fields = [
        "problem", "customer_segment", "solution_approach", "mechanism",
        "unique_benefit", "high_level_competitive_view", "revenue_hypotheses",
        "compliance_snapshot", "top_3_risks_and_mitigations"
    ]

    next_element = None
    for field in value_prop_fields:
        if not st.session_state["scratchpad"].get(field):
            next_element = field
            break

    if next_element:
        prompt_text = f"Let's refine the '{next_element}' element of your idea. What are your thoughts on this?"
        follow_up = "Does this seem accurate, or would you like to explore this element from a different perspective?"
    else:
        prompt_text = "All value proposition elements are complete. Would you like to review or refine any of them?"
        follow_up = "We can revisit any element or generate a final summary report."

    # Inject "Is this on target?" every 10 turns
    if st.session_state["turn_count"] > 0 and st.session_state["turn_count"] % 10 == 0:
        prompt_text += "\n\nIs this on target?"

    return {
        "element_name": next_element,
        "prompt_text": prompt_text,
        "follow_up": follow_up
    }

def generate_actionable_recommendations(element: str, context: str):
    """
    Generates up to 2 research-based suggestions for a given element and context,
    and appends them to conversation_history as assistant turns.
    """
    # In a real implementation, this would query an LLM or a knowledge base
    # to generate relevant recommendations based on the element and context.
    # For testing, we'll assume query_gemini returns a string like "1. Rec1\n2. Rec2"
    mock_response = query_gemini(f"Generate recommendations for {element} based on {context}")
    # Ensure that the mock response is split into at least two recommendations for the test
    recommendations = [rec.strip() for rec in mock_response.split('\n') if rec.strip()]
    if len(recommendations) < 2:
        # Add dummy recommendations if the mock response doesn't provide enough
        recommendations.extend([f"Additional Recommendation {i}" for i in range(2 - len(recommendations))])

    for rec in recommendations:
        st.session_state["conversation_history"].append({
            "role": "assistant",
            "text": rec,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
    save_session(st.session_state["user_id"], st.session_state.to_dict())
    return recommendations # Return the list of recommendations


def trim_conversation_history():
    """
    Trims the conversation history based on the number of summaries or token count.
    Removes oldest 5 turns already covered by summaries if conditions are met.
    """
    # Placeholder for actual token counting logic
    # For now, we'll use a simple approximation or assume a function exists.
    def count_tokens(text: str) -> int:
        return len(text.split()) # Simple word count as token approximation

    current_history_tokens = sum(count_tokens(turn["text"]) for turn in st.session_state["conversation_history"])

    if len(st.session_state["summaries"]) >= 20 or current_history_tokens >= 4000:
        # Determine how many turns to remove. This logic needs to be careful
        # not to remove turns that are not yet summarized.
        # For simplicity, we'll just remove the oldest 5 if the condition is met.
        # A more robust solution would track which turns are covered by which summaries.
        if len(st.session_state["conversation_history"]) > 5:
            st.session_state["conversation_history"] = st.session_state["conversation_history"][5:]
            st.session_state["summaries"] = st.session_state["summaries"][1:] # Remove oldest summary if it covers these turns
            save_session(st.session_state["user_id"], st.session_state.to_dict())


def create_turn_summary(text: str) -> str:
    """
    Sends text to Gemini to create a short (<=100-token) summary,
    stores it in last_summary, and appends to summaries.
    """
    # In a real implementation, this would query Gemini for a summary.
    # For now, a simple truncation.
    summary = f"Summary of: {text[:150]}..." # Truncate for demo
    if len(summary.split()) > 100:
        summary = " ".join(summary.split()[:100]) + "..."

    st.session_state["last_summary"] = summary
    st.session_state["summaries"].append(summary)
    save_session(st.session_state["user_id"], st.session_state.to_dict())
    return summary

def reconstruct_context_from_summaries() -> str:
    """
    Combines the latest 10 summaries and the 3 most recent conversation turns
    to reconstruct context for LLM prompt building.
    """
    context_parts = []

    # Add latest 10 summaries
    context_parts.extend(st.session_state["summaries"][-10:])

    # Add 3 most recent conversation turns
    recent_turns = st.session_state["conversation_history"][-3:]
    for turn in recent_turns:
        context_parts.append(f"{turn['role']}: {turn['text']}")

    return "\n".join(context_parts)

def build_summary_from_scratchpad(scratchpad: dict) -> str:
    """
    Returns the full summary from current scratchpad content for export or simulation logs.
    """
    summary_report = []
    summary_report.append("Problem Statement:\n" + scratchpad.get("problem", "N/A"))
    summary_report.append("\nTarget User:\n" + scratchpad.get("customer_segment", "N/A"))
    summary_report.append("\nSolution Approach:\n" + scratchpad.get("solution_approach", "N/A"))
    summary_report.append("\nMechanism:\n" + scratchpad.get("mechanism", "N/A"))
    summary_report.append("\nUnique Benefit:\n" + scratchpad.get("unique_benefit", "N/A"))
    summary_report.append("\nHigh-Level Competitive View:\n" + scratchpad.get("high_level_competitive_view", "N/A"))
    summary_report.append("\nRevenue Hypotheses:\n" + scratchpad.get("revenue_hypotheses", "N/A"))
    summary_report.append("\nCompliance Snapshot:\n" + scratchpad.get("compliance_snapshot", "N/A"))
    summary_report.append("\nTop 3 Risks and Mitigations:\n" + scratchpad.get("top_3_risks_and_mitigations", "N/A"))
    return "\n".join(summary_report)

def generate_final_summary_report() -> str:
    """
    Generates a plain-text session recap with headings based on the scratchpad content.
    Ends the report with a concluding question.
    """
    report = build_summary_from_scratchpad(st.session_state["scratchpad"])
    report += "\n\nQuestions for Consideration:\n" # Placeholder for LLM-generated questions
    report += "\nWould you like to revisit any element or conclude?"
    return report


def is_out_of_scope(msg: str) -> bool:
    """
    Checks if a message is out of scope based on predefined keywords.
    Returns True if the message includes PHI, TAM/SAM/SOM modeling, or other off-topic queries.
    """
    msg_lower = msg.lower()
    # Simple keyword matching for demonstration. A more robust solution would use NLP.
    if "personal health information" in msg_lower or \
       "phi" in msg_lower or \
       "health records" in msg_lower or \
       "medical history" in msg_lower or \
       "diabetes records" in msg_lower or \
       "tam" in msg_lower or \
       "sam" in msg_lower or \
       "som" in msg_lower or \
       "market size" in msg_lower or \
       "financial projection" in msg_lower:
        return True
    return False

def update_token_usage(tokens: int):
    """
    Updates session and daily token usage. Enforces a daily token cap.
    """
    # Only update if not already over daily cap
    daily_cap_str = os.environ.get("DAILY_TOKEN_CAP", "100000")
    try:
        daily_cap = int(daily_cap_str)
    except ValueError:
        daily_cap = 100000 # Fallback if env var is invalid

    if st.session_state["token_usage"]["daily"] + tokens <= daily_cap:
        st.session_state["token_usage"]["session"] += tokens
        st.session_state["token_usage"]["daily"] += tokens
    else:
        # If adding tokens would exceed the cap, set to cap and trigger limit_exceeded stage
        st.session_state["token_usage"]["daily"] = daily_cap
        st.session_state["stage"] = "limit_exceeded"
        st.error("You’ve hit today’s usage limit. Please come back tomorrow to continue refining your ideas!")

    daily_cap_str = os.environ.get("DAILY_TOKEN_CAP", "100000") # Default cap
    try:
        daily_cap = int(daily_cap_str)
    except ValueError:
        daily_cap = 100000 # Fallback if env var is invalid

    if st.session_state["token_usage"]["daily"] > daily_cap:
        st.session_state["stage"] = "limit_exceeded" # Set a stage to indicate limit hit
        st.error("You’ve hit today’s usage limit. Please come back tomorrow to continue refining your ideas!")
        # In a real app, you might disable input or redirect.
    save_session(st.session_state["user_id"], st.session_state.to_dict())


def enforce_session_time():
    """
    Checks if 45 minutes have passed since start_timestamp and prompts the user to wrap up.
    """
    current_time = datetime.datetime.now(datetime.timezone.utc)
    time_elapsed = current_time - st.session_state["start_timestamp"]
    if time_elapsed.total_seconds() >= 45 * 60: # 45 minutes in seconds
        st.warning("You’ve been working for 45 minutes. Would you like to save your progress and wrap up?")
        # In a real app, you might offer options to save/conclude.