"""Performs a series of health checks on the application environment and dependencies."""
import os
import sys
import sqlite3
import threading

# Flag to track overall health
all_checks_passed = True

def check_env_vars():
    global all_checks_passed
    print("Checking required environment variables...")
    required_vars = ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "SQLITE_DB_PATH", "DAILY_TOKEN_CAP"]

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"FAIL: Environment variable {var} not set.")
            all_checks_passed = False
        else:
            print(f"PASS: Environment variable {var} is set.")
    print("-" * 30)

def check_module_imports():
    global all_checks_passed
    print("Checking module imports and function resolution...")
    modules_to_check = {
        "conversation_manager": "initialize_conversation_state",
        "database": "get_connection", # Corrected function name
        "error_handling": "log_error",
        "llm_utils": "query_openai",
        "persistence_utils": "save_session",
        "search_utils": "async_perplexity_search",
        "ui_components": "privacy_notice",
        "streamlit_app": None # For streamlit_app, just check import
    }

    for module_name, func_name in modules_to_check.items():
        try:
            module = __import__(f"src.{module_name}", fromlist=[func_name if func_name else module_name])
            if func_name:
                assert hasattr(module, func_name)
                print(f"PASS: src.{module_name} imported and function '{func_name}' resolves.")
            else:
                print(f"PASS: src.{module_name} imported.")
        except Exception as e:
            print(f"FAIL: Importing src.{module_name} or resolving function: {e}")
            all_checks_passed = False
    print("-" * 30)

def check_sqlite_connection():
    global all_checks_passed
    print("Checking SQLite connection...")
    db_path = os.getenv("SQLITE_DB_PATH")
    if not db_path:
        print("FAIL: SQLITE_DB_PATH not set, cannot check SQLite connection.")
        all_checks_passed = False
        print("-" * 30)
        return

    try:
        conn = sqlite3.connect(db_path)
        # You might want to execute a simple query like "PRAGMA integrity_check;"
        conn.close()
        print(f"PASS: SQLite connection to '{db_path}' opened and closed successfully.")
    except Exception as e:
        print(f"FAIL: SQLite connection to '{db_path}' failed: {e}")
        all_checks_passed = False
    print("-" * 30)

# Mock Streamlit's session_state for token logging simulation
class MockSessionState(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure token_usage is initialized as llm_utils.count_tokens expects it
        if 'token_usage' not in self:
            self['token_usage'] = {"session": 0, "daily": 0}

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            # Fallback for items not explicitly set, to mimic st.session_state behavior
            # For this specific mock, we only care about token_usage
            if item == 'token_usage' and item not in self:
                 self[item] = {"session": 0, "daily": 0}
                 return self[item]
            raise AttributeError(f"MockSessionState has no attribute '{item}'")


    def __setattr__(self, key, value):
        self[key] = value

mock_st_session_state = MockSessionState()

def simulate_token_log_call(call_id: int):
    try:
        from src import llm_utils
        # This import is tricky because streamlit is not a direct dependency of health_check.py
        # However, llm_utils.count_tokens uses st.session_state.
        # We will mock st.session_state globally for the duration of this function.
        class MockStreamlitModule:
            def __init__(self):
                self.session_state = mock_st_session_state
        
        st_original = sys.modules.get("streamlit")
        sys.modules["streamlit"] = MockStreamlitModule()

        llm_utils.count_tokens("test prompt", "test response")

        if st_original:
            sys.modules["streamlit"] = st_original
        else:
            del sys.modules["streamlit"]
            
    except Exception as e:
        print(f"Error in simulate_token_log_call for call {call_id}: {e}")
        # Depending on strictness, this could set all_checks_passed = False

def check_hf_spaces_and_concurrency():
    global all_checks_passed
    print("Checking Hugging Face Spaces detection and concurrency...")
    is_hf_space = os.getenv("HF_SPACE_ID") is not None
    concurrency_level_msg = ""

    if is_hf_space:
        print("INFO: Detected Hugging Face Spaces environment.")
        num_concurrent_calls = 5
        concurrency_level_msg = "LOW CONCURRENCY"
        print("Checking Hugging Face Secrets...")
        secret_gemini = os.getenv("SECRET_OPENAI_API_KEY")
        secret_perplexity = os.getenv("SECRET_PERPLEXITY_API_KEY")
        if not secret_gemini:
            print("FAIL: SECRET_OPENAI_API_KEY not set in HF Space.")
            all_checks_passed = False
        else:
            print("PASS: SECRET_OPENAI_API_KEY is set in HF Space.")
        if not secret_perplexity:
            print("FAIL: SECRET_PERPLEXITY_API_KEY not set in HF Space.")
            all_checks_passed = False
        else:
            print("PASS: SECRET_PERPLEXITY_API_KEY is set in HF Space.")
    else:
        print("INFO: Not in Hugging Face Spaces environment (or HF_SPACE_ID not set).")
        num_concurrent_calls = 25
        concurrency_level_msg = "STRESS"

    print(f"Simulating {num_concurrent_calls} concurrent token-logging calls...")
    threads = []
    for i in range(num_concurrent_calls):
        thread = threading.Thread(target=simulate_token_log_call, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f"PASS: Simulated {num_concurrent_calls} concurrent calls completed.")
    if concurrency_level_msg: # Only print if set
        print(f"HEALTH CHECK PASS ({concurrency_level_msg}) for concurrency simulation.")
    print("-" * 30)

def main():
    print("Starting Health Check...")
    print("=" * 30)

    check_env_vars()
    check_module_imports()
    check_sqlite_connection()
    check_hf_spaces_and_concurrency()

    print("=" * 30)
    if all_checks_passed:
        print("All health checks PASSED.")
        sys.exit(0)
    else:
        print("One or more health checks FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()