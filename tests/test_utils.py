# tests/test_utils.py

import pytest
from src import llm_utils, search_utils, database

def test_dummy_llm_format_prompt():
    prompt = "Hello, world!"
    formatted = llm_utils.format_prompt(prompt)
    assert isinstance(formatted, str)
    assert prompt in formatted

def test_dummy_search_query_format():
    query = "test search"
    formatted = search_utils.format_query(query)
    assert isinstance(formatted, str)
    assert "test" in formatted

def test_database_connection():
    conn = database.get_connection()
    assert conn is not None
    assert hasattr(conn, 'cursor')
    conn.close()

# tests/test_utils.py

def test_math():
    assert 2 + 2 == 4
