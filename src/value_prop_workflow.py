from src.coach_persona import BehaviorEngine

class ValuePropWorkflow:
    def __init__(self, context=None):
        self.context = context or {}
        self.behavior = BehaviorEngine()
        self.current_step = "problem"
        self.scratchpad = {
            "problem": "",
            "target_user": "",
            "solution": "",
            "benefit": "",
            "research_requests": []
        }
        self.completed = False

    def next_step(self):
        steps = ["problem", "target_user", "solution", "benefit"]
        idx = steps.index(self.current_step)
        if idx + 1 < len(steps):
            self.current_step = steps[idx + 1]
        else:
            self.completed = True

    def process_user_input(self, user_input: str):
        stance = self.behavior.detect_user_stance(user_input, self.current_step)
        maturity = self.behavior.assess_idea_maturity(user_input)
        response = ""
        if stance == "uncertain":
            response += self.behavior.diplomatic_acknowledgement(stance) + " "
            response += self.behavior.offer_example(self.current_step) + " "
            response += f"Could you give it a try, or want a quick brainstorm?"
        elif stance == "open":
            response += self.behavior.diplomatic_acknowledgement(stance) + " "
            response += self.behavior.offer_strategic_suggestion(self.current_step) + " "
            response += "What do you think?"
        elif stance == "interest":
            response += self.behavior.diplomatic_acknowledgement(stance) + " "
            response += "Would you like to dive deeper, or move to the next step?"
        elif stance == "decided":
            response += self.behavior.diplomatic_acknowledgement(stance)
            self.scratchpad[self.current_step] = user_input
            self.next_step()
        else:
            response += self.behavior.active_listening(user_input) + " "
            response += "Ready to move on, or want to explore further?"
        if self.current_step in ["solution", "benefit"] and stance in ["open", "uncertain"]:
            response += " Would you like me to look up relevant research or benchmarks for this?"
        return response.strip()

    def add_research_request(self, step: str, details: str = ""):
        self.scratchpad["research_requests"].append({"step": step, "details": details})

    def actionable_recommendations(self):
        recs = []
        for req in self.scratchpad["research_requests"]:
            recs.append(f"Suggested research for '{req['step']}': {req.get('details', 'TBD')}")
        if not recs:
            return "No additional research was requested."
        return "\n".join(recs)

    def generate_summary(self):
        summary = (
            f"{self.scratchpad.get('solution', 'A solution')} is proposed to address the problem: "
            f"{self.scratchpad.get('problem', 'N/A')} "
            f"for {self.scratchpad.get('target_user', 'the target users')}. "
            f"The anticipated benefit is: {self.scratchpad.get('benefit', 'N/A')}."
        )
        if self.scratchpad["research_requests"]:
            summary += (
                " Supporting evidence and further research were identified and can be reviewed in the actionable recommendations section."
            )
        return summary

    def is_complete(self):
        return self.completed

    def get_step(self):
        return self.current_step