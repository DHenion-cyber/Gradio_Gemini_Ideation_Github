"""Calculates the maturity score of an idea based on a rubric and scratchpad content."""
from constants import CANONICAL_KEYS

RUBRIC = {
    "elements": {k: {"weight": 12.5} for k in CANONICAL_KEYS}, # 8 keys * 12.5 = 100
    "scoring_cap": 100
}

def calculate_maturity(scratchpad: dict) -> tuple[int, list[str]]:
    """
    Calculates the maturity score of an idea based on the provided scratchpad.

    The score is determined by a weighted heuristic. If confidence in the
    heuristic score is low (e.g., < 0.5, placeholder for now), a call to
    a more sophisticated model like Gemini would be made using a specific rubric.

    Args:
        scratchpad: A dictionary containing idea elements.

    Returns:
        A tuple containing:
            - int: The maturity score (0-100).
            - list[str]: A list of the two weakest components (keys from RUBRIC).
    """
    score = 0
    present_elements_scores = {}

    for element in CANONICAL_KEYS:
        if scratchpad.get(element):  # Check if element is present and not empty
            # For now, presence gives full weight. Quality weighting can be added later.
            element_score = RUBRIC["elements"][element]["weight"]
            score += element_score
            present_elements_scores[element] = element_score
        else:
            present_elements_scores[element] = 0

    # Cap the score
    score = min(score, RUBRIC["scoring_cap"])

    # Determine weakest components
    # Sort elements by their score (ascending), then by name (for tie-breaking)
    sorted_elements = sorted(present_elements_scores.items(), key=lambda item: (item[1], item[0]))
    
    weakest_components = [element for element, score_val in sorted_elements if score_val < RUBRIC["elements"][element]["weight"]]
    
    # If all elements are perfectly scored, weakest_components might be empty.
    # Ensure we return at most two weakest components.
    weakest_components = weakest_components[:2]


    # Placeholder for confidence check and Gemini call
    # confidence = 0.4 # Example confidence value
    # if confidence < 0.5:
    #     # print("Confidence low, consider calling Gemini with a detailed rubric.")
    #     # gemini_score, gemini_weakest_components = call_gemini_with_rubric(scratchpad, GEMINI_RUBRIC)
    #     # return gemini_score, gemini_weakest_components
    #     pass

    return int(score), weakest_components

if __name__ == '__main__':
    # Example Usage:
    print("--- Test Case 1: Minimal ---")
    scratchpad1 = {"problem": "X", "solution": "Y", "revenue_model": ""} # revenue_model is empty
    score1, weakest1 = calculate_maturity(scratchpad1)
    print(f"Scratchpad: {scratchpad1}")
    print(f"Score: {score1}, Weakest: {weakest1}") # Expected: Score based on problem, solution. Weakest: customer_segment, differentiator (or others depending on sort order)

    print("\n--- Test Case 2: Progress ---")
    scratchpad2 = {"problem": "X", "solution": "Y", "revenue_model": "subscription"}
    score2, weakest2 = calculate_maturity(scratchpad2)
    print(f"Scratchpad: {scratchpad2}")
    print(f"Score: {score2}, Weakest: {weakest2}") # Expected: Score higher than score1.

    print("\n--- Test Case 3: More complete ---")
    scratchpad3 = {
        "problem": "Lack of affordable unicorn rides",
        "customer_segment": "Urban commuters",
        "solution": "App-based unicorn sharing",
        "differentiator": "Ethically sourced unicorns",
        "impact_metrics": "Reduced traffic congestion by 5%",
        "revenue_model": "Subscription + per-ride fee",
        "channels": "Social media, partnerships with coffee shops",
        "competitive_moat": "Exclusive unicorn breeding program"
    }
    score3, weakest3 = calculate_maturity(scratchpad3)
    print(f"Scratchpad: {scratchpad3}")
    print(f"Score: {score3}, Weakest: {weakest3}") # Expected: Score 100, Weakest: (depends on tie-breaking, could be any two if all are full)

    print("\n--- Test Case 4: Some missing ---")
    scratchpad4 = {
        "problem": "Finding good parking",
        "customer_segment": "City drivers",
        "solution": "Parking spot finder app",
        # "differentiator": "", # Missing
        "impact_metrics": "Time saved per user",
        "revenue_model": "Freemium",
        # "channels": "", # Missing
        "competitive_moat": "Proprietary algorithm"
    }
    score4, weakest4 = calculate_maturity(scratchpad4)
    print(f"Scratchpad: {scratchpad4}")
    print(f"Score: {score4}, Weakest: {weakest4}") # Expected: Score based on 6 elements. Weakest: differentiator, channels
    
    print("\n--- Test Case 5: All empty strings ---")
    scratchpad5 = {key: "" for key in RUBRIC["elements"].keys()}
    score5, weakest5 = calculate_maturity(scratchpad5)
    print(f"Scratchpad: {scratchpad5}")
    print(f"Score: {score5}, Weakest: {weakest5}") # Expected: Score 0. Weakest: e.g. ['channels', 'competitive_moat'] (depends on alphabetical)

    print("\n--- Test Case 6: One element present ---")
    scratchpad6 = {"problem": "Test Problem"}
    for key in CANONICAL_KEYS:
        if key != "problem":
            scratchpad6[key] = ""
    score6, weakest6 = calculate_maturity(scratchpad6)
    print(f"Scratchpad: {scratchpad6}")
    print(f"Score: {score6}, Weakest: {weakest6}") # Expected: Score 12.5. Weakest: e.g. ['channels', 'competitive_moat']