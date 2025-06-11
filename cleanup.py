import os
import shutil

def cleanup_directories():
    """
    Removes specified runtime-generated directories to reclaim disk space.
    """
    directories_to_remove = [
        "data",
        "app/old_evals",
        "app/logs",
        "app/output",
        "app/checkpoints"
    ]

    print("Starting cleanup of runtime-generated directories...")

    for directory in directories_to_remove:
        if os.path.exists(directory):
            print(f"Removing directory: {directory}")
            try:
                shutil.rmtree(directory)
                print(f"Successfully removed: {directory}")
            except OSError as e:
                print(f"Error removing directory {directory}: {e}")
        else:
            print(f"Directory does not exist, skipping: {directory}")

if __name__ == "__main__":
    cleanup_directories()