from typing import Tuple, Dict, List
import random

CHECKLIST = ["problem", "target_user", "solution", "benefit"]

QMAP = {
    "problem": (
        "Could you describe in one line the main problem you’d like this solution to tackle? "
        'Example: "Patients miss appointments because reminders are buried."'
    ),
    "target_user": (
        'Who feels that pain the most? (e.g., "out-patients," "radiology schedulers," etc.)'
    ),
    "solution": (
        "What’s your one-sentence solution idea? You can stay high-level for now."
    ),
    "benefit": (
        'Which single measurable benefit would prove success? (e.g., "10% fewer no-shows.")'
    ),
}

STRENGTH_TEMPL = "Strength: {item} looks solid."
ALT_POOL = [
    "Alternative: pilot with one small clinic first.",
    "Alternative: focus on peri-op patients before a hospital-wide roll-out.",
    "Alternative: consider bilingual templates to double reach with little cost.",
]


class ValuePropWorkflow:
    name = "value_prop"

    # helper -----------------------------------------------------------
    def _vp(self, sp: Dict) -> Dict:
        if "vp" not in sp:
            sp["vp"] = {}
        return sp["vp"]

    # main entry -------------------------------------------------------
    def step(self, user_msg: str, scratchpad: Dict) -> Tuple[str, str]:
        sp_vp = self._vp(scratchpad)

        # pull pending item (if any)
        pending = scratchpad.pop("vp_pending", None)

        # stance classification ---------------------------------------
        def is_uncertain(txt: str) -> bool:
            txt = txt.lower()
            return any(k in txt for k in ["not sure", "don't know", "idk", "?", "maybe"])

        txt_lc = user_msg.lower()
        if any(k in txt_lc for k in ["open to", "explore", "any ideas"]):
            stance = "open"
        elif any(k in txt_lc for k in ["decided", "locked", "keep as is", "that's it"]):
            stance = "decided"
        elif is_uncertain(txt_lc):
            stance = "uncertain"
        else:
            stance = "interest"

        # handle answer to pending item --------------------------------
        if pending in CHECKLIST:
            if stance == "uncertain":
                return (
                    "No worries—here’s one angle you could consider. " + QMAP[pending],
                    "development",
                )

            if stance == "open":
                if pending == "problem":
                    sugg = "Consider narrowing to appointment-coordination confusion first."
                elif pending == "target_user":
                    sugg = "High-visit dialysis patients often show scheduling pain."
                elif pending == "solution":
                    sugg = "A multilingual SMS itinerary is fast to prototype."
                else:  # benefit
                    sugg = "Aim for ≥10 % no-show reduction as a clear win."
                return (
                    f"Great idea! {sugg} Does that resonate, or do you prefer something else?",
                    "development",
                )

            if stance == "decided":
                sp_vp[pending] = user_msg.strip()
                # fall through to ask next item

            else:  # stance == "interest"
                sp_vp[pending] = user_msg.strip()
                if pending != "benefit":
                    nxt = CHECKLIST[CHECKLIST.index(pending) + 1]
                    scratchpad["vp_pending"] = nxt
                    return "Great—got it. " + QMAP[nxt], "development"

        # ask next missing item ---------------------------------------
        missing = [k for k in CHECKLIST if not sp_vp.get(k)]
        if missing:
            nxt = missing[0]
            scratchpad["vp_pending"] = nxt
            return QMAP[nxt], "development"

        # recap --------------------------------------------------------
        def clean(k):
            val = sp_vp.get(k, "")
            return "" if val.lower() in {"", "not sure"} else val

        recap = (
            "**Quick Recap**\n"
            f"*Problem*  : {clean('problem')}\n"
            f"*User*     : {clean('target_user')}\n"
            f"*Solution* : {clean('solution')}\n"
            f"*Benefit*  : {clean('benefit')}"
        )
        first_solid = next((clean(k) for k in CHECKLIST if clean(k)), "early clarity")
        strength = STRENGTH_TEMPL.format(item=first_solid)
        alt = random.choice(ALT_POOL)
        recap_block = f"{recap}\n\n{strength}\n{alt}\n\nIterate further or get the full summary?"

        scratchpad["vp_complete"] = True
        return recap_block, "summary"

