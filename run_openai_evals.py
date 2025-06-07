import subprocess
import os
from dotenv import load_dotenv

def run_evals():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file or environment variables.")
        return
    eval_cmd = [
        "oaieval",
        "chatbot-openai",  # completion_fn
        "coaching-convo-quality.main",  # eval_name
        "--registry_path", "evals/registry",
        "--record_path", "eval_results/eval_output.jsonl"
    ]
    subprocess.run(eval_cmd)

if __name__ == "__main__":
    run_evals()