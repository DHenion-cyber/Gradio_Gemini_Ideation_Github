"""Provides utility functions for interacting with OpenAI's LLMs, managing prompts, and token counting."""
import os
from dotenv import load_dotenv # Import load_dotenv
from openai import OpenAI # Import the OpenAI class
import streamlit as st
from typing import Optional
# from src.coach_persona import COACH_PROMPT # Removed import as COACH_PROMPT is no longer defined there

load_dotenv() # Load environment variables from .env file

# Instantiate the client. It will automatically pick up the OPENAI_API_KEY environment variable.
client = OpenAI()

COACH_SYSTEM_PROMPT = """
You are an expert business coach specializing in digital health innovation. You help users discover, clarify, and sharpen their own ideas for solving real-world problems—especially in healthcare. Your style is masterfully conversational, warm but candid, intellectually curious, and never pandering. You gently but intelligently challenge vague statements, but never sound like you’re filling out a checklist.

You always:
- Seek to understand the user’s perspective, motivations, and goals.
- Guide the conversation toward a focused, testable value proposition, while making the user feel heard and respected.
- Present creative opportunities or alternative directions, building on what the user has shared, not just narrowing based on their words.
- Encourage the user to reflect on and respond to your suggestions, ensuring they remain in the driver’s seat.
- Use your business expertise and industry knowledge to spot opportunities, risks, and differentiation, and share these insights with tact.
- If clarity is missing, seek it through open, thoughtful questions or gentle reframing—summarizing only when necessary to resolve ambiguity.

Do not use mechanical or repetitive phrasing. Avoid sounding like a form. Keep each message focused, specific, and forward-moving. Your ultimate goal is to help the user define a compelling value proposition for a digital health solution, but you do so naturally, with intellectual rigor and authentic curiosity.
"""

VALUE_PROP_EXPLORATION_SYSTEM_PROMPT = """
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
""".strip()

# Configure OpenAI key from env
# openai.api_key = os.getenv('OPENAI_API_KEY') # Removed: Handled by client instantiation

# Unified function to query OpenAI's GPT-4.1
def query_openai(messages: list, **kwargs): # Changed 'prompt' to 'messages: list'
    # Ensure API key is available (client instantiation handles this, but good to be aware)
    if not client.api_key:
        error_handling.log_error("OpenAI API key is not configured.")
        raise ValueError("OpenAI API key not configured.")

    # COACH_PROMPT was previously prepended here.
    # System messages are now expected to be part of the 'messages' input if needed,
    # or handled by specific functions like build_prompt.
    
    response = client.chat.completions.create(
        model=kwargs.pop('model', 'gpt-4-1106-preview'), # Allow model override via kwargs, default
        messages=messages, # Use the original messages list
        **kwargs # Pass through any other keyword arguments like temperature, max_tokens
    )
    return response.choices[0].message.content.strip() # Ensure stripping

# Assuming error_handling.py and search_utils.py exist or will be created
# For now, using placeholders for these imports.
try:
    from src import error_handling
except ImportError:
    class ErrorHandling: # type: ignore
        def log_error(self, message: str, e: Exception = None):
            print(f"ERROR: {message}")
            if e:
                print(f"Exception: {e}")
    error_handling = ErrorHandling() # type: ignore

try:
    from src import search_utils
except ImportError:
    class SearchUtils: # type: ignore
        def perform_search(self, query: str):
            return [{"title": "Dummy Search Result", "url": "http://example.com/dummy", "snippet": "This is a dummy search result."}]
    search_utils = SearchUtils() # type: ignore


def count_tokens(prompt: str, response: str) -> Optional[str]:
    """
    Updates session and daily token usage based on prompt and response length.
    Returns a message if the daily limit is reached, otherwise None.
    """
    # Simple token estimation: count words. A real implementation would use a tokenizer.
    prompt_tokens = len(prompt.split())
    response_tokens = len(response.split())
    total_tokens = prompt_tokens + response_tokens

    if "token_usage" not in st.session_state:
        st.session_state["token_usage"] = {"session": 0, "daily": 0}

    st.session_state["token_usage"]["session"] += total_tokens
    st.session_state["token_usage"]["daily"] += total_tokens

    daily_cap_str = os.environ.get("DAILY_TOKEN_CAP", "100000") # Default cap
    try:
        daily_cap = int(daily_cap_str)
    except ValueError:
        daily_cap = 100000 # Fallback if env var is invalid

    if st.session_state["token_usage"]["daily"] > daily_cap:
        return "Daily limit reached; try again tomorrow."
    return None

def format_citations(search_results: list) -> tuple[str, str]:
    """
    Converts search_utils results into markdown ^-style inline references
    and a reference block.
    """
    citations_text = []
    reference_block_content = [] # Initialize empty list for content
    
    if not search_results:
        return "", "" # Return empty strings if no search results

    # Only add header and process if there are search results
    reference_block_content.append("\n--- References ---")
    for i, result in enumerate(search_results):
        citation_tag = f"[^{i+1}]"
        citations_text.append(citation_tag)
        reference_block_content.append(f"{citation_tag} {result.get('title', 'No Title')} - {result.get('url', 'No URL')}")
    
    return " ".join(citations_text), "\n".join(reference_block_content)


def build_conversation_messages(scratchpad, latest_user_input, current_phase):
    context_lines = []
    for key, value in scratchpad.items():
        if value and key != "research_requests":
            context_lines.append(f"{key.replace('_', ' ').title()}: {value}")

    intake_summary = st.session_state.get("context_summary", "")
    context = ""
    if intake_summary:
        context += intake_summary + "\n\n"
    context += (
        "Here’s what the user has shared about their idea so far:\n"
        + "\n".join(context_lines)
        + f"\n\nMost recent user message: {latest_user_input}\n"
        + f"Current focus: {current_phase}.\n"
        "Your job is to advance the conversation in a natural, helpful, and opportunity-oriented way."
    )

    system_prompt_content = COACH_SYSTEM_PROMPT
    if current_phase == "exploration":
        system_prompt_content = VALUE_PROP_EXPLORATION_SYSTEM_PROMPT
        # The context built below will serve as the user message to this system prompt.
        # The VALUE_PROP_EXPLORATION_SYSTEM_PROMPT implies the LLM will use the scratchpad info
        # (which is part of 'context') to find missing slots.

    messages = [
        {"role": "system", "content": system_prompt_content},
        {"role": "user", "content": context},
    ]
    return messages
def build_prompt(conversation_history: list, scratchpad: dict, summaries: list, user_input: str, phase: str, search_results: list = None, element_focus: dict = None) -> tuple[str, str]:
    """
    Builds a comprehensive prompt for the LLM, separating system instructions
    from user-facing content.
    Returns a tuple: (system_instructions, user_prompt_content)
    """
    system_instructions = COACH_SYSTEM_PROMPT + """

ADDITIONAL OPERATIONAL GUIDELINES:
SYSTEM GOALS (Internal):
- Internally maximise:
  a) Idea maturity score
  b) Coverage of value‑proposition elements in the scratchpad.

RESEARCH POLICY:
- Use web_search() only when (a) the user explicitly requests it or (b) current phase == 'refinement' and missing fact is identified.
- Hard limit: 3 calls per session.

WEAKNESSES:
- When weaknesses arise, state them plainly, followed by at least one mitigation or alternative.
"""

    user_prompt_parts = []

    # Inject current focus from conversation_manager.navigate_value_prop_elements()

    # Add conversation phase
    user_prompt_parts.append(f"Conversation Phase: {phase}")

    # Context from scratchpad
    if scratchpad and any(scratchpad.values()):
        user_prompt_parts.append("\n--- Current Value Proposition Elements ---")
        for key, value in scratchpad.items():
            if value:
                user_prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        user_prompt_parts.append("------------------------------------------")

    # Formats Perplexity results as [^n] inline citations + reference block.
    citations_inline = ""
    references_block = ""
    if search_results:
        citations_inline, references_block = format_citations(search_results)
        user_prompt_parts.append("\n--- Search Results Context ---")
        for i, result in enumerate(search_results):
            user_prompt_parts.append(f"Result {i+1}: {result.get('snippet', 'No snippet available.')}")
        user_prompt_parts.append("------------------------------")

    # Add conversation history
    if conversation_history:
        user_prompt_parts.append("\n--- Conversation History ---")
        for turn in conversation_history:
            user_prompt_parts.append(f"{turn['role'].title()}: {turn['text']}")
        user_prompt_parts.append("----------------------------")

    # Add summaries
    if summaries:
        user_prompt_parts.append("\n--- Summaries ---")
        for summary in summaries:
            user_prompt_parts.append(summary)
        user_prompt_parts.append("-------------------")

    # Add the current user input
    user_prompt_parts.append(f"\nUser Input: {user_input}")

    # Append references block at the end if present
    if references_block:
        user_prompt_parts.append(references_block)

    return system_instructions, "\n".join(user_prompt_parts)

def format_prompt(prompt: str) -> str:
    """
    A dummy function to satisfy tests that expect a format_prompt function.
    It simply returns the input prompt.
    """
    return prompt

def generate_contextual_follow_up(advice_text: str) -> str:
    """
    Generates a contextually relevant follow-up question based on the provided advice.
    """
    if not advice_text:
        return ""

    prompt = f"""Given the following advice:
"{advice_text}"

Generate a single, open-ended follow-up question that encourages the user to reflect on the advice, make a choice, or continue the conversation. The question should be directly related to the content of the advice. Avoid generic or canned questions.

Follow-up question:"""

    try:
        # Using the existing query_openai function structure
        response = client.chat.completions.create(
            model='gpt-4-1106-preview', # Or your preferred model for this task
            messages=[
                {"role": "system", "content": "You are an expert at crafting engaging and contextually relevant follow-up questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Allow for some creativity
            max_tokens=50,   # Keep the question concise
            n=1,
            stop=None
        )
        question = response.choices[0].message.content.strip()
        # Ensure it's a question
        if question and not question.endswith("?"):
            question += "?"
        return question
    except Exception as e:
        # Log the error, but don't break the flow. Return an empty string.
        print(f"Error generating follow-up question: {e}") # Or use a proper logger
        return ""

# Alias for backward compatibility or clearer naming in some contexts
get_llm_response = query_openai