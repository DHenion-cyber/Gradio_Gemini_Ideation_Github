import subprocess

def run_evals():
    eval_cmd = [
        "oaieval",
        "chatbot-openai",  # completion_fn
        "coaching-convo-quality",  # eval_name
        "--registry_path", "evals/registry",
        "--record_path", "eval_results/"
    ]
    subprocess.run(eval_cmd)

if __name__ == "__main__":
    run_evals()