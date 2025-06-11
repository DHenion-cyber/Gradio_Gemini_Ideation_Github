import os
import shutil

def cleanup_directories():
    """
    Removes specified runtime-generated directories to reclaim disk space.
    Assumes it's running from the /app directory on Hugging Face Spaces.
    """
    # Paths are relative to the /app directory in Hugging Face Spaces
    # or the directory where streamlit_app.py is if run locally.
    # For Hugging Face, if streamlit_app.py is in /app/src,
    # and we want to delete /app/data, the path should be "../data"
    # However, the problem description implies these paths are relative to /app
    # Let's stick to the original paths and assume they are correct for the HF environment.
    directories_to_remove = [
        "data",                     # Expected to be /app/data
        "app/old_evals",            # This path seems absolute or relative to a root
        "app/logs",                 # Same as above
        "app/output",               # Same as above
        "app/checkpoints"           # Same as above
    ]

    # If running from /app/src, and target is /app/data, path should be ../data
    # Let's adjust for common Hugging Face structure where app root is /app
    # and main script might be in /app or /app/src
    # Assuming script is run from /app or /app/src and paths are relative to /app
    
    # More robust approach: define paths relative to the script's parent directory if it's 'src'
    # or relative to the script's directory if it's 'app'
    # For simplicity, using the provided paths and assuming they are correctly interpreted by HF.
    # If streamlit_app.py is in /app/src, then 'data' would be /app/src/data which is likely wrong.
    # The paths should likely be absolute from the root of the space, e.g., /data or /app/data.
    # The user mentioned "/data", "/app/old_evals", etc. these look like absolute paths from the Space root.

    # Let's use absolute paths from the root of the Hugging Face Space.
    # The /app directory is the root of your application code.
    # So, /data means root_of_space/data.
    # And /app/logs means root_of_space/app/logs.

    directories_to_remove_hf = [
        "/data", # Assuming this is at the root of the space, outside /app
        "old_evals", # Assuming this is inside /app, so /app/old_evals
        "logs",      # Assuming /app/logs
        "output",    # Assuming /app/output
        "checkpoints" # Assuming /app/checkpoints
    ]
    # The original request had /app/old_evals, /app/logs etc.
    # Let's use the original list and assume they are paths accessible from where the script runs.
    # If streamlit_app.py is in /app/src/, then os.getcwd() might be /app/src/
    # shutil.rmtree("data") would target /app/src/data.
    # shutil.rmtree("/data") would target the root /data if permissions allow.

    # Given the error "No module named 'cleanup'", the issue is Python's module path.
    # The paths *inside* cleanup.py for rmtree are a separate concern.
    # Let's stick to the paths provided by the user in the initial prompt for directories_to_remove.
    # These paths are relative to the root of the Hugging Face space.

    base_path = "/app" # Common root for app-specific generated files in Hugging Face

    # Corrected list based on typical Hugging Face structure and user's intent
    # /data is often at the root of the persistent storage, not necessarily /app/data
    # The other paths like /app/logs are within the application directory.
    
    final_directories_to_remove = [
        "data",             # This should be /data on the HF space root
        "app/old_evals",    # This is /app/old_evals
        "app/logs",
        "app/output",
        "app/checkpoints"
    ]
    # The script itself will be in /app/src/cleanup.py
    # If it tries to remove "data", it will look for /app/src/data
    # If it tries to remove "app/logs", it will look for /app/src/app/logs - incorrect.

    # The paths need to be relative to the root of the Hugging Face space,
    # or absolute paths within the space.
    # Let's assume the paths given are meant to be from the root of the *application directory* (/app).
    # So, if the script is in /app/src, and we want to delete /app/data, the path from /app/src would be "../data".

    # Let's re-evaluate. The user said "runtime-generated files and folders (such as /data, old logs, outputs, checkpoints, or unused evaluation artifacts)"
    # And then "Defines a list of directories to try to remove (such as /data, /app/old_evals, /app/logs, /app/output, /app/checkpoints)."
    # These look like absolute paths from the root of the Hugging Face Space.

    directories_to_remove_abs = [
        "/data",
        "/app/old_evals",
        "/app/logs",
        "/app/output",
        "/app/checkpoints"
    ]

    print("Starting cleanup of runtime-generated directories...")

    for directory in directories_to_remove_abs:
        # Check if path needs to be adjusted if script is not at /app root
        # For now, assume these absolute paths work directly.
        path_to_check = directory
        
        print(f"Attempting to check/remove: {path_to_check}")
        if os.path.exists(path_to_check):
            print(f"Removing directory: {path_to_check}")
            try:
                shutil.rmtree(path_to_check)
                print(f"Successfully removed: {path_to_check}")
            except OSError as e:
                print(f"Error removing directory {path_to_check}: {e}")
        else:
            print(f"Directory does not exist, skipping: {path_to_check}")

# Call the cleanup function directly when the module is imported.
# This ensures it runs once when streamlit_app.py imports it.
cleanup_directories()