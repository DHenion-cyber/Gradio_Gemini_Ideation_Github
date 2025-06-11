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

def get_persona_response(phase, scratchpad=None):
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
    if scratchpad and "conversation_history" in scratchpad and scratchpad["conversation_history"]:
        for m in reversed(scratchpad["conversation_history"]):
            if m.get("role") == "assistant":
                last_msg = m.get("text", "")
                break
        if last_msg:
            messages.append({"role": "assistant", "content": last_msg})

    user_prompt = (
        "As Pat Morgan, reply realistically to the assistant's last message, considering your professional background and project constraints."
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
