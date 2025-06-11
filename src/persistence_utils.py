import os
import sqlite3

def ensure_data_dir_exists():
    data_dir = '/data'
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            print(f"CRITICAL: Unable to create /data directory: {e}")

def get_sqlite_db_path():
    # Use /data if available, else fallback to current dir (local dev)
    if os.environ.get("HF_SPACE_ID") or os.path.isdir('/data'):
        ensure_data_dir_exists()
        return '/data/chatbot_sessions.sqlite'
    else:
        return 'chatbot_sessions.sqlite'

SQLITE_DB_PATH = get_sqlite_db_path()

def get_db_connection():
    db_dir = os.path.dirname(SQLITE_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            print(f"CRITICAL: Could not create db directory {db_dir}: {e}")
            raise
    try:
        # Explicitly set timeout and isolation to avoid some cloud SQLite bugs
        return sqlite3.connect(SQLITE_DB_PATH, timeout=10, isolation_level=None)
    except Exception as e:
        print(f"CRITICAL: Could not open SQLite DB at {SQLITE_DB_PATH}: {e}")
        raise

def ensure_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Edit this schema to match your actual one!
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        conn.close()
        print(f"SQLite DB successfully created/opened at {SQLITE_DB_PATH}")
    except Exception as e:
        print(f"CRITICAL: DB initialization failed: {e}")
        raise

ensure_db()
# ... (rest of your file as before)
