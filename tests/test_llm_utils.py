"""Tests for the llm_utils module, covering prompt building, token counting, and citation formatting."""
import pytest
import os
from src import llm_utils
from src.constants import EMPTY_SCRATCHPAD # For build_prompt test
import streamlit as st # For mocking st.session_state in count_tokens

# Fixture to mock streamlit.session_state for count_tokens tests
# This can be moved to conftest.py if used by more test files later
@pytest.fixture
def mock_st_session_for_tokens(monkeypatch):
    mock_session_data = {}
    
    class MockSessionState:
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def __setitem__(self, key, value):
            self._data[key] = value
        
        def __contains__(self, key):
            return key in self._data

        def get(self, key, default=None):
            return self._data.get(key, default)

    mock_ss = MockSessionState(mock_session_data)
    monkeypatch.setattr(st, "session_state", mock_ss)
    # Also patch it within the llm_utils module if it's imported as 'st.session_state'
    monkeypatch.setattr(llm_utils, "st", st)
    return mock_session_data # Return the underlying data dict for manipulation

def test_format_citations_empty():
    citations_inline, references_block = llm_utils.format_citations([])
    assert citations_inline == ""
    assert references_block == ""

def test_format_citations_single():
    search_results = [{"title": "Test Title 1", "url": "http://example.com/1"}]
    citations_inline, references_block = llm_utils.format_citations(search_results)
    assert citations_inline == "[^1]"
    assert references_block == "\n--- References ---\n[^1] Test Title 1 - http://example.com/1"

def test_format_citations_multiple():
    search_results = [
        {"title": "Test Title 1", "url": "http://example.com/1"},
        {"title": "Test Title 2", "url": "http://example.com/2", "snippet": "A snippet"}
    ]
    citations_inline, references_block = llm_utils.format_citations(search_results)
    assert citations_inline == "[^1] [^2]"
    expected_references = (
        "\n--- References ---\n"
        "[^1] Test Title 1 - http://example.com/1\n"
        "[^2] Test Title 2 - http://example.com/2"
    )
    assert references_block == expected_references

def test_format_citations_missing_fields():
    search_results = [{"url": "http://example.com/1"}, {"title": "Only Title"}]
    citations_inline, references_block = llm_utils.format_citations(search_results)
    assert citations_inline == "[^1] [^2]"
    expected_references = (
        "\n--- References ---\n"
        "[^1] No Title - http://example.com/1\n"
        "[^2] Only Title - No URL"
    )
    assert references_block == expected_references

def test_count_tokens_initial(mock_st_session_for_tokens, monkeypatch):
    # Ensure "token_usage" is not in session initially to test its creation
    if "token_usage" in mock_st_session_for_tokens:
        del mock_st_session_for_tokens["token_usage"]
    
    monkeypatch.setenv("DAILY_TOKEN_CAP", "1000")
    prompt = "hello world"
    response = "this is a response"
    # prompt_tokens = 2, response_tokens = 4, total = 6
    
    limit_message = llm_utils.count_tokens(prompt, response)
    
    assert limit_message is None
    assert "token_usage" in st.session_state
    assert st.session_state["token_usage"]["session"] == 6
    assert st.session_state["token_usage"]["daily"] == 6

def test_count_tokens_accumulates(mock_st_session_for_tokens, monkeypatch):
    monkeypatch.setenv("DAILY_TOKEN_CAP", "1000")
    mock_st_session_for_tokens["token_usage"] = {"session": 10, "daily": 20}
    
    prompt = "another prompt" # 2 tokens
    response = "short" # 1 token
    # total = 3
    
    limit_message = llm_utils.count_tokens(prompt, response)
    
    assert limit_message is None
    assert st.session_state["token_usage"]["session"] == 13 # 10 + 3
    assert st.session_state["token_usage"]["daily"] == 23  # 20 + 3

def test_count_tokens_reaches_daily_cap(mock_st_session_for_tokens, monkeypatch):
    monkeypatch.setenv("DAILY_TOKEN_CAP", "100")
    mock_st_session_for_tokens["token_usage"] = {"session": 50, "daily": 98} # 2 tokens away from cap
    
    prompt = "one two three" # 3 tokens
    response = "four five"   # 2 tokens
    # total = 5
    
    limit_message = llm_utils.count_tokens(prompt, response)
    
    assert limit_message == "Daily limit reached; try again tomorrow."
    assert st.session_state["token_usage"]["session"] == 55 # 50 + 5
    assert st.session_state["token_usage"]["daily"] == 103 # 98 + 5 (goes over cap)

def test_count_tokens_invalid_cap_env(mock_st_session_for_tokens, monkeypatch):
    monkeypatch.setenv("DAILY_TOKEN_CAP", "invalid_integer")
    # Default cap is 100000
    mock_st_session_for_tokens["token_usage"] = {"session": 0, "daily": 99998}
    
    prompt = "test" # 1 token
    response = "words" # 1 token
    # total = 2
    
    limit_message = llm_utils.count_tokens(prompt, response) # Should not hit default cap yet
    assert limit_message is None
    assert st.session_state["token_usage"]["daily"] == 100000

    prompt_over = "go over cap" # 3 tokens
def test_build_prompt_minimal():
    prompt = llm_utils.build_prompt(
        conversation_history=[],
        scratchpad={},
        summaries=[],
        user_input="Hello",
        phase="exploration"
    )
    assert "SYSTEM GOALS" in prompt
    assert "Conversation Phase: exploration" in prompt
    assert "User Input: Hello" in prompt
    assert "--- Search Results Context ---" not in prompt
    assert "--- Current Value Proposition Elements ---" not in prompt
    assert "--- Conversation History ---" not in prompt
    assert "--- Summaries ---" not in prompt

def test_build_prompt_with_scratchpad_and_history():
    history = [{"role": "user", "text": "Previous message"}]
    scratchpad = {"problem": "A test problem", "solution": ""} # solution is empty
    summaries = ["A summary"]
    prompt = llm_utils.build_prompt(
        conversation_history=history,
        scratchpad=scratchpad,
        summaries=summaries,
        user_input="New message",
        phase="development"
    )
    assert "Conversation Phase: development" in prompt
    assert "--- Current Value Proposition Elements ---" in prompt
    assert "Problem: A test problem" in prompt
    assert "Solution:" not in prompt # Empty values should not be printed
    assert "--- Conversation History ---" in prompt
    assert "User: Previous message" in prompt
    assert "--- Summaries ---" in prompt
    assert "A summary" in prompt
    assert "User Input: New message" in prompt

def test_build_prompt_with_search_results():
    search_results = [{"title": "Search Result 1", "url": "http://example.com/sr1", "snippet": "Snippet 1"}]
    prompt = llm_utils.build_prompt(
        conversation_history=[],
        scratchpad={},
        summaries=[],
        user_input="Search query",
        phase="refinement",
        search_results=search_results
    )
    assert "--- Search Results Context ---" in prompt
    assert "Result 1: Snippet 1" in prompt
    assert "--- References ---" in prompt # References block should be appended
    assert "[^1] Search Result 1 - http://example.com/sr1" in prompt
    # The inline citation [^1] would be part of the LLM response, not directly in the prompt build here,
    # but the reference block itself is part of the prompt.

def test_build_prompt_all_elements():
    history = [{"role": "user", "text": "Hi"}, {"role": "assistant", "text": "Hello there"}]
    scratchpad = EMPTY_SCRATCHPAD.copy()
    scratchpad["problem"] = "Scalability issues"
    scratchpad["customer_segment"] = "Large enterprises"
    summaries = ["First summary.", "Second summary."]
    search_results = [
        {"title": "Scalability Patterns", "url": "http://example.com/scalability", "snippet": "Info on scaling."},
        {"title": "Enterprise Solutions", "url": "http://example.com/enterprise", "snippet": "Solutions for big companies."}
    ]
    user_input = "Tell me more about enterprise patterns."
    phase = "refinement"
    # element_focus is not used by build_prompt currently, so passing None or {}
    
    prompt = llm_utils.build_prompt(
        conversation_history=history,
        scratchpad=scratchpad,
        summaries=summaries,
        user_input=user_input,
        phase=phase,
        search_results=search_results,
        element_focus=None 
    )

    assert "SYSTEM GOALS" in prompt
    assert "Conversation Phase: refinement" in prompt
    
    assert "--- Current Value Proposition Elements ---" in prompt
    assert "Problem: Scalability issues" in prompt
    assert "Customer Segment: Large enterprises" in prompt
    
    assert "--- Search Results Context ---" in prompt
    assert "Result 1: Info on scaling." in prompt
    assert "Result 2: Solutions for big companies." in prompt
    
    assert "--- Conversation History ---" in prompt
    assert "User: Hi" in prompt
    assert "Assistant: Hello there" in prompt
    
    assert "--- Summaries ---" in prompt
    assert "First summary." in prompt
    assert "Second summary." in prompt
    
    assert f"User Input: {user_input}" in prompt
    
    assert "--- References ---" in prompt
    assert "[^1] Scalability Patterns - http://example.com/scalability" in prompt
    assert "[^2] Enterprise Solutions - http://example.com/enterprise" in prompt

@pytest.mark.parametrize("empty_value", ["", None, [], {}])
def test_build_prompt_handles_empty_scratchpad_values(empty_value):
    scratchpad = {"problem": "A problem", "solution": empty_value, "customer_segment": "Someone"}
    prompt = llm_utils.build_prompt([], scratchpad, [], "test", "exploration")
    assert "Problem: A problem" in prompt
    assert "Solution:" not in prompt # Check that the key for the empty value is not rendered
    assert "Customer Segment: Someone" in prompt


@pytest.mark.llm_mocked
def test_summarize_response(monkeypatch):
    mock_response_content = "This is a mock summary."

    # Mock the OpenAI client's completion create method
    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockCompletion:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    def mock_create_completion(*args, **kwargs):
        # We can assert on kwargs here if needed, e.g., model, messages, temperature, max_tokens
        assert kwargs.get("model") == 'gpt-4-1106-preview'
        assert kwargs.get("temperature") == 0.5
        assert kwargs.get("max_tokens") == 100
        user_prompt_content = kwargs["messages"][-1]["content"] # get user message
        assert user_prompt_content.startswith("Summarize the following text in 100 tokens or less:\n\n")
        assert "Original text to summarize." in user_prompt_content
        return MockCompletion(mock_response_content)

    monkeypatch.setattr(llm_utils.client.chat.completions, "create", mock_create_completion)
    
    summary = llm_utils.summarize_response("Original text to summarize.")
@pytest.mark.llm_mocked
def test_propose_next_conversation_turn_minimal_input(monkeypatch):
    mock_response_text = "Mocked proposed turn for minimal input."

    def mock_create_completion(*args, **kwargs):
        # Basic check for system and user roles in messages
        assert len(kwargs["messages"]) == 2
        assert kwargs["messages"][0]["role"] == "system"
        assert kwargs["messages"][1]["role"] == "user"
        
        system_prompt = kwargs["messages"][0]["content"]
        user_prompt = kwargs["messages"][1]["content"]

        assert "You are a peer coach brainstorming new digital health innovations" in system_prompt
        assert "Current Conversation Phase: exploration" in user_prompt
        assert "--- Intake Answers ---" not in user_prompt # No intake answers provided
        assert "--- Current Scratchpad ---" not in user_prompt # Empty scratchpad
        assert "--- Recent Conversation History (last 3 turns) ---" not in user_prompt # No history

        # Check for task instructions
        assert "--- Your Task ---" in user_prompt
        assert "Scan all intake responses and scratchpad fields." in user_prompt
        
        # Return a mock completion object
        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
        class MockMessage:
            def __init__(self, content):
                self.content = content
        class MockCompletion:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
        return MockCompletion(mock_response_text)

    monkeypatch.setattr(llm_utils.client.chat.completions, "create", mock_create_completion)

    response = llm_utils.propose_next_conversation_turn(
        intake_answers=[],
        scratchpad={},
        phase="exploration",
        conversation_history=[]
    )
    assert response == mock_response_text

@pytest.mark.llm_mocked
def test_propose_next_conversation_turn_with_all_inputs(monkeypatch):
    mock_response_text = "Mocked proposed turn with all inputs."
    
    intake = [{"text": "I like AI"}, {"text": "Healthcare focus"}]
    scratch = {"problem": "Accessibility", "solution": "Telehealth app"}
    history = [
        {"role": "user", "text": "Hello"},
        {"role": "assistant", "text": "Hi there"},
        {"role": "user", "text": "Tell me more"},
        {"role": "assistant", "text": "Okay, about what?"} # Only last 3 should be in prompt
    ]

    def mock_create_completion(*args, **kwargs):
        system_prompt = kwargs["messages"][0]["content"]
        user_prompt = kwargs["messages"][1]["content"]

        assert "You are a peer coach" in system_prompt
        assert "Current Conversation Phase: development" in user_prompt
        
        assert "--- Intake Answers ---" in user_prompt
        assert "- I like AI" in user_prompt
        assert "- Healthcare focus" in user_prompt
        
        assert "--- Current Scratchpad ---" in user_prompt
        assert "Problem: Accessibility" in user_prompt
        assert "Solution: Telehealth app" in user_prompt
        
        assert "--- Recent Conversation History (last 3 turns) ---" in user_prompt
        assert "Assistant: Hi there" in user_prompt # Second message in history
        assert "User: Tell me more" in user_prompt # Third message
        assert "Assistant: Okay, about what?" in user_prompt # Fourth message
        assert "User: Hello" not in user_prompt # First message, should be excluded (older than last 3)

        assert "--- Your Task ---" in user_prompt
        
        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
        class MockMessage:
            def __init__(self, content):
                self.content = content
        class MockCompletion:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
        return MockCompletion(mock_response_text)

    monkeypatch.setattr(llm_utils.client.chat.completions, "create", mock_create_completion)

    response = llm_utils.propose_next_conversation_turn(
        intake_answers=intake,
        scratchpad=scratch,
        phase="development",
        conversation_history=history
    )
    assert response == mock_response_text

@pytest.mark.llm_mocked
def test_propose_next_conversation_turn_empty_scratchpad_values(monkeypatch):
    mock_response_text = "Mocked turn for empty scratchpad values."
    intake = [{"text": "Test intake"}]
    # Scratchpad with some empty/None values
    scratch = {"problem": "Defined Problem", "solution": None, "customer_segment": "", "differentiator": "Exists"}

    def mock_create_completion(*args, **kwargs):
        user_prompt = kwargs["messages"][1]["content"]
        assert "Current Conversation Phase: ideation" in user_prompt
        assert "--- Intake Answers ---" in user_prompt
        assert "- Test intake" in user_prompt
        
        assert "--- Current Scratchpad ---" in user_prompt
        assert "Problem: Defined Problem" in user_prompt
        assert "Solution:" not in user_prompt # Should not include None value
        assert "Customer Segment:" not in user_prompt # Should not include empty string value
        assert "Differentiator: Exists" in user_prompt
        
        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
        class MockMessage:
            def __init__(self, content):
                self.content = content
        class MockCompletion:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
        return MockCompletion(mock_response_text)

    monkeypatch.setattr(llm_utils.client.chat.completions, "create", mock_create_completion)

    response = llm_utils.propose_next_conversation_turn(
        intake_answers=intake,
        scratchpad=scratch,
        phase="ideation"
    )
    assert response == mock_response_text

# More tests for build_prompt and summarize_response will be added next.