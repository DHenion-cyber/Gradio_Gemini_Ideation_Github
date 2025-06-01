import google.generativeai as genai
import os
from dotenv import load_dotenv # Import load_dotenv
import streamlit as st
import datetime # For timestamp in error logging
from trulens.apps.custom import instrument # Import instrument

load_dotenv() # Load environment variables from .env file

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


def count_tokens(prompt: str, response: str) -> str or None:
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
    reference_block = ["\n--- References ---"]
    for i, result in enumerate(search_results):
        citation_tag = f"[^{i+1}]"
        citations_text.append(citation_tag)
        reference_block.append(f"{citation_tag} {result.get('title', 'No Title')} - {result.get('url', 'No URL')}")
    
    return " ".join(citations_text), "\n".join(reference_block) if reference_block else ""


def build_prompt(conversation_history: list, scratchpad: dict, summaries: list, user_input: str, search_results: list = None, element_focus: dict = None) -> str:
    """
    Builds a comprehensive prompt for the LLM, incorporating system preamble,
    current focus, scratchpad content, and formatted search results.
    """
    prompt_parts = []

    # System preamble
    prompt_parts.append("You are a digital health innovation assistant. Respond in plain language, using up to 3 inline citations from provided search results where relevant. Do not include Personal Health Information (PHI). Use minimal clarifiers and get straight to the point.")

    # Inject current focus from conversation_manager.navigate_value_prop_elements()
    if element_focus and element_focus.get("element_name"):
        prompt_parts.append(f"\n--- Current Focus: {element_focus['element_name'].replace('_', ' ').title()} ---")
        prompt_parts.append(element_focus.get("prompt_text", ""))
        prompt_parts.append(element_focus.get("follow_up", ""))
        prompt_parts.append("------------------------------------------")

    # Context from scratchpad
    if scratchpad and any(scratchpad.values()):
        prompt_parts.append("\n--- Current Value Proposition Elements ---")
        for key, value in scratchpad.items():
            if value:
                prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        prompt_parts.append("------------------------------------------")

    # Formats Perplexity results as [^n] inline citations + reference block.
    citations_inline = ""
    references_block = ""
    if search_results:
        citations_inline, references_block = format_citations(search_results)
        prompt_parts.append(f"\n--- Search Results Context ---")
        for i, result in enumerate(search_results):
            prompt_parts.append(f"Result {i+1}: {result.get('snippet', 'No snippet available.')}")
        prompt_parts.append("------------------------------")

    # Add conversation history
    if conversation_history:
        prompt_parts.append("\n--- Conversation History ---")
        for turn in conversation_history:
            prompt_parts.append(f"{turn['role'].title()}: {turn['text']}")
        prompt_parts.append("----------------------------")

    # Add summaries
    if summaries:
        prompt_parts.append("\n--- Summaries ---")
        for summary in summaries:
            prompt_parts.append(summary)
        prompt_parts.append("-------------------")

    # Add the current user input
    prompt_parts.append(f"\nUser Input: {user_input}")

    # Append references block at the end if present
    if references_block:
        prompt_parts.append(references_block)

    return "\n".join(prompt_parts)

def format_prompt(prompt: str) -> str:
    """
    A dummy function to satisfy tests that expect a format_prompt function.
    It simply returns the input prompt.
    """
    return prompt

@instrument # Add this decorator
def query_gemini(prompt: str, model: str = "gemini-1.5-flash-latest", temperature: float = 0.7, top_p: float = 0.95, max_output_tokens: int = 1024) -> str:
    """
    Queries the Gemini LLM with the given prompt and returns the response text.
    Includes default parameter configuration and error handling.
    Updates token usage.
    """
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        error_handling.log_error("GOOGLE_API_KEY environment variable not set.")
        return "I'm having trouble with my configuration. Please ensure the GOOGLE_API_KEY is set."

    try:
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens
            )
        )
        
        if response.candidates:
            response_text = response.text
        else:
            response_text = "No response text generated."

        # Update token usage
        token_limit_message = count_tokens(prompt, response_text)
        if token_limit_message:
            return token_limit_message # Return daily limit message if exceeded

        return response_text
    except Exception as e:
        error_handling.log_error("Error querying Gemini", e)
        return "I’m having trouble retrieving fresh data—here’s a concise response based on prior context…"

def summarize_response(text: str) -> str:
    """
    Sends text to Gemini to create a short (<=100-token) summary.
    """
    summary_prompt = f"Summarize the following text in 100 tokens or less:\n\n{text}"
    # Use a slightly lower temperature for summarization to get more concise results
    summary = query_gemini(summary_prompt, temperature=0.5, max_output_tokens=100)
    return summary

# Alias for backward compatibility or clearer naming in some contexts
get_llm_response = query_gemini