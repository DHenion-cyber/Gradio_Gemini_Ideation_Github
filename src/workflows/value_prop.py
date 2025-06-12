from typing import Tuple, Dict, List
import random

CHECKLIST = ["problem", "target_user", "solution", "benefit"]
QMAP = {
    "problem": (
        "Could you describe in one line the main problem you’d like this solution to tackle? "
        "Example: “Patients miss appointments because reminders are buried.”"
    ),
    "target_user": (
        "Who feels that pain the most? (e.g., “out-patients,” “radiology schedulers,” etc.)"
    ),
    "solution": (
        "What’s your one-sentence solution idea? You can stay high-level for now."
    ),
    "benefit": (
        "Which single measurable benefit would prove success? (e.g., “10 % fewer no-shows.”)"
    )
}
STRENGTH_TEMPL = "Strength: {item} looks solid."
ALT_POOL = [
    "Alternative: pilot with one small clinic first.",
    "Alternative: focus on peri-op patients before a hospital-wide roll-out.",
    "Alternative: consider bilingual templates to double reach with little cost.",
]

class ValuePropWorkflow:
    name = "value_prop"

    # -------- helper --------
    def _vp(self, sp: Dict) -> Dict:
        if "vp" not in sp:
            sp["vp"] = {}
        return sp["vp"]

    # -------- main entry --------
    def step(self, user_msg: str, scratchpad: Dict) -> Tuple[str, str]:
        sp_vp = self._vp(scratchpad)

        # If a question was pending, treat current user_msg as the answer
        pending = scratchpad.pop("vp_pending", None)

        if pending in CHECKLIST:
            cleaned = user_msg.strip().lower()
            if cleaned in {"not sure", "no thanks", ""}:
                # user declined or unsure → re-ask with gentle reframe
                return "No worries—take your time. " + QMAP[pending], "development"
            sp_vp[pending] = user_msg.strip()

        # Find the first missing slot
        missing: List[str] = [k for k in CHECKLIST if not sp_vp.get(k)]
        if missing:
            nxt = missing[0]
            scratchpad["vp_pending"] = nxt
            return QMAP[nxt], "development"

        # === Quick Recap phase ===
        recap = (
            f"**Quick Recap**\n"
            f"*Problem*  : {sp_vp['problem']}\n"
            f"*User*     : {sp_vp['target_user']}\n"
            f"*Solution* : {sp_vp['solution']}\n"
            f"*Benefit*  : {sp_vp['benefit']}"
        )
        strength = STRENGTH_TEMPL.format(item=random.choice(list(sp_vp.values())))
        alt      = random.choice(ALT_POOL)
        recap_block = f"{recap}\n\n{strength}\n{alt}\n\nIterate further or get the full summary?"

        scratchpad["vp_complete"] = True
        return recap_block, "summary"