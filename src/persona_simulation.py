# src/persona_simulation.py

"""
Persona simulation module for auto-filling user responses based on program phase.
Add `from src.persona_simulation import get_persona_response` in your main app logic.
"""

PERSONA_PROFILE = {
    "name": "Pat Morgan",
    "background": "Hospital admin, 15 years managing imaging, digital innovation advocate.",
    "goal": "Deploy a patient-facing chatbot to streamline appointment scheduling and navigation for in-person care.",
    "constraints": "Bootstrap, avoid external funding, keep scope tight and integration easy.",
    "preferences": [
        "Prioritize features with highest impact and simplest integration.",
        "Hybrid approach: AI handles routine, humans for exceptions.",
        "Financial value ($3 per patient scheduled; $300/day for 100 patients).",
    ]
}

# Map your actual conversation phases to canned or dynamic responses.
def get_persona_response(phase, scratchpad=None):
    """
    Returns a plausible user response for the given phase.
    Optionally uses current scratchpad/context.
    """
    if phase == "intake":
        return (
            "I'm Pat Morgan, hospital administrator with 15 years in imaging. "
            "I'm looking for ways to use a chatbot to reduce scheduling complexity and improve care, but I want to start lean—bootstrap if possible, avoid outside investment, and keep costs down for proof of concept. "
            "My main pain point is patients and staff getting conflicting or confusing appointment instructions—especially when there are multiple appointments in a day."
        )
    elif phase == "exploration":
        return (
            "Let’s focus on a scheduling and navigation assistant for in-person care. "
            "Biggest problems: multiple appointments, fragmented instructions, and too many contact points. "
            "If we could give patients one clear itinerary and a single support number, that would be a huge improvement."
        )
    elif phase == "development":
        return (
            "Assume a scheduler makes $20/hour and handles 50 patients a day. If the bot can handle all related tasks—scheduling, reminders, and instructions—that’s about $3 saved per patient or $300/day for a 100-patient clinic. "
            "Patients get convenience, clarity, and easy follow-up; hospitals save money and reduce no-shows."
        )
    elif phase == "summary":
        return (
            "Yes, that's the value: cost savings, patient convenience, fewer missed appointments, and central support for anything the bot can't solve. "
            "Let's keep scope tight: start with scheduling, then expand to post-op care and other resources once proven."
        )
    else:
        # Default/fallback
        return "That sounds good. Please summarize what we've established so far."

# Optionally: expose a list of valid phases for your app
PHASES = ["intake", "exploration", "development", "summary"]
