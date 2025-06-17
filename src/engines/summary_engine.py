from typing import Dict
from ..llm_utils import query_openai

class SummaryEngine:
    def generate(self, scratchpad: Dict[str, str]) -> str:
        def fmt(k: str) -> str:
            return k.replace("_", " ").title()

        context = "\n".join(
            f"{fmt(k)}: {v}"
            for k, v in scratchpad.items() if v
        ) or "No structured input yet."

        prompt = (
            "Using the following value proposition draft, create a structured "
            "summary in markdown format. Use the following headings:\n\n"
            "Elevator Pitch:\n<one-sentence pitch>\n\n"
            "Value Proposition Details:\n"
            "- Use Case: ...\n- Problem: ...\n- Target Customer: ...\n"
            "- Solution: ...\n- Main Benefit: ...\n- Differentiator: ...\n\n"
            "Case Study Context:\n"
            "<If any relevant anecdote, scenario, or situation is known>\n\n"
            "Supporting Research & Background:\n"
            "<Any motivating evidence or reasoning provided>\n\n"
            "Here's the raw input:\n"
            f"{context}"
        )

        try:
            return query_openai(prompt)
        except Exception:
            return (
                "Elevator Pitch:\n<example pitch here>\n\n"
                "Value Proposition Details:\n"
                "- Use Case: TBD\n- Problem: TBD\n- Target Customer: TBD\n"
                "- Solution: TBD\n- Main Benefit: TBD\n- Differentiator: TBD\n\n"
                "Case Study Context:\n"
                "(No context provided)\n\n"
                "Supporting Research & Background:\n"
                "(No background provided)"
            )