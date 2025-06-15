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

    messages = [
        {"role": "system", "content": COACH_SYSTEM_PROMPT},
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

def propose_next_conversation_turn(intake_answers: list, scratchpad: dict, phase: str, conversation_history: list = None) -> str:
    """
    Uses the LLM to propose the next natural conversation turn based on intake, scratchpad, phase, and conversation history.
    Aims for peer coaching, brainstorming, and conversational EQ.
    """
    system_prompt_content = """You are a peer coach brainstorming new digital health innovations with the user. You help them surface promising business ideas by building on any aspect of their prior answers that shows potential, creativity, or relevance.

You are not a therapist, but you are very emotionally intelligent and always bring conversational energy and warmth.

Never just repeat the user’s last answer. Always move the conversation forward, build excitement, and keep things open-ended.

If the user says ‘no’, ‘I don’t know’, or gives a one-word answer, gently prompt them to revisit an earlier idea, suggest a new direction, or validate that it’s normal to feel stuck.

Example interaction:
User: I care about cost savings and rapid deployment.
Assistant: Love it—so quick wins and low friction matter. We could brainstorm ideas for settings where speed makes a huge difference, or dive into ways to get to value quickly. Want to riff on those, or is there another angle you’re curious about?"""

    user_prompt_parts = []
    user_prompt_parts.append(f"Current Conversation Phase: {phase}")

    if intake_answers:
        user_prompt_parts.append("\n--- Intake Answers ---")
        for answer_item in intake_answers:
            # Assuming intake_answers is a list of dicts with a 'text' key or similar
            if isinstance(answer_item, dict) and 'text' in answer_item and answer_item['text']:
                user_prompt_parts.append(f"- {answer_item['text']}")
            elif isinstance(answer_item, str) and answer_item: # Fallback if it's just a list of strings
                user_prompt_parts.append(f"- {answer_item}")
        user_prompt_parts.append("----------------------")

    if scratchpad and any(scratchpad.values()):
        user_prompt_parts.append("\n--- Current Scratchpad ---")
        for key, value in scratchpad.items():
            if value: # Only include items with a value
                user_prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        user_prompt_parts.append("--------------------------")

    if conversation_history:
        user_prompt_parts.append("\n--- Recent Conversation History (last 3 turns) ---")
        # Take last 3 turns, ensure 'role' and 'text' exist
        for turn in conversation_history[-3:]:
            role = turn.get('role', 'unknown').title()
            text = turn.get('text', '')
            if text: # Only add if there's text
                 user_prompt_parts.append(f"{role}: {text}")
        user_prompt_parts.append("----------------------------------------------------")


    user_prompt_parts.append("\n--- Your Task ---")
    user_prompt_parts.append("""Based on all the information above (intake, scratchpad, phase, and recent history):
1. Scan all intake responses and scratchpad fields.
2. Identify 2–3 elements with the most potential, novelty, or relevance to valuable business ideas (considering excitement, user impact, originality, etc.).
3. Briefly express enthusiasm about 1–2 of these elements (e.g., "I love how you mentioned X…" or "It’s cool that you’re interested in Y…").
4. Ask the user if they want to brainstorm more about any of these identified elements, OR suggest a related angle.
5. If previous responses were bland, “no”, or unclear, gently pivot with curiosity, encouragement, or by surfacing something previously mentioned.
6. Never repeat the same phrase or get stuck on a single answer. Never just restate a prior user reply as a question.
7. Always keep the conversation moving naturally, with a friendly, peer-like tone, using mild humor and warmth when appropriate.

--- Example Scenarios ---

Scenario 1: Surfacing multiple elements, peer excitement
Context:
  Intake: "I'm passionate about mental wellness for students." "I think technology can make support more accessible." "Maybe something with AI."
  Scratchpad: Problem_Statement: "Students lack accessible mental wellness resources."
Your Output: "This is great! I'm really picking up on your passion for student mental wellness and the idea of using tech, especially AI, to make support more accessible. That's a super relevant area. Would you like to brainstorm some specific ways AI could play a role here, or perhaps explore different student populations that might see the main benefit most?"

Scenario 2: Handling "no" gracefully, suggesting new angle
Context:
  Recent History:
    Assistant: "...Want to explore AI for personalized coaching or for early detection?"
    User: "No."
Your Output: "No worries at all! Sometimes an idea just doesn't click. How about we pivot a bit? You also mentioned making support 'more accessible' earlier (from intake/scratchpad). That's a big one. We could think about what 'accessible' really means – is it about cost, time, overcoming stigma, or something else? Or, is there another aspect of student mental wellness that's on your mind?"

Scenario 3: Handling bland reply ("Dunno"), encouraging revisit
Context:
  Recent History:
    Assistant: "...Interested in brainstorming around gamification for engagement, or focusing on data privacy?"
    User: "Dunno."
  Intake/Scratchpad contains: "User mentioned unique pressures faced by graduate students."
Your Output: "Hey, it's totally fine to feel a bit unsure – sometimes the best ideas take a little while to surface! You know, earlier you had a really interesting thought about the unique pressures faced by graduate students. Maybe we could circle back to that for a moment? Or, if you're feeling like a completely fresh angle, we can totally do that too!"

--- Now, generate your response for the current user based on their information. ---
What is your proposed next conversational turn?
""")

    full_user_prompt = "\n".join(user_prompt_parts)

    # Using the existing query_openai function structure
    response = client.chat.completions.create(
        model='gpt-4-1106-preview', # Or your preferred model
        messages=[
            {"role": "system", "content": system_prompt_content},
            {"role": "user", "content": full_user_prompt}
        ],
        temperature=0.75, # Slightly higher for more creative/natural conversation
        max_tokens=250    # Increased to allow for more nuanced and example-driven prompts
    )
    return response.choices[0].message.content.strip()
def format_prompt(prompt: str) -> str:
    """
    A dummy function to satisfy tests that expect a format_prompt function.
    It simply returns the input prompt.
    """
    return prompt

def summarize_response(text: str) -> str:
    """
    Sends text to OpenAI to create a short (<=100-token) summary.
    """
    summary_prompt = f"Summarize the following text in 100 tokens or less:\n\n{text}"
    # Use a slightly lower temperature for summarization to get more concise results
    summary = query_openai(messages=[{"role": "user", "content": summary_prompt}], temperature=0.5, max_tokens=100)
    return summary

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