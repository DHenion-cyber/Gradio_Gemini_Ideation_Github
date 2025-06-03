from src.utils.scratchpad_extractor import update_scratchpad

def test_extract_channels():
    scratch = {}
    msg = "Our main channels will be EHR app stores and hospital trade shows."
    updated_scratchpad = update_scratchpad(msg, scratch)
    assert updated_scratchpad["channels"]