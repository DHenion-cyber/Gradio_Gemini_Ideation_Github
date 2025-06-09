import subprocess
import os
from dotenv import load_dotenv
# import argparse # Removed as UI launch is no longer supported here

# def launch_grading_ui(): # Removed as local UI launch seems unsupported/deprecated
#     """Launches the OpenAI Evals grading UI."""
#     record_path = "eval_results/eval_output.jsonl"
#     if not os.path.exists(record_path):
#         print(f"Error: Evaluation results file not found at {record_path}")
#         print("Please run the evaluations first to generate the results file.")
#         return
#
#     # The 'oaieval.app' command was found to be incorrect or part of an older/different setup.
#     ui_cmd = ["oaieval.app", "--record_path", record_path]
#     print(f"Attempting to launch grading UI with command: {' '.join(ui_cmd)}")
#     print("This would typically open a local web server.")
#     try:
#         subprocess.run(ui_cmd, check=True)
#     except FileNotFoundError:
#         print("Error: 'oaieval.app' command not found. This local UI functionality may be deprecated.")
#         print("Please check OpenAI's official documentation for current methods to review eval results, possibly via their online dashboard.")
#     except subprocess.CalledProcessError as e:
#         print(f"Error launching grading UI: {e}")

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
    # parser = argparse.ArgumentParser(description="Run OpenAI Evals or launch the grading UI.") # Reverted
    # parser.add_argument(
    #     "action",
    #     choices=["run", "ui"],
    #     nargs="?",
    #     default="run",
    #     help="Specify 'run' to execute evaluations or 'ui' to launch the grading interface (default: run)."
    # )
    # args = parser.parse_args()
    #
    # if args.action == "run":
    #     run_evals()
    # elif args.action == "ui":
    #     launch_grading_ui()
    run_evals() # Reverted to only run evaluations