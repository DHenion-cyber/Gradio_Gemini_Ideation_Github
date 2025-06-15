"""Tests the stub response behavior of search_perplexity when the API key is missing."""
import os
from src.search_utils import search_perplexity

def test_perplexity_api_key_none_returns_stub_response(monkeypatch):
    """
    Test that search_perplexity returns "STUB_RESPONSE" when PERPLEXITY_API_KEY is None.
    """
    # Ensure PERPLEXITY_API_KEY is not set for this test
    if "PERPLEXITY_API_KEY" in os.environ:
        monkeypatch.delenv("PERPLEXITY_API_KEY")
    # Set it to a value that search_perplexity would treat as missing (e.g., empty string or ensure it's not present)
    # For this test, we want it to be truly absent or None, so delenv is appropriate.
    # If we needed to set it to an empty string, we'd use monkeypatch.setenv("PERPLEXITY_API_KEY", "")
    assert search_perplexity("abc") == "STUB_RESPONSE"