import datetime

def log_error(message: str, e: Exception = None):
    """
    Logs an error message with a timestamp.
    Optionally includes exception details if provided.
    Logs to console and could be extended to a file or monitoring system.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_entry = f"[{timestamp}] ERROR: {message}"
    if e:
        log_entry += f" Exception: {type(e).__name__}: {e}"
    print(log_entry)
    # In a production environment, you might write this to a log file:
    # with open("error_log.txt", "a") as f:
    #     f.write(log_entry + "\n")