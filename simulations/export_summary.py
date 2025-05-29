import json
import os
from typing import Dict, Any

def export_eval_summary(log_file):
    with open(log_file, "r") as f:
        data = json.load(f)

    scores = {k: [] for k in ["Helpfulness", "Relevance", "Alignment", "User Empowerment", "Coaching Tone"]}
    for turn in data:
        for key in scores:
            score = turn.get("scores", {}).get(key)
            if score is not None:
                scores[key].append(score)

    for key in scores:
        avg = sum(scores[key]) / len(scores[key]) if scores[key] else 0
        print(f"{key}: {avg:.2f}")

if __name__ == "__main__":
    # Example usage:
    # Assuming log files are generated in simulations/logs/
    # You would run this script after running trulens_runner.py
    
    # For demonstration, create a dummy log file if it doesn't exist
    dummy_log_path = "simulations/logs/dummy_chat.json"
    if not os.path.exists(dummy_log_path):
        dummy_data = [
            {"turn_number": 1, "role": "user", "message": "Hi", "assistant_response": "Hello", "scores": {"helpfulness": 8, "relevance": 7, "alignment": 9}},
            {"turn_number": 2, "role": "assistant", "message": "Hello", "assistant_response": "How can I help?", "scores": {"helpfulness": 9, "relevance": 8, "alignment": 8}},
            {"turn_number": 3, "role": "user", "message": "Tell me about PHI", "assistant_response": "I cannot discuss PHI.", "scores": {"helpfulness": 2, "relevance": 10, "alignment": 2}}
        ]
        os.makedirs(os.path.dirname(dummy_log_path), exist_ok=True)
        with open(dummy_log_path, "w") as f:
            json.dump(dummy_data, f, indent=4)
        print(f"Created dummy log file: {dummy_log_path}")

    # Call the function with the dummy log file
    export_eval_summary(dummy_log_path)

    # You can also call it for the actual persona logs after running trulens_runner.py
    # export_eval_summary("simulations/logs/Startup_Clinician_chat.json")
    # export_eval_summary("simulations/logs/Tech_Researcher_chat.json")