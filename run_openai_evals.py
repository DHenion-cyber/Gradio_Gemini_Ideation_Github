import subprocess
import os
from dotenv import load_dotenv

def run_evals():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file or environment variables.")
        return
    # Construct the path to the Python executable in the venv
    # Assuming Windows based on prior context.
    # If this script needs to be cross-platform, a check for os.name would be better.
    python_executable = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(python_executable):
        # Fallback for non-Windows or if .venv is not in the standard location relative to the script
        python_executable = "python"
        print(f"Warning: .venv/Scripts/python.exe not found. Falling back to 'python'. Ensure your venv is activated and 'python' resolves to the venv's interpreter.")

    eval_cmd = [
        python_executable, "-m", "evals.cli.oaieval",
        "chatbot-openai",  # completion_fn
        "coaching-convo-quality.main",  # eval_name
        "--registry_path", "evals/registry/evals", # Made path more specific
        "--record_path", "eval_results/eval_output.jsonl"
    ]
    subprocess.run(eval_cmd)

if __name__ == "__main__":
    run_evals()