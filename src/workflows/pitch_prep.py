"""Defines the PitchPrepWorkflow class, managing the pitch preparation coaching process."""
# Persona will be passed in, no direct import needed here unless for type hinting
# from src.personas.coach import CoachPersona

class PitchPrepWorkflow:
   def __init__(self, persona_instance, context=None): # Added persona_instance
       self.context = context or {}
       self.persona = persona_instance # Use the passed persona instance
       self.current_step = "storytelling" # Example step
       self.scratchpad = {
           "pitch_title": "",
           "target_audience": "",
           "core_message": "",
           "key_slides_content": {}, # e.g. {"problem_slide": "text", "solution_slide": "text"}
           "call_to_action": ""
       } # Example scratchpad, more detailed
       self.completed = False

   def process_user_input(self, user_input: str, search_results: list = None): # Added search_results
       # Example: Delegate to persona for response generation
       # Actual logic for step management and scratchpad updates would be here
       # response = self.persona.critique_pitch_element(self.current_step, self.scratchpad, user_input, search_results=search_results)
       # self.scratchpad[self.current_step] = user_input # Example update
       # return response + self.persona.get_reflection_prompt()
       
       # Placeholder response using the persona if available and has a generic method
       if hasattr(self.persona, 'paraphrase_user_input'):
            # This is a placeholder, actual persona methods would be more specific
           return self.persona.paraphrase_user_input(user_input, "decided", self.current_step, self.scratchpad, search_results=search_results)
       return f"PitchPrepWorkflow (Step: {self.current_step}) received: '{user_input}'. Persona would respond here."

   def generate_summary(self):
       # if hasattr(self.persona, 'generate_pitch_deck_outline'):
       #     return self.persona.generate_pitch_deck_outline(self.scratchpad)
       return f"Pitch Prep Summary for {self.scratchpad.get('pitch_title', 'Untitled Pitch')} (stub)"

   def is_complete(self):
       return self.completed

   def get_step(self):
       return self.current_step
    # TODO: add other required workflow methods, like suggest_next_step