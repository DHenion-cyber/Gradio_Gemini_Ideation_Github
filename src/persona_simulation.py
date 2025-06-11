import os
from openai import OpenAI

PERSONA_PROFILE = {
    "name": "Pat Morgan",
    "background": "Hospital admin, 15 years managing imaging departments.",
    "goal": "Deploy a patient-facing chatbot to streamline appointment scheduling and navigation for in-person care.",
    "constraints": "Bootstrap, avoid external funding, keep scope tight and integration easy.",
}

# Create an OpenAI client instance
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_persona_response(phase, conversation_history=None, scratchpad=None): # Added conversation_history parameter
    """
    Calls OpenAI GPT-3.5-turbo to generate an adaptive persona reply, using conversation history.
    """
    messages = []
    persona_instructions = (
        f"You are Pat Morgan, a practical, cost-conscious hospital administrator who wants to deploy a chatbot for appointment scheduling and navigation. "
        f"Your priorities: patient experience, cost savings, and quick wins. You are skeptical of unnecessary complexity, and prefer MVPs that can be bootstrapped. "
        f"Be concise and businesslike, but willing to brainstorm when prompted. Reply ONLY as Pat Morgan would—do not add extra explanation."
    )
    messages.append({"role": "system", "content": persona_instructions})

    last_msg = ""
    # Use the passed conversation_history directly
    if conversation_history: # Check if conversation_history is provided and not empty
        for m in reversed(conversation_history):
            if isinstance(m, dict) and m.get("role") == "assistant": # Ensure m is a dict
                last_msg = m.get("text", "")
                break
        if last_msg:
            messages.append({"role": "assistant", "content": last_msg})

    # Include scratchpad information in the user prompt if available
    scratchpad_summary = ""
    if scratchpad:
        scratchpad_items = []
        for key, value in scratchpad.items():
            if value and isinstance(value, str): # Only include non-empty string values
                scratchpad_items.append(f"- {key.replace('_', ' ').title()}: {value}")
        if scratchpad_items:
            scratchpad_summary = "\nCurrent project thoughts from scratchpad:\n" + "\n".join(scratchpad_items)

    user_prompt = (
        f"As Pat Morgan, reply realistically to the assistant's last message, considering your professional background and project constraints.{scratchpad_summary}\nYour current focus is the '{phase}' phase."
    )
    messages.append({"role": "user", "content": user_prompt})

    # New OpenAI 1.x interface!
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
