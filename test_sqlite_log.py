# test_sqlite_log.py
#
# Purpose:
# This script connects to a SQLite database (default: chatbot_sessions.sqlite),
# lists its tables, and queries a specified table (e.g., "messages") for records
# where the 'source' field indicates a simulated user prompt or simulated feedback.
# It then prints relevant details from these records.
#
# Instructions for Running:
# 1. Ensure you have Python 3 installed.
# 2. Place this script in the same directory as your 'chatbot_sessions.sqlite'
#    database file, or update the DB_FILE variable below to the correct path.
# 3. Run the script from your terminal: python test_sqlite_log.py
#
# Modifying for Different Schemas:
# - If your database file has a different name, change the DB_FILE variable.
# - If the script cannot automatically find your messages table, or if you want to
#   specify it directly, modify the `DEFAULT_MESSAGES_TABLE` variable.
# - If your table's column names differ from the defaults (e.g., 'session_id',
#   'user_message', 'bot_message', 'timestamp', 'source', 'module', 'rating'),
#   update the `COLUMN_MAPPING` dictionary. The keys in this dictionary are
#   conceptual field names used by the script, and the values are the
#   corresponding actual column names in your database table.
#   The script will attempt to use these mappings and will report an error if
#   essential columns (session_id, user_prompt, bot_response, timestamp, source)
#   are not found using the provided mappings. Optional columns like 'module' or
#   'rating' will be queried if found, otherwise gracefully ignored.

import sqlite3
import os

# --- Configuration ---
DB_FILE = "chatbot_sessions.sqlite"

# Table name detection:
# The script will try to find a table from this list.
# If multiple are found, or none, it will ask you to set DEFAULT_MESSAGES_TABLE.
MESSAGES_TABLE_CANDIDATES = ["messages", "chat_log", "interactions", "message_log", "session_messages"]
# If auto-detection fails or you want to override, set this variable:
# EXAMPLE: DEFAULT_MESSAGES_TABLE = "my_specific_message_table"
DEFAULT_MESSAGES_TABLE = None

# Column names mapping (conceptual_field_name: actual_db_column_name)
# Update these values if your database schema uses different column names.
COLUMN_MAPPING = {
    "session_id": "session_id",
    "user_prompt": "user_message",
    "bot_response": "bot_message",
    "timestamp": "timestamp",
    "source": "source",
    "module": "module",        # Optional, will be queried if column exists
    "rating": "rating",        # Optional, for feedback, will be queried if column exists
    # "feedback_type": "type"  # Another optional field for feedback context
}

# Fields considered essential for the script's core functionality
REQUIRED_CONCEPTUAL_FIELDS = ["session_id", "user_prompt", "bot_response", "timestamp", "source"]

def list_tables(conn):
    """Lists all tables in the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    return tables

def get_table_columns(conn, table_name):
    """Gets column names for a given table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}');")
    columns = [info[1] for info in cursor.fetchall()]
    return columns

def determine_messages_table(conn, db_tables):
    """Attempts to determine the messages table name."""
    if DEFAULT_MESSAGES_TABLE and DEFAULT_MESSAGES_TABLE in db_tables:
        print(f"Using specified messages table: '{DEFAULT_MESSAGES_TABLE}'")
        return DEFAULT_MESSAGES_TABLE

    found_candidates = [name for name in MESSAGES_TABLE_CANDIDATES if name in db_tables]

    if len(found_candidates) == 1:
        print(f"Automatically selected messages table: '{found_candidates[0]}'")
        return found_candidates[0]
    elif len(found_candidates) > 1:
        print("Multiple candidate tables found for messages:")
        for i, name in enumerate(found_candidates):
            print(f"  {i+1}. {name}")
        print(f"\nPlease specify which table to use by setting the 'DEFAULT_MESSAGES_TABLE' variable in the script.")
        return None
    else:
        print("Could not automatically determine the messages table.")
        print("Available tables:", db_tables)
        print(f"Please specify the messages table by setting the 'DEFAULT_MESSAGES_TABLE' variable in the script.")
        return None


def main():
    if not os.path.exists(DB_FILE):
        print(f"Error: Database file '{DB_FILE}' not found.")
        print("Please ensure the database file is in the correct location or update the DB_FILE variable.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Access columns by name
    except sqlite3.Error as e:
        print(f"Error connecting to database '{DB_FILE}': {e}")
        return

    print(f"Successfully connected to '{DB_FILE}'.")

    db_tables = list_tables(conn)
    if not db_tables:
        print("No tables found in the database.")
        conn.close()
        return

    print("\nTables in the database:")
    for table in db_tables:
        print(f"- {table}")

    messages_table_name = determine_messages_table(conn, db_tables)

    if not messages_table_name:
        conn.close()
        return

    print(f"\nAttempting to query table: '{messages_table_name}'")
    actual_columns = get_table_columns(conn, messages_table_name)
    if not actual_columns:
        print(f"Error: Could not retrieve column information for table '{messages_table_name}'.")
        conn.close()
        return
    
    print(f"Columns in '{messages_table_name}': {', '.join(actual_columns)}")

    select_clauses = []
    valid_conceptual_fields = []

    for conceptual_name, db_col_name in COLUMN_MAPPING.items():
        if db_col_name in actual_columns:
            select_clauses.append(f'"{db_col_name}" AS "{conceptual_name}"')
            valid_conceptual_fields.append(conceptual_name)
        elif conceptual_name in REQUIRED_CONCEPTUAL_FIELDS:
            print(f"\nError: Required column '{db_col_name}' (mapped for '{conceptual_name}') not found in table '{messages_table_name}'.")
            print(f"Please check the COLUMN_MAPPING in the script or your table schema.")
            conn.close()
            return
        else:
            print(f"Info: Optional column '{db_col_name}' (mapped for '{conceptual_name}') not found. It will not be queried.")
            
    if not select_clauses:
        print(f"Error: No usable columns found based on COLUMN_MAPPING for table '{messages_table_name}'.")
        conn.close()
        return

    source_db_col = COLUMN_MAPPING.get("source")
    if source_db_col not in actual_columns:
        print(f"\nError: The 'source' column ('{source_db_col}') is essential for filtering and was not found in table '{messages_table_name}'.")
        print(f"Please check the COLUMN_MAPPING for 'source'.")
        conn.close()
        return

    sql_query = f"""
    SELECT {', '.join(select_clauses)}
    FROM "{messages_table_name}"
    WHERE "{source_db_col}" IN ('simulated', 'simulated_feedback')
    ORDER BY "{COLUMN_MAPPING.get('timestamp', 'timestamp')}" ASC; 
    """ 
    # Default order by timestamp if mapped, otherwise uses 'timestamp' literally (might fail if not present)
    # A more robust sort would check if timestamp_db_col is in actual_columns

    print(f"\nExecuting query for simulated messages and feedback...")
    # print(f"SQL: {sql_query}") # Uncomment for debugging SQL

    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
        print("This might be due to incorrect table or column names in your configuration.")
        conn.close()
        return

    if not results:
        print("No messages found with source 'simulated' or 'simulated_feedback'.")
    else:
        print(f"\nFound {len(results)} matching entries:\n")
        for row in results:
            print("-" * 40)
            print(f"Session ID:   {row['session_id'] if 'session_id' in valid_conceptual_fields else 'N/A'}")
            print(f"Timestamp:    {row['timestamp'] if 'timestamp' in valid_conceptual_fields else 'N/A'}")
            
            source_val = row['source'] if 'source' in valid_conceptual_fields else 'N/A'
            print(f"Source:       {source_val}")

            if 'module' in valid_conceptual_fields and row['module'] is not None:
                print(f"Module:       {row['module']}")
            
            user_prompt_val = row['user_prompt'] if 'user_prompt' in valid_conceptual_fields else 'N/A'
            bot_response_val = row['bot_response'] if 'bot_response' in valid_conceptual_fields else 'N/A'

            if source_val == 'simulated_feedback':
                print(f"Feedback Text:{bot_response_val}") # Feedback text is in bot_response column for these
                if 'rating' in valid_conceptual_fields and row['rating'] is not None:
                    print(f"Rating:       {row['rating']}")
                if user_prompt_val and user_prompt_val != "N/A (Feedback Entry)": # If original prompt was logged
                     print(f"Original User Prompt (context): {user_prompt_val}")
            else: # simulated message
                print(f"User Prompt:  {user_prompt_val}")
                print(f"Bot Response: {bot_response_val}")
            print("-" * 40)

    conn.close()
    print("\nScript finished.")

if __name__ == "__main__":
    main()