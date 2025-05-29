import sqlite3
import json
import asyncio
import httpx
import hashlib
import datetime
import os
from typing import List, Dict, Optional

# Assuming error_handling.py exists
try:
    from . import error_handling
except ImportError:
    class ErrorHandling:
        def log_error(self, message: str, e: Exception = None):
            print(f"ERROR: {message}")
            if e:
                print(f"Exception: {e}")
    error_handling = ErrorHandling()

# Database setup for caching
CACHE_DB = "search_cache.db"

def _init_db():
    """Initializes the SQLite database for search caching."""
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            query_hash TEXT PRIMARY KEY,
            response_json TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

_init_db() # Initialize database on module load

def build_query(element: str, scratchpad: dict, user_msg: str) -> str:
    """
    Builds a focused Perplexity query based on the current element, scratchpad content,
    and user message, always including "digital health".
    """
    query_parts = [user_msg]

    if element:
        query_parts.append(f"focus on {element.replace('_', ' ')}")

    # Add relevant scratchpad content for context, but keep it concise for search queries
    context_from_scratchpad = []
    for key, value in scratchpad.items():
        if value and key != element: # Avoid duplicating the element focus
            context_from_scratchpad.append(f"{key.replace('_', ' ')}: {value}")
    if context_from_scratchpad:
        query_parts.append(f"context: {' '.join(context_from_scratchpad[:3])}") # Limit context for query length

    query_parts.append("digital health") # Always include this

    return " ".join(query_parts).strip()

def _get_query_hash(query: str) -> str:
    """Generates a SHA256 hash for a given query string."""
    return hashlib.sha256(query.encode('utf-8')).hexdigest()

def cache_lookup(query_hash: str, max_age_hours: int = 12) -> Optional[List[Dict]]:
    """
    Looks up a query in the cache. Returns the cached response if found and not expired,
    otherwise returns None.
    """
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT response_json, timestamp FROM search_cache WHERE query_hash = ?", (query_hash,))
    result = cursor.fetchone()
    conn.close()

    if result:
        response_json, timestamp_str = result
        cached_time = datetime.datetime.fromisoformat(timestamp_str)
        current_time = datetime.datetime.now(datetime.timezone.utc)
        if (current_time - cached_time).total_seconds() / 3600 < max_age_hours:
            try:
                return json.loads(response_json)
            except json.JSONDecodeError as e:
                error_handling.log_error(f"Failed to decode cached JSON for hash {query_hash}", e)
                return None
    return None

def cache_store(query_hash: str, response_json: List[Dict]):
    """
    Stores a query response in the cache.
    """
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO search_cache (query_hash, response_json, timestamp) VALUES (?, ?, ?)",
            (query_hash, json.dumps(response_json), timestamp)
        )
        conn.commit()
    except Exception as e:
        error_handling.log_error(f"Failed to store cache for hash {query_hash}", e)
    finally:
        conn.close()

async def async_perplexity_search(query: str) -> List[Dict]:
    """
    Performs an asynchronous search using the Perplexity API.
    Checks cache before making a network call and stores new responses in cache.
    Includes retry logic for transient network errors.
    """
    query_hash = _get_query_hash(query)
    cached_response = cache_lookup(query_hash)
    if cached_response:
        print(f"Cache hit for query: {query}")
        return cached_response

    print(f"Cache miss for query: {query}. Fetching from Perplexity...")
    perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not perplexity_api_key:
        error_handling.log_error("PERPLEXITY_API_KEY environment variable not set.")
        return []

    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Accept": "application/json"
    }
    url = "https://api.perplexity.ai/chat/completions" # Assuming this is the correct endpoint for search-like functionality
    # Perplexity API is primarily for chat completions, so we'll simulate a search
    # by asking it to provide search results. A dedicated search API would be better.
    messages = [
        {"role": "system", "content": "You are an AI assistant that provides concise search results. For the given query, provide 3 relevant search results including title, URL, and a short snippet."},
        {"role": "user", "content": f"Search query: {query}"}
    ]
    payload = {
        "model": "sonar-small-online", # Or another suitable online model
        "messages": messages
    }

    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status() # Raise an exception for 4xx or 5xx responses
                data = response.json()
                
                # Attempt to parse the response into a list of dicts
                # This part is highly dependent on how Perplexity's API actually returns search results.
                # For now, we'll try to extract text and then parse it.
                if data and data.get("choices"):
                    assistant_response_text = data["choices"][0]["message"]["content"]
                    # This is a very naive parsing. A more robust solution would use regex or a more structured output from Perplexity.
                    # For the purpose of this exercise, we'll assume a simple text parsing.
                    parsed_results = _parse_simple_text_search_results(assistant_response_text)
                    if parsed_results:
                        cache_store(query_hash, parsed_results)
                        return parsed_results
                    else:
                        error_handling.log_error(f"Failed to parse Perplexity response for query: {query}. Response: {assistant_response_text}")
                        return []
                return []
        except httpx.RequestError as e:
            error_handling.log_error(f"Network error during Perplexity search (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt) # Exponential backoff
            else:
                return []
        except httpx.HTTPStatusError as e:
            error_handling.log_error(f"HTTP error during Perplexity search (attempt {attempt + 1}/{retries}): {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            error_handling.log_error(f"Unexpected error during Perplexity search (attempt {attempt + 1}/{retries}): {e}")
            return []
    return []

def _parse_simple_text_search_results(text: str) -> List[Dict]:
    """
    A very basic parser for text-based search results from Perplexity.
    This needs to be adapted based on actual Perplexity output format.
    Assumes results are somewhat structured with Title, URL, Snippet.
    """
    results = []
    lines = text.split('\n')
    current_result = {}
    for line in lines:
        line = line.strip()
        if line.lower().startswith("title:"):
            if current_result: # Save previous result if exists
                results.append(current_result)
            current_result = {"title": line[len("title:"):].strip()}
        elif line.lower().startswith("url:"):
            current_result["url"] = line[len("url:"):].strip()
        elif line.lower().startswith("snippet:"):
            current_result["snippet"] = line[len("snippet:"):].strip()
        elif line and not current_result: # If line exists but no current result, assume it's a snippet for the first result
            if not results and not current_result.get("snippet"):
                current_result["snippet"] = line # First line could be a general intro
            elif current_result.get("snippet"):
                current_result["snippet"] += " " + line # Append to snippet
    if current_result:
        results.append(current_result)
    return results


def parse_perplexity_response(raw_response: List[Dict]) -> List[Dict]:
    """
    Parses raw Perplexity search results, filters for newest-first (<2 yrs),
    and returns top-3 formatted as {title, url, snippet, citation_id}.
    Note: Perplexity API doesn't directly provide publication dates for filtering.
    This function will assume `raw_response` already contains structured data
    and will focus on selecting top 3 and assigning citation_id.
    Date filtering would require actual date metadata from the search results.
    For now, "newest-first (<2 yrs)" is a conceptual filter.
    """
    parsed_results = []
    # In a real scenario, you'd filter by date here if `raw_response` had date fields.
    # For this implementation, we'll just take the first 3 and assign citation_ids.
    for i, result in enumerate(raw_response[:3]): # Take top 3
        parsed_results.append({
            "title": result.get("title", "No Title"),
            "url": result.get("url", "#"),
            "snippet": result.get("snippet", "No snippet available."),
            "citation_id": i + 1
        })
    return parsed_results

# Unit-Test Hooks
_mock_response_data = None

def mock_perplexity_response(data: Optional[List[Dict]]):
    """
    Sets a mock response for async_perplexity_search for testing purposes.
    Set to None to clear the mock.
    """
    global _mock_response_data
    _mock_response_data = data

async def _mockable_async_perplexity_search(query: str) -> List[Dict]:
    """
    Internal function to allow mocking async_perplexity_search.
    """
    if _mock_response_data is not None:
        print(f"Using mocked Perplexity response for query: {query}")
        return _mock_response_data
    else:
        return await async_perplexity_search(query)

# Override the actual function with the mockable one
async_perplexity_search = _mockable_async_perplexity_search