import sqlite3
import json
import os
import datetime
from typing import Dict, Optional, Any

# --- Dynamic Database Path Logic ---
_DB_FILENAME = "chatbot_sessions.sqlite"
_DATA_DIR_PATH = "/data"

def get_dynamic_db_path() -> str:
    """
    Determines the SQLite database path dynamically.
    Uses /data/chatbot_sessions.sqlite if /data exists,
    otherwise defaults to chatbot_sessions.sqlite in the current working directory.
    """
    if os.path.exists(_DATA_DIR_PATH) and os.path.isdir(_DATA_DIR_PATH):
        # Check if the /data directory is writable
        # This is a simplified check; real-world scenarios might need more robust permission handling
        if os.access(_DATA_DIR_PATH, os.W_OK):
            return os.path.join(_DATA_DIR_PATH, _DB_FILENAME)
        else:
            # /data exists but is not writable, fall back to local
            print(f"Warning: Directory '{_DATA_DIR_PATH}' exists but is not writable. Using local DB path.")
            return _DB_FILENAME
    return _DB_FILENAME

SQLITE_DB_PATH = get_dynamic_db_path()
# --- End Dynamic Database Path Logic ---

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a SQLite database connection."""
    # Ensure SQLITE_DB_PATH is current if it could change after module load
    # For this setup, it's set once at module load. If it needed to be more dynamic,
    # this function might need to call get_dynamic_db_path() directly.
    return sqlite3.connect(SQLITE_DB_PATH)

def ensure_db():
    """
    Ensures that the necessary tables (sessions, search_cache) exist in the database.
    Creates them if they are missing using the dynamically determined path.
    """
    # Ensure we are using the potentially updated path
    current_db_path = get_dynamic_db_path()
    if SQLITE_DB_PATH != current_db_path:
        # This case should ideally not happen if SQLITE_DB_PATH is set correctly at module load
        # and not changed elsewhere. However, as a safeguard:
        print(f"Warning: DB path discrepancy. Module loaded with {SQLITE_DB_PATH}, but current dynamic path is {current_db_path}. Using {current_db_path}.")
        # In a more complex app, you might re-initialize connection logic here or raise an error.
        # For now, we'll proceed assuming get_db_connection() will use the module-level SQLITE_DB_PATH
        # which should be the result of get_dynamic_db_path() at import time.
        # To be absolutely sure, ensure_db could take the path as an argument or re-fetch it.
        # For simplicity, we rely on get_db_connection() using the module-level SQLITE_DB_PATH.
        pass

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
    # Use the actual path that will be used by get_db_connection
    print(f"Database {SQLITE_DB_PATH} ensured with sessions and search_cache tables at path: {os.path.abspath(SQLITE_DB_PATH)}")

# Call ensure_db on module load to make sure tables are ready
# This will now use the dynamically determined SQLITE_DB_PATH
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