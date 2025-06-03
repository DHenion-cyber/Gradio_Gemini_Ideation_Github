from src.utils.idea_maturity import calculate_maturity, RUBRIC
from src.constants import CANONICAL_KEYS, EMPTY_SCRATCHPAD

def test_score_progresses():
    """
    Tests that the maturity score increases when an element is added to the scratchpad.
    """
    scratchpad = EMPTY_SCRATCHPAD.copy() # Start with an empty scratchpad

    # Initial score with only problem and solution (empty)
    scratchpad_v1 = scratchpad.copy()
    scratchpad_v1["problem"] = "X"
    scratchpad_v1["solution"] = "Y"
    # Explicitly set revenue_model to empty to match prompt's intent for score1
    scratchpad_v1["revenue_model"] = ""
    
    score1, weakest1 = calculate_maturity(scratchpad_v1)

    # Add revenue_model
    scratchpad_v2 = scratchpad_v1.copy()
    scratchpad_v2["revenue_model"] = "subscription"
    score2, weakest2 = calculate_maturity(scratchpad_v2)

    print(f"Scratchpad v1: {scratchpad_v1}, Score1: {score1}, Weakest1: {weakest1}")
    print(f"Scratchpad v2: {scratchpad_v2}, Score2: {score2}, Weakest2: {weakest2}")
    
    assert score2 > score1, f"Score should progress. Score1 was {score1}, Score2 was {score2}"

def test_all_elements_present_max_score():
    """
    Tests that the score is capped at RUBRIC["scoring_cap"] when all elements are present.
    """
    scratchpad = {key: "filled" for key in CANONICAL_KEYS}
    score, _ = calculate_maturity(scratchpad)
    assert score == RUBRIC["scoring_cap"]

def test_no_elements_present_min_score():
    """
    Tests that the score is 0 when no elements are present.
    """
    scratchpad = EMPTY_SCRATCHPAD.copy()
    score, _ = calculate_maturity(scratchpad)
    assert score == 0

def test_weakest_elements_identified_correctly_simple():
    """
    Tests that the two weakest elements are correctly identified when some are missing.
    """
    scratchpad = {key: "filled" for key in CANONICAL_KEYS}
    scratchpad["problem"] = ""
    scratchpad["solution"] = ""
    
    expected_weakest_set = {"problem", "solution"}

    _, weakest = calculate_maturity(scratchpad)
    
    print(f"Scratchpad: {scratchpad}, Weakest: {weakest}")
    assert len(weakest) == 2, f"Expected 2 weakest elements, got {len(weakest)}"
    assert set(weakest) == expected_weakest_set, f"Expected weakest to be {expected_weakest_set}, got {set(weakest)}"


def test_weakest_elements_all_present():
    """
    Tests that if all elements are present and scored, it still returns two weakest (lowest scored).
    The function should return an empty list for weakest if all elements have full score.
    """
    scratchpad = {key: "filled" for key in CANONICAL_KEYS}
    _, weakest = calculate_maturity(scratchpad)
        
    print(f"Scratchpad: {scratchpad}, Weakest: {weakest}")
    # If all elements are filled, they all get 12.5 points.
    # The weakest_components logic should return an empty list if no element is below its full weight.
    assert weakest == [], f"Expected no weakest elements when all are filled, got {weakest}"


def test_weakest_elements_one_missing():
    """
    Tests weakest elements when only one element is missing.
    The missing element should be one of the weakest.
    """
    scratchpad = {key: "filled" for key in CANONICAL_KEYS}
    missing_element = "problem" # example
    scratchpad[missing_element] = ""

    _, weakest = calculate_maturity(scratchpad)
    
    print(f"Scratchpad: {scratchpad}, Weakest: {weakest}")
    assert len(weakest) <= 2 # Can be 1 or 2
    assert missing_element in weakest, f"Expected missing element '{missing_element}' to be in weakest {weakest}"

def test_score_cap():
    """
    Tests that the score does not exceed the scoring_cap.
    With 8 keys * 12.5 = 100, this test is effectively the same as test_all_elements_present_max_score.
    """
    scratchpad = {key: "filled" for key in CANONICAL_KEYS}
    score, _ = calculate_maturity(scratchpad)
    assert score == RUBRIC["scoring_cap"]

def test_empty_string_values_are_treated_as_absent():
    """
    Tests that elements with empty string values are treated as absent and score 0 for that element.
    """
    scratchpad = EMPTY_SCRATCHPAD.copy()
    scratchpad["problem"] = "Exists"
    scratchpad["solution"] = "" # Empty string
    scratchpad["customer_segment"] = "Also Exists"
    
    # Expected score: problem (12.5) + customer_segment (12.5) = 25
    # solution should contribute 0.
    
    expected_score = RUBRIC["elements"]["problem"]["weight"] + RUBRIC["elements"]["customer_segment"]["weight"]
    
    score, weakest = calculate_maturity(scratchpad)
    
    print(f"Scratchpad: {scratchpad}, Score: {score}, Weakest: {weakest}")
    assert score == expected_score
    
    empty_elements_in_scratchpad = {key for key, value in scratchpad.items() if not value}
    assert len(weakest) <= 2
    assert all(w_elem in empty_elements_in_scratchpad for w_elem in weakest), \
        f"Weakest elements {weakest} should be among the empty elements {empty_elements_in_scratchpad}"
    # "solution" is confirmed to be weak by its 0 contribution to score.
    # Whether it appears in the top 2 alphabetically of all weak elements is secondary.

def test_score_full():
    """
    Tests that a scratchpad with all 8 canonical keys filled yields a score of 100.
    """
    scratchpad = {key: "filled" for key in CANONICAL_KEYS}
    score, weakest = calculate_maturity(scratchpad)
    print(f"Full Scratchpad: {scratchpad}, Score: {score}, Weakest: {weakest}")
    assert score == 100
    assert weakest == [], "Expected no weakest elements when all are filled"