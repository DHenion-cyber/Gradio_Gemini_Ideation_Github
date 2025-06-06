from src.utils.scratchpad_extractor import update_scratchpad

def test_revenue_model_extraction_from_licence_fee():
    """
    Confirm that stating "Hospitals will pay a yearly licence fee" fills revenue_model.
    """
    user_message = "Hospitals will pay a yearly licence fee"
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "revenue_model" in updated_scratchpad
    assert "yearly licence fee" in updated_scratchpad["revenue_model"].lower()

def test_revenue_model_extraction_from_pay_fee():
    """
    Confirm that stating "Customers will pay a monthly fee" fills revenue_model.
    """
    user_message = "Customers will pay a monthly fee"
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "revenue_model" in updated_scratchpad
    assert "monthly fee" in updated_scratchpad["revenue_model"].lower()

def test_problem_extraction():
    """
    Test extraction of 'problem' using regex.
    """
    user_message = "The main problem is that patients struggle with access to care."
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "problem" in updated_scratchpad
    assert "patients struggle with access to care" in updated_scratchpad["problem"]

def test_customer_segment_extraction():
    """
    Test extraction of 'customer_segment' using regex.
    """
    user_message = "Our target customers are elderly individuals."
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "customer_segment" in updated_scratchpad
    assert "elderly individuals" in updated_scratchpad["customer_segment"]

def test_solution_extraction():
    """
    Test extraction of 'solution' using regex.
    """
    user_message = "The proposed solution is a mobile app for remote monitoring."
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "solution" in updated_scratchpad
    assert "a mobile app for remote monitoring" in updated_scratchpad["solution"]

def test_value_proposition_extraction():
    """
    Test extraction of 'value_proposition' using regex.
    """
    user_message = "Our unique benefit is improved patient engagement."
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "value_proposition" in updated_scratchpad
    assert "improved patient engagement" in updated_scratchpad["value_proposition"]

def test_market_size_extraction():
    """
    Test extraction of 'market_size' using regex.
    """
    user_message = "The total addressable market is worth 50 billion dollars."
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "impact_metrics" in updated_scratchpad
    assert "50 billion dollars" in updated_scratchpad["impact_metrics"]

def test_llm_fallback_for_unmatched_keys(mocker):
    """
    Test LLM fallback when regex doesn't find a match.
    """
    mocker.patch('src.utils.scratchpad_extractor.get_llm_response', return_value='{"problem": "patients have long wait times"}')
    user_message = "Many patients experience excessively long wait times for their appointments." # Reworded to avoid direct regex match for "problem"
    scratchpad = {"customer_segment": "hospitals"} # Pre-fill one key to ensure LLM only targets missing ones
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "problem" in updated_scratchpad
    assert updated_scratchpad["problem"] == "patients have long wait times"
    assert updated_scratchpad["customer_segment"] == "hospitals" # Ensure pre-filled key is not overwritten

def test_llm_fallback_with_multiple_keys(mocker):
    """
    Test LLM fallback extracting multiple keys.
    """
    mocker.patch('src.utils.scratchpad_extractor.get_llm_response', return_value='{"problem": "lack of data integration", "solution": "a unified platform"}')
    user_message = "Data silos are a significant hurdle. Our concept involves creating a unified platform." # Reworded
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "problem" in updated_scratchpad
    assert updated_scratchpad["problem"] == "lack of data integration"
    assert "solution" in updated_scratchpad
    assert updated_scratchpad["solution"] == "a unified platform"

def test_no_extraction_if_key_already_filled():
    """
    Ensure that already filled keys are not overwritten by regex or LLM.
    """
    user_message = "The problem is something else entirely."
    scratchpad = {"problem": "existing problem description"}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert updated_scratchpad["problem"] == "existing problem description"

def test_empty_message_no_change():
    """
    An empty message should not change the scratchpad.
    """
    user_message = ""
    scratchpad = {"problem": "initial problem"}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert updated_scratchpad == {"problem": "initial problem"}

def test_message_with_no_relevant_info(mocker):
    """
    A message with no relevant info should not change the scratchpad (LLM returns empty).
    """
    mocker.patch('src.utils.scratchpad_extractor.get_llm_response', return_value='{}')
    user_message = "This is a general conversation."
    scratchpad = {"problem": "initial problem"}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert updated_scratchpad == {"problem": "initial problem"}

def test_llm_response_with_non_json_but_key_value_pairs(mocker):
    """
    Test LLM fallback when response is not strict JSON but contains key: value.
    """
    mocker.patch('src.utils.scratchpad_extractor.get_llm_response', return_value='problem: high readmission rates\ncustomer_segment: hospitals')
    user_message = "The frequency of hospital readmissions is a major concern." # Reworded
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "problem" in updated_scratchpad
    assert updated_scratchpad["problem"] == "high readmission rates"
    assert "customer_segment" in updated_scratchpad
    assert updated_scratchpad["customer_segment"] == "hospitals"

def test_llm_response_with_markdown_json(mocker):
    """
    Test LLM fallback when response is markdown JSON.
    """
    mocker.patch('src.utils.scratchpad_extractor.get_llm_response', return_value='```json\n{"problem": "data privacy concerns"}\n```')
    user_message = "Protecting data privacy is a key consideration for us." # Reworded
    scratchpad = {}
    updated_scratchpad = update_scratchpad(user_message, scratchpad)
    assert "problem" in updated_scratchpad
    assert updated_scratchpad["problem"] == "data privacy concerns"