import os
import sqlite3

# Detect if we're running in a Hugging Face Space (or anywhere we want to force /data path)
def get_sqlite_db_path():
    # HF Spaces set the HF_SPACE_ID env var
    hf_running = bool(os.environ.get("HF_SPACE_ID")) or os.environ.get("SPACE_ENVIRONMENT") == "spaces"
    db_in_data = '/data/chatbot_sessions.sqlite'
    db_local = 'chatbot_sessions.sqlite'
    if hf_running:
        # Ensure /data exists
        os.makedirs('/data', exist_ok=True)
        return db_in_data
    else:
        return db_local

SQLITE_DB_PATH = get_sqlite_db_path()

def get_db_connection():
    # Ensure parent directory exists (should already for /data)
    db_dir = os.path.dirname(SQLITE_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    try:
        return sqlite3.connect(SQLITE_DB_PATH)
    except sqlite3.OperationalError as e:
        print(f"Failed to open DB at {SQLITE_DB_PATH}: {e}")
        raise

def ensure_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Example schema setup — replace with your actual table creation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

# Call ensure_db on import (if you did this before)
ensure_db()

# Add your other persistence functions below as before...
