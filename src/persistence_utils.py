import sqlite3
import json
import os
import datetime
from typing import Dict, Optional, Any

# Use the SQLITE_DB_PATH environment variable for the database file
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "chatbot_sessions.sqlite") # Default if not set

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a SQLite database connection."""
    return sqlite3.connect(SQLITE_DB_PATH)

def ensure_db():
    """
    Ensures that the necessary tables (sessions, search_cache) exist in the database.
    Creates them if they are missing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            uuid TEXT PRIMARY KEY,
            data_json TEXT,
            last_modified TEXT
        )
    """)

    # Create search_cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            query_hash TEXT PRIMARY KEY,
            response_json TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database {SQLITE_DB_PATH} ensured with sessions and search_cache tables.")

# Call ensure_db on module load to make sure tables are ready
ensure_db()

def _datetime_converter(o):
    """Helper function to convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def save_session(session_uuid: str, data_dict: Dict[str, Any]):
    """
    Saves a session to the database. Data is JSON-serialized.
    Datetime objects are converted to ISO format strings.
    Performs an UPSERT operation (insert or replace).

    Args:
        session_uuid: The unique identifier for the session.
        data_dict: The session data as a dictionary.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data_json = json.dumps(data_dict, default=_datetime_converter)
    except TypeError as e:
        print(f"Error serializing session data for {session_uuid}: {e}")
        # Potentially log the problematic data_dict for debugging
        # For now, we'll try to save a version with problematic fields removed or stringified
        # This is a basic fallback, a more robust solution would be needed for complex cases
        safe_data_dict = {}
        for k, v in data_dict.items():
            if isinstance(v, datetime.datetime):
                safe_data_dict[k] = v.isoformat()
            elif isinstance(v, (dict, list, str, int, float, bool, type(None))):
                 safe_data_dict[k] = v
            else:
                 safe_data_dict[k] = str(v) # Fallback to string representation
        data_json = json.dumps(safe_data_dict)
    last_modified = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (uuid, data_json, last_modified) VALUES (?, ?, ?)",
            (session_uuid, data_json, last_modified)
        )
        conn.commit()
        print(f"Session {session_uuid} saved successfully.")
    except sqlite3.Error as e:
        print(f"Error saving session {session_uuid}: {e}") # Consider using a proper logger
    finally:
        conn.close()

def load_session(session_uuid: str) -> Optional[Dict[str, Any]]:
    """
    Loads a session from the database by its UUID.

    Args:
        session_uuid: The unique identifier for the session.

    Returns:
        A dictionary containing the session data, or None if the session is not found
        or an error occurs.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT data_json FROM sessions WHERE uuid = ?", (session_uuid,))
        result = cursor.fetchone()
        if result:
            data_dict = json.loads(result[0])
            # Convert ISO format strings back to datetime objects
            for key, value in data_dict.items():
                if isinstance(value, str):
                    try:
                        # Attempt to parse as datetime if it matches ISO format
                        # This is a simple check; more robust parsing might be needed
                        if len(value) > 19 and value[10] == 'T' and (value.endswith('Z') or '+' in value or '-' in value[11:]):
                             data_dict[key] = datetime.datetime.fromisoformat(value)
                    except ValueError:
                        pass # Not an ISO datetime string, leave as is
            print(f"Session {session_uuid} loaded successfully.")
            return data_dict
        else:
            print(f"Session {session_uuid} not found.")
            return None
    except sqlite3.Error as e:
        print(f"Error loading session {session_uuid}: {e}") # Consider using a proper logger
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for session {session_uuid}: {e}")
        return None
    finally:
        conn.close()

def prune_sessions(max_age_days: int = 14):
    """
    Removes sessions older than a specified number of days from the database.

    Args:
        max_age_days: The maximum age of a session in days. Sessions older than this
                      will be removed. Defaults to 14 days.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=max_age_days)).isoformat()
    try:
        cursor.execute("DELETE FROM sessions WHERE last_modified < ?", (cutoff_date,))
        conn.commit()
        deleted_count = cursor.rowcount
        print(f"Pruned {deleted_count} sessions older than {max_age_days} days.")
    except sqlite3.Error as e:
        print(f"Error pruning sessions: {e}") # Consider using a proper logger
    finally:
        conn.close()

# --- Search Cache Helper Functions ---
# These will be called by search_utils.py

def get_cached_search_response(query_hash: str, max_age_hours: int = 12) -> Optional[Dict[str, Any]]:
    """
    Looks up a query in the search_cache table.

    Args:
        query_hash: The SHA256 hash of the search query.
        max_age_hours: The maximum age of the cache entry in hours.

    Returns:
        The cached response as a dictionary if found and not expired, otherwise None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT response_json, timestamp FROM search_cache WHERE query_hash = ?", (query_hash,))
        result = cursor.fetchone()
        if result:
            response_json_str, timestamp_str = result
            cached_time = datetime.datetime.fromisoformat(timestamp_str)
            # Ensure current_time is offset-aware if timestamp_str is
            if cached_time.tzinfo is None: # If timestamp was stored as naive
                current_time = datetime.datetime.now()
            else: # If timestamp was stored as aware (e.g. UTC)
                current_time = datetime.datetime.now(datetime.timezone.utc)

            if (current_time - cached_time).total_seconds() / 3600 < max_age_hours:
                print(f"Cache hit for hash {query_hash}.")
                return json.loads(response_json_str)
            else:
                print(f"Cache expired for hash {query_hash}.")
                return None
        else:
            print(f"Cache miss for hash {query_hash}.")
            return None
    except sqlite3.Error as e:
        print(f"Error looking up cached search response for hash {query_hash}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding cached JSON for hash {query_hash}: {e}")
        return None
    finally:
        conn.close()

def store_search_response(query_hash: str, response_data: Dict[str, Any]):
    """
    Stores a search query response in the search_cache table.

    Args:
        query_hash: The SHA256 hash of the search query.
        response_data: The search response data as a dictionary.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    response_json_str = json.dumps(response_data)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO search_cache (query_hash, response_json, timestamp) VALUES (?, ?, ?)",
            (query_hash, response_json_str, timestamp)
        )
        conn.commit()
        print(f"Search response for hash {query_hash} stored in cache.")
    except sqlite3.Error as e:
        print(f"Error storing search response for hash {query_hash}: {e}")
    finally:
        conn.close()

def clear_search_cache():
    """
    Clears all entries from the search_cache table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM search_cache")
        conn.commit()
        print("Search cache cleared.")
    except sqlite3.Error as e:
        print(f"Error clearing search cache: {e}")
    finally:
        conn.close()