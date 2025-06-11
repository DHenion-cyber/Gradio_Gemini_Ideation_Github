import os
import sqlite3
import sys

# --- ensure_data_dir_exists ---
def ensure_data_dir_exists():
    print("DEBUG_P_UTILS: ensure_data_dir_exists() CALLED")
    sys.stdout.flush()
    data_dir = '/data'
    try:
        if not os.path.exists(data_dir):
            print(f"DEBUG_P_UTILS: /data directory '{data_dir}' does not exist. Attempting to create.")
            sys.stdout.flush()
            os.makedirs(data_dir, exist_ok=True)
            print(f"DEBUG_P_UTILS: Successfully created or ensured /data directory '{data_dir}'")
            sys.stdout.flush()
        else:
            print(f"DEBUG_P_UTILS: /data directory '{data_dir}' already exists.")
            sys.stdout.flush()
    except Exception as e:
        print(f"CRITICAL_P_UTILS: Exception in ensure_data_dir_exists for {data_dir}: {e}")
        sys.stdout.flush()
        # Do not raise, allow get_sqlite_db_path to try to handle path determination

# --- get_sqlite_db_path ---
def get_sqlite_db_path():
    print("DEBUG_P_UTILS: get_sqlite_db_path() CALLED - TOP")
    sys.stdout.flush()
    try:
        hf_space_id = os.environ.get("HF_SPACE_ID")
        # Check /data existence *before* calling ensure_data_dir_exists within this function's logic
        is_data_dir_initially = os.path.isdir('/data')
        print(f"DEBUG_P_UTILS: In get_sqlite_db_path - HF_SPACE_ID: {hf_space_id}, initial os.path.isdir('/data'): {is_data_dir_initially}")
        sys.stdout.flush()

        if hf_space_id or is_data_dir_initially:
            print("DEBUG_P_UTILS: get_sqlite_db_path() - In if block (HF Space or /data initially exists). Ensuring /data.")
            sys.stdout.flush()
            ensure_data_dir_exists() # Attempt to create/ensure /data
            # Re-check /data status after attempt
            if not os.path.isdir('/data'):
                 print("CRITICAL_P_UTILS: /data is STILL NOT a directory after ensure_data_dir_exists(). Defaulting path to local.")
                 sys.stdout.flush()
                 final_path = 'fallback_chatbot_sessions.sqlite' # Fallback if /data cannot be made
            else:
                 final_path = '/data/chatbot_sessions.sqlite'
            print(f"DEBUG_P_UTILS: get_sqlite_db_path() - Returning from if block: {final_path}")
            sys.stdout.flush()
            return final_path
        else:
            print("DEBUG_P_UTILS: get_sqlite_db_path() - In else block (local dev likely, /data not found initially).")
            sys.stdout.flush()
            final_path = 'chatbot_sessions.sqlite' # Local path for non-HF/no-data scenarios
            print(f"DEBUG_P_UTILS: get_sqlite_db_path() - Returning from else block: {final_path}")
            sys.stdout.flush()
            return final_path
    except Exception as e:
        print(f"CRITICAL_P_UTILS: Exception in get_sqlite_db_path() execution: {e}")
        sys.stdout.flush()
        error_fallback_path = 'error_during_get_path.sqlite'
        print(f"DEBUG_P_UTILS: get_sqlite_db_path() - Returning error fallback path: {error_fallback_path}")
        sys.stdout.flush()
        return error_fallback_path

# --- Global SQLITE_DB_PATH assignment with robust error handling ---
SQLITE_DB_PATH = "uninitialized_db_path.sqlite" # Default if everything fails
try:
    print("DEBUG_P_UTILS: MODULE LEVEL - About to call get_sqlite_db_path() for SQLITE_DB_PATH global assignment.")
    sys.stdout.flush()
    SQLITE_DB_PATH = get_sqlite_db_path()
    print(f"DEBUG_P_UTILS: MODULE LEVEL - SQLITE_DB_PATH globally initialized to: {SQLITE_DB_PATH}")
    sys.stdout.flush()
    if SQLITE_DB_PATH is None: # Should be handled by get_sqlite_db_path returning fallbacks
        print("CRITICAL_P_UTILS: MODULE LEVEL - SQLITE_DB_PATH is None after assignment! This should not happen.")
        sys.stdout.flush()
        SQLITE_DB_PATH = "critical_none_fallback.sqlite"
except Exception as e:
    print(f"CRITICAL_P_UTILS: MODULE LEVEL - Exception during global SQLITE_DB_PATH assignment: {e}")
    sys.stdout.flush()
    SQLITE_DB_PATH = "global_assign_exception_fallback.sqlite"
finally:
    print(f"DEBUG_P_UTILS: MODULE LEVEL - Final SQLITE_DB_PATH after try/except/finally: {SQLITE_DB_PATH}")
    sys.stdout.flush()

# Ensure the database schema is created when this module is first imported
try:
    print("DEBUG_P_UTILS: MODULE LEVEL - Attempting to call ensure_db() after SQLITE_DB_PATH initialization.")
    sys.stdout.flush()
    ensure_db() # Defined later in the file, but Python allows this for module-level execution
    print("DEBUG_P_UTILS: MODULE LEVEL - ensure_db() call completed.")
    sys.stdout.flush()
except Exception as e:
    print(f"CRITICAL_P_UTILS: MODULE LEVEL - Exception during initial ensure_db() call: {e}")
    sys.stdout.flush()

def get_db_connection():
    print(f"DEBUG_P_UTILS: get_db_connection() called. Using SQLITE_DB_PATH: {SQLITE_DB_PATH}")
    sys.stdout.flush()
    db_dir = os.path.dirname(SQLITE_DB_PATH)
    print(f"DEBUG: db_dir: {db_dir}")
    sys.stdout.flush()
    if db_dir and not os.path.exists(db_dir):
        print(f"DEBUG: db_dir '{db_dir}' does not exist. Attempting to create.")
        sys.stdout.flush()
        try:
            os.makedirs(db_dir, exist_ok=True)
            print(f"DEBUG: Successfully created db_dir '{db_dir}'")
            sys.stdout.flush()
        except Exception as e:
            print(f"CRITICAL: Could not create db directory {db_dir}: {e}")
            sys.stdout.flush()
            raise
    else:
        print(f"DEBUG: db_dir '{db_dir}' already exists or is not specified.")
        sys.stdout.flush()
    try:
        print("DEBUG: Attempting to connect. SQLITE_DB_PATH =", SQLITE_DB_PATH)
        sys.stdout.flush()
        return sqlite3.connect(SQLITE_DB_PATH, timeout=10, isolation_level=None)
    except Exception as e:
        print(f"CRITICAL: Could not open SQLite DB at {SQLITE_DB_PATH}: {e}")
        sys.stdout.flush()
        raise

def ensure_db():
    print("DEBUG_P_UTILS: ensure_db() CALLED")
    sys.stdout.flush()
    try:
        print("DEBUG_P_UTILS: ensure_db() - Attempting to get DB connection.")
        sys.stdout.flush()
        conn = get_db_connection()
        print(f"DEBUG_P_UTILS: ensure_db() - DB connection obtained: {conn}")
        sys.stdout.flush()
        cursor = conn.cursor()
        print("DEBUG_P_UTILS: ensure_db() - Cursor obtained.")
        sys.stdout.flush()
        
        print("DEBUG_P_UTILS: ensure_db() - Attempting to CREATE TABLE chatbot_sessions.")
        sys.stdout.flush()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        print("DEBUG_P_UTILS: ensure_db() - CREATE TABLE chatbot_sessions executed.")
        sys.stdout.flush()

        print("DEBUG_P_UTILS: ensure_db() - Attempting to CREATE TABLE general_session_feedback.")
        sys.stdout.flush()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS general_session_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        print("DEBUG_P_UTILS: ensure_db() - CREATE TABLE general_session_feedback executed.")
        sys.stdout.flush()

        print("DEBUG_P_UTILS: ensure_db() - Attempting to commit.")
        sys.stdout.flush()
        conn.commit()
        print("DEBUG_P_UTILS: ensure_db() - Commit successful.")
        sys.stdout.flush()
        
        conn.close()
        print("DEBUG_P_UTILS: ensure_db() - Connection closed.")
        sys.stdout.flush()
        print(f"DEBUG_P_UTILS: SQLite DB ensure_db() completed successfully for {SQLITE_DB_PATH}")
        sys.stdout.flush()
    except Exception as e:
        print(f"CRITICAL_P_UTILS: Exception in ensure_db(): {e}") # Changed to CRITICAL_P_UTILS for consistency
        sys.stdout.flush()
        raise

# === Helper functions restored from your original code ===

def save_session(user_id, session_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chatbot_sessions (user_id, session_data) VALUES (?, ?)",
        (user_id, session_data,)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def load_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT session_data FROM chatbot_sessions WHERE id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM chatbot_sessions WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()

def save_feedback(session_id, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO general_session_feedback (session_id, feedback) VALUES (?, ?)",
        (session_id, feedback)
    )
    conn.commit()
    conn.close()

def load_feedback(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT feedback FROM general_session_feedback WHERE session_id = ?",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def delete_feedback(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM general_session_feedback WHERE session_id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()

# Add other helpers here as needed. If you have more tables or session functions, let me know!
