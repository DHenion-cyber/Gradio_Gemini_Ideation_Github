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
        return sqlite3.connect(SQLITE_DB_PATH, timeout=10, isolation_level=None)
    except Exception as e:
        print(f"CRITICAL: Could not open SQLite DB at {SQLITE_DB_PATH}: {e}")
        raise

def ensure_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Your actual schema here!
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS general_session_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        conn.close()
        print(f"SQLite DB successfully created/opened at {SQLITE_DB_PATH}")
    except Exception as e:
        print(f"CRITICAL: DB initialization failed: {e}")
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
