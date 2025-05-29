import google.generativeai as genai
import os

def build_prompt(history: list, scratchpad: dict, summaries: list, current_input: str) -> str:
    """
    Builds a comprehensive prompt for the LLM, incorporating conversation history,
    scratchpad content, and summaries to provide rich context.
    """
    prompt_parts = []

    # Add summaries for long-term context
    if summaries:
        prompt_parts.append("--- Summaries of previous turns ---")
        prompt_parts.extend(summaries)
        prompt_parts.append("----------------------------------")

    # Add relevant scratchpad content
    if scratchpad and any(scratchpad.values()):
        prompt_parts.append("--- Current Value Proposition Elements ---")
        for key, value in scratchpad.items():
            if value:
                prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        prompt_parts.append("------------------------------------------")

    # Add recent conversation history
    if history:
        prompt_parts.append("--- Recent Conversation History ---")
        for turn in history[-10:]: # Include last 10 turns for immediate context
            role = "User" if turn["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role}: {turn['text']}")
        prompt_parts.append("-----------------------------------")

    # Add the current user input
    prompt_parts.append(f"User Input: {current_input}")

    # Add instructions for the LLM (e.g., persona, task)
    prompt_parts.append("\nAs a digital health innovation assistant, help the user refine their idea. Focus on the current user input in the context of the conversation history and value proposition elements.")

    return "\n".join(prompt_parts)

def query_gemini(prompt: str, model: str = "gemini-pro") -> str:
    """
    Queries the Gemini LLM with the given prompt and returns the response text.
    Ensures the Google API key is set from environment variables.
    """
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        return "Error: GOOGLE_API_KEY environment variable not set. Please set it to use Gemini."

    try:
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error querying Gemini: {e}"