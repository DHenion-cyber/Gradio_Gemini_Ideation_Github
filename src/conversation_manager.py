import streamlit as st
import datetime
import uuid
import os
import asyncio
import logging # Add this import
import random # Added for empathetic statements
import re

from .persistence_utils import save_session, load_session, ensure_db
from .llm_utils import build_prompt, query_openai, propose_next_conversation_turn, generate_contextual_follow_up # Added generate_contextual_follow_up
from . import search_utils
from . import conversation_phases # Added for phase routing
from .utils.scratchpad_extractor import update_scratchpad # Added for scratchpad extraction
from .constants import EMPTY_SCRATCHPAD # Import EMPTY_SCRATCHPAD
from src.coach_persona import COACH_PROMPT
from src.workflows.value_prop import ValuePropWorkflow

WORKFLOWS = {"value_prop": ValuePropWorkflow()}

def generate_uuid() -> str:
    """Generates a short random string for user_id."""
    return str(uuid.uuid4())[:8] # Using first 8 characters for a short slug

def initialize_conversation_state(new_chat: bool = False):
    # Ensure database and tables are created before any session logic
    try:
        logging.info("DEBUG: Calling ensure_db() from initialize_conversation_state.")
        ensure_db()
        logging.info("DEBUG: ensure_db() call completed in initialize_conversation_state.")
    except Exception as e:
        logging.error(f"CRITICAL: Error calling ensure_db() in initialize_conversation_state: {e}")
        # Optionally, re-raise or handle critical failure, e.g., st.error("Database setup failed!")
        # For now, we'll let it proceed and see if subsequent operations fail,
        # as ensure_db() itself logs critical errors.

    """
    Initializes the conversation state in st.session_state.
    - If `new_chat` is True, it creates a completely fresh session.
    - If `new_chat` is False and `conversation_initialized` is True, it assumes
      the state is already correctly managed by a previous run (e.g., after intake completion)
      and does minimal setup, crucially AVOIDING reloading from disk.
    - If `new_chat` is False and `conversation_initialized` is False (e.g., first ever load,
      or load with a UID in URL), it attempts to load or initialize a new session.
    """
    # This check is now primarily for the very first script run or explicit new chat.
    # For reruns where conversation_initialized is True and new_chat is False,
    # we want to trust the existing st.session_state.

    if new_chat:
        logging.info("DEBUG: initialize_conversation_state called with new_chat=True. Creating fresh session.")
        st.session_state["stage"] = "intake"
        st.session_state["turn_count"] = 0
        st.session_state["intake_index"] = 0
        st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy()
        st.session_state["conversation_history"] = []
        st.session_state["summaries"] = []
        st.session_state["token_usage"] = {"session": 0, "daily": 0}
        st.session_state["last_summary"] = ""
        st.session_state["start_timestamp"] = datetime.datetime.now(datetime.timezone.utc)
        st.session_state["user_id"] = generate_uuid()
        st.session_state["maturity_score"] = 0
        st.session_state["perplexity_calls"] = 0
        st.session_state["phase"] = "exploration"
        st.session_state.setdefault("intake_answers", [])
        st.session_state["current_workflow"] = "value_prop"
        st.session_state["conversation_initialized"] = True # Mark as initialized
        save_session(st.session_state["user_id"], dict(st.session_state))
        return # Explicitly return after handling new_chat

    # If not a new_chat, check if it's already initialized (e.g., from a previous script run like intake completion)
    if st.session_state.get("conversation_initialized"):
        logging.info("DEBUG: initialize_conversation_state called with new_chat=False, but conversation_initialized is True. Assuming state is managed, doing minimal setup.")
        # Ensure essential keys have defaults if they were somehow missed, but don't overwrite existing session values.
        st.session_state.setdefault("stage", "intake")
        st.session_state.setdefault("turn_count", 0)
        st.session_state.setdefault("intake_index", 0)
        st.session_state.setdefault("user_id", generate_uuid())
        st.session_state.setdefault("scratchpad", EMPTY_SCRATCHPAD.copy())
        st.session_state.setdefault("conversation_history", [])
        st.session_state.setdefault("summaries", [])
        st.session_state.setdefault("token_usage", {"session": 0, "daily": 0})
        st.session_state.setdefault("last_summary", "")
        st.session_state.setdefault("start_timestamp", datetime.datetime.now(datetime.timezone.utc))
        st.session_state.setdefault("maturity_score", 0)
        st.session_state.setdefault("perplexity_calls", 0)
        st.session_state.setdefault("phase", "exploration")
        st.session_state.setdefault("intake_answers", [])
        return # IMPORTANT: Return here to prevent reloading from disk

    # This part now only runs if new_chat is False AND conversation_initialized is False
    # (i.e., very first load of the app, or first load with a UID in URL)
    logging.info("DEBUG: initialize_conversation_state called with new_chat=False and conversation_initialized is False. Proceeding with load/default init.")
    st.session_state["stage"] = "intake" # Default initial stage
    st.session_state["turn_count"] = 0
    st.session_state["intake_index"] = 0
    
    query_params = st.query_params
    uid_from_url = query_params.get("uid")

    loaded_successfully = False
    if uid_from_url:
        loaded_data = load_session(uid_from_url)
        if loaded_data:
            st.session_state.update(loaded_data)
            if "user_id" not in st.session_state or not st.session_state["user_id"]:
                st.session_state["user_id"] = uid_from_url
            st.session_state.setdefault("intake_answers", []) # Ensure key exists after loading
            loaded_successfully = True
            logging.info(f"DEBUG: Session loaded for user_id {st.session_state.get('user_id')} from UID {uid_from_url}.")

    if not loaded_successfully:
        # Initialize a new session (either no UID, or UID load failed)
        st.session_state["user_id"] = uid_from_url if uid_from_url else generate_uuid()
        st.session_state.setdefault("scratchpad", EMPTY_SCRATCHPAD.copy())
        st.session_state.setdefault("conversation_history", [])
        st.session_state.setdefault("summaries", [])
        st.session_state.setdefault("token_usage", {"session": 0, "daily": 0})
        st.session_state.setdefault("last_summary", "")
        st.session_state.setdefault("start_timestamp", datetime.datetime.now(datetime.timezone.utc))
        st.session_state.setdefault("maturity_score", 0)
        st.session_state.setdefault("perplexity_calls", 0)
        st.session_state.setdefault("phase", "exploration")
        st.session_state.setdefault("intake_answers", [])
        logging.info(f"DEBUG: New session initialized for user_id {st.session_state['user_id']}.")
    
    st.session_state["conversation_initialized"] = True # Mark as initialized
    save_session(st.session_state["user_id"], dict(st.session_state)) # Save whatever state we ended up with


def get_intake_questions() -> list[str]:
    """
    Returns the list of intake questions.
    """
    return [
        "Hello! I’m trained to help you explore ideas for digital health innovation! Please describe any experience or familiarity you have within the health landscape. This may come from positions on your resume, training you've recieved, or experiences you've had.", 
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

    # Store user's intake response in st.session_state["intake_answers"]
    # and not in st.session_state["conversation_history"]
    st.session_state.setdefault("intake_answers", [])
    st.session_state["intake_answers"].append({
        "role": "user",
        "text": user_input,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "meta": "intake" # Mark message as intake-related
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
        st.session_state["scratchpad"]["solution"] = user_input # Mapped to canonical 'solution'
    elif current_intake_index == 3: # Existing ideas or brainstorming
        # This can inform solution or other canonical keys.
        # For now, we'll keep it as pass, as it's more about intent.
        pass
    elif current_intake_index == 4: # Business qualities
        st.session_state["scratchpad"]["revenue_model"] = user_input # Mapped to canonical 'revenue_model'

    st.session_state["intake_index"] += 1

    if st.session_state["intake_index"] >= len(intake_questions):
        st.session_state["stage"] = "ideation"
        # Compute and store best_answer from intake_answers for the transition
        answers_texts = [
            ans.get("text", "")
            for ans in st.session_state.get("intake_answers", [])
            if isinstance(ans, dict)
        ]
        # Ensure answers_texts is not empty for max() to prevent error, default to empty string
        if not answers_texts:
            answers_texts = [""]
        st.session_state["best_intake_answer_for_transition"] = max(answers_texts, key=len, default="")
    
    save_session(st.session_state["user_id"], st.session_state.to_dict())


async def generate_assistant_response(user_input: str) -> tuple[str, list]:
    """
    Generates an assistant response using the LLM, builds the prompt,
    queries Gemini, and stores the result in conversation history.
    Returns the response text and the search results.
    """
    # This patch is to support simulation/test scripts that run without `streamlit run` or UI context.
    # Initialize essential session state keys if they don't exist, providing defaults for simulation.
    st.session_state.setdefault("conversation_history", [])
    st.session_state.setdefault("user_id", generate_uuid()) # Ensure user_id exists
    st.session_state.setdefault("scratchpad", EMPTY_SCRATCHPAD.copy())
    st.session_state.setdefault("summaries", [])
    st.session_state.setdefault("token_usage", {"session": 0, "daily": 0})
    st.session_state.setdefault("last_summary", "")
    st.session_state.setdefault("start_timestamp", datetime.datetime.now(datetime.timezone.utc))
    st.session_state.setdefault("maturity_score", 0)
    st.session_state.setdefault("perplexity_calls", 0)
    st.session_state.setdefault("phase", "exploration") # Default phase for simulation
    st.session_state.setdefault("module", "default_module") # Default module for simulation
    st.session_state.setdefault("turn_count", 0) # Ensure turn_count exists

    print(f"DEBUG: In generate_assistant_response. Event loop running: {asyncio.get_event_loop().is_running()}")
    
    search_results = [] # Initialize with no results
    perform_web_search = False
    user_input_lower = user_input.lower()
    search_keywords = ["search for", "research", "find information on", "look up", "what is", "who is", "tell me about"] # Add more as needed

    # Condition 1: User explicitly requests search
    if any(keyword in user_input_lower for keyword in search_keywords):
        perform_web_search = True
        print("DEBUG: User explicitly requested search.")

    # Condition 2: Current phase is 'refinement' and a missing fact is identified (placeholder for missing fact logic)
    current_phase = st.session_state.get("phase", "exploration")
    if current_phase == "refinement":
        # TODO: Implement robust "missing fact" identification logic.
        # For now, we can assume if in refinement and not an explicit search,
        # a simple heuristic might be to search if the user asks a question.
        # This is a placeholder and should be improved.
        if "?" in user_input and not perform_web_search: # Simple heuristic: user asks a question
            perform_web_search = True
            print("DEBUG: Performing search in refinement phase (heuristic: user asked a question).")
        elif not perform_web_search: # If no explicit search and not a question, maybe still search sometimes?
             # This part needs careful consideration to avoid over-searching.
             # For now, let's be conservative and only search on explicit request or question in refinement.
             pass


    if perform_web_search:
        # Check research cap BEFORE attempting search
        current_calls = st.session_state.get("perplexity_calls", 0)
        if current_calls < search_utils.MAX_PERPLEXITY_CALLS:
            # Check API key BEFORE incrementing calls or attempting search
            perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
            if perplexity_api_key:
                st.session_state["perplexity_calls"] = current_calls + 1
                print(f"DEBUG: Performing Perplexity search for: {user_input}. Call count: {st.session_state['perplexity_calls']}")
                search_results = await search_utils.perform_search(user_input)
            else:
                print("DEBUG: PERPLEXITY_API_KEY not set. Skipping search.")
                # Optionally, inform the user or return a specific message via search_results
        else:
            print(f"DEBUG: Perplexity call cap reached ({st.session_state.get('perplexity_calls', 0)}). Skipping search.")
            # Optionally, inform the user that the search cap has been reached.
            # search_results can remain empty or carry a message.

    # Build the full prompt
    full_prompt = build_prompt(
        conversation_history=st.session_state["conversation_history"],
        scratchpad=st.session_state["scratchpad"],
        summaries=st.session_state["summaries"],
        user_input=user_input,
        phase=st.session_state["phase"], # Pass the current phase
        search_results=search_results, # Pass search results to build_prompt
        element_focus=None
    )

    # Check for empathetic trigger phrases
    empathetic_prepend = ""
    empathy_keywords = ["i'm struggling", "i always ignore", "i'm frustrated"]
    if any(keyword in user_input.lower() for keyword in empathy_keywords):
        empathetic_statements = [
            "It sounds like things are a bit tough right now, and that's completely understandable. ",
            "I hear you; it can be really challenging when you're feeling that way. ",
            "Thanks for sharing that; it takes courage to acknowledge those feelings. "
        ]
        empathetic_prepend = random.choice(empathetic_statements)

    # Query Gemini for main advice
    main_advice_text = query_openai(full_prompt)

    # Generate contextual follow-up question
    follow_up_question = ""
    if main_advice_text: # Only generate if there's main advice
        follow_up_question = generate_contextual_follow_up(main_advice_text)

    # Combine response parts
    final_response_text = f"{empathetic_prepend}{main_advice_text}"
    if follow_up_question:
        final_response_text += f" {follow_up_question}"


    # Store result in conversation history
    st.session_state["conversation_history"].append({
        "role": "assistant",
        "text": final_response_text, # Store the combined response
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    st.session_state["turn_count"] += 1
    save_session(st.session_state["user_id"], dict(st.session_state))
    return final_response_text, search_results

def route_conversation(user_message: str, scratchpad: dict) -> tuple[str, str]:
    """
    Routes the conversation to the appropriate handler based on the current phase.

    Args:
        user_message: The user's latest message.
        scratchpad: The current scratchpad data.

    Returns:
        A tuple containing the assistant's reply and the next phase.
    """
    # Update scratchpad at the top of route_conversation before phase helpers
    st.session_state["scratchpad"] = update_scratchpad(user_message, st.session_state["scratchpad"])

    current_phase = st.session_state.get("phase", "exploration")  # Default to exploration

    cw = st.session_state.get("current_workflow")
    if cw in WORKFLOWS:
        assistant_reply, new_phase = WORKFLOWS[cw].step(user_message, st.session_state["scratchpad"])
        st.session_state["phase"] = new_phase
        return assistant_reply, new_phase
# Check for affirmative response in exploration phase to confirm value prop
    if current_phase == "exploration" and user_message and re.search(r"\b(yes|that.?s it|correct|sounds good)\b", user_message, re.I):
        # Ensure scratchpad exists in session_state, though it should by this point.
        if "scratchpad" not in st.session_state:
            st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy() # Or some other default
        
        # The 'scratchpad' variable passed into this function might be a copy or stale.
        # It's safer to update st.session_state["scratchpad"] directly as it's the source of truth.
        st.session_state["scratchpad"]["value_prop_confirmed"] = True
        # No need to update the local `scratchpad` variable here as it might not propagate as expected.
        # The `handle_exploration` function will read from st.session_state["scratchpad"].
    assistant_reply = "An unexpected error occurred." # Default reply
    next_phase = current_phase # Default next_phase

    # Check if this is the initial call for the exploration phase after intake
    if not user_message and current_phase == "exploration" and st.session_state.get("stage") == "ideation":
        # This is the transition from intake to ideation (exploration phase starts here)
        # Remove the marker that was set at the end of intake
        st.session_state.pop("best_intake_answer_for_transition", None)

        # Remove any existing "maturity-score" or similar system message if present
        if st.session_state.get("conversation_history"):
            # This cleanup might be better handled in streamlit_app.py when transitioning stages
            pass

        assistant_reply = propose_next_conversation_turn(
            intake_answers=st.session_state.get("intake_answers", []),
            scratchpad=st.session_state.get("scratchpad", EMPTY_SCRATCHPAD.copy()),
            phase=current_phase, # Should be "exploration"
            conversation_history=st.session_state.get("conversation_history", [])
        )
        # The phase remains "exploration" as this is the first turn of exploration
        next_phase = "exploration"
        # The calling function in streamlit_app.py will append this to history.
        save_session(st.session_state["user_id"], dict(st.session_state))
        return assistant_reply, next_phase

    if current_phase == "exploration":
        assistant_reply, next_phase = conversation_phases.handle_exploration(user_message, st.session_state["scratchpad"])
    elif current_phase == "development":
        assistant_reply, next_phase = conversation_phases.handle_development(user_message, st.session_state["scratchpad"])
    elif current_phase == "refinement":
        assistant_reply, next_phase = conversation_phases.handle_refinement(user_message, st.session_state["scratchpad"])
    elif current_phase == "summary":
        assistant_reply, next_phase = conversation_phases.handle_summary(user_message, st.session_state["scratchpad"])
    else:
        # Fallback for unknown phase
        assistant_reply = f"Debug: Unknown phase '{current_phase}'. Resetting to exploration."
        next_phase = "exploration"
        st.session_state["phase"] = "exploration" # Explicitly reset

    # Update phase in session state after getting the reply and next_phase
    st.session_state["phase"] = next_phase
    
    # Note: The research cap (MAX_PERPLEXITY_CALLS) logic is intended to be
    # implemented within the specific phase handler functions in 
    # conversation_phases.py if they call search_utils.search_perplexity.
    # Example placeholder for this is in conversation_phases.handle_exploration.

    # Append user message and assistant reply to conversation history
    # This might be handled by the calling function (e.g., in streamlit_app.py)
    # or could be centralized here if route_conversation is the primary entry point
    # for generating all non-intake replies. For now, assuming the calling function handles history.

    save_session(st.session_state["user_id"], dict(st.session_state)) # Persist state changes
    return assistant_reply, next_phase
# Deleted navigate_value_prop_elements function

def generate_actionable_recommendations(element: str, context: str):
    """
    Generates up to 2 research-based suggestions for a given element and context,
    and appends them to conversation_history as assistant turns.
    """
    # In a real implementation, this would query an LLM or a knowledge base
    # to generate relevant recommendations based on the element and context.
    # For testing, we'll assume query_openai returns a string like "1. Rec1\n2. Rec2"
    mock_response = query_openai(f"Generate recommendations for {element} based on {context}")
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
    summary_report.append("\nCustomer Segment:\n" + scratchpad.get("customer_segment", "N/A"))
    summary_report.append("\nSolution:\n" + scratchpad.get("solution", "N/A"))
    summary_report.append("\nDifferentiator:\n" + scratchpad.get("differentiator", "N/A"))
    summary_report.append("\nImpact Metrics:\n" + scratchpad.get("impact_metrics", "N/A"))
    summary_report.append("\nRevenue Model:\n" + scratchpad.get("revenue_model", "N/A"))
    summary_report.append("\nChannels:\n" + scratchpad.get("channels", "N/A"))
    summary_report.append("\nCompetitive Moat:\n" + scratchpad.get("competitive_moat", "N/A"))
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
    import re # Add import for regular expressions
    msg_lower = msg.lower()
    # Simple keyword matching for demonstration. A more robust solution would use NLP.
    out_of_scope_keywords = [
        "personal health information", "phi", "pii",
        "health records", "medical history", "diabetes records",
        "privacy policy", "health data",
        "tam", "sam", "som", "market size", "financial projection"
    ]
    
    short_sensitive_keywords = ["phi", "pii", "tam", "sam", "som"]

    for keyword in out_of_scope_keywords:
        if keyword in short_sensitive_keywords:
            # Use regex word boundaries for short, sensitive keywords
            # \b ensures that the keyword is a whole word
            pattern = r"\b" + re.escape(keyword) + r"\b"
            match = re.search(pattern, msg_lower)
            if match:
                return True
        elif keyword in msg_lower: # For longer, less ambiguous keywords
            return True
    
    # If none of the out-of-scope keywords are found, the message is considered in-scope.
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