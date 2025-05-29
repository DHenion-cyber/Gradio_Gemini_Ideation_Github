import json
import os
from typing import Dict, Any

def export_eval_summary(log_file: str):
    """
    Loads a JSON log file from a simulation, prints average scores,
    and flags low-performing turns.

    Args:
        log_file: The path to the JSON log file (e.g., 'simulations/logs/Startup_Clinician_chat.json').
    """
    if not os.path.exists(log_file):
        print(f"Error: Log file not found at {log_file}")
        return

    with open(log_file, 'r') as f:
        transcript = json.load(f)

    if not transcript:
        print(f"No data found in {log_file}.")
        return

    total_helpfulness = 0
    total_relevance = 0
    total_alignment = 0
    evaluated_turns = 0
    low_performing_turns = []

    for turn in transcript:
        scores = turn.get("scores")
        if scores:
            helpfulness = scores.get("helpfulness")
            relevance = scores.get("relevance")
            alignment = scores.get("alignment")

            if helpfulness is not None and relevance is not None and alignment is not None:
                total_helpfulness += helpfulness
                total_relevance += relevance
                total_alignment += alignment
                evaluated_turns += 1

                # Flag turns with any score below a threshold (e.g., 5)
                if helpfulness < 5 or relevance < 5 or alignment < 5:
                    low_performing_turns.append({
                        "turn_number": turn.get("turn_number"),
                        "user_message": turn.get("message"),
                        "assistant_response": turn.get("assistant_response"),
                        "scores": scores
                    })

    print(f"\n--- Evaluation Summary for {os.path.basename(log_file)} ---")
    if evaluated_turns > 0:
        avg_helpfulness = total_helpfulness / evaluated_turns
        avg_relevance = total_relevance / evaluated_turns
        avg_alignment = total_alignment / evaluated_turns

        print(f"Average Helpfulness: {avg_helpfulness:.2f}")
        print(f"Average Relevance: {avg_relevance:.2f}")
        print(f"Average Alignment: {avg_alignment:.2f}")
    else:
        print("No evaluable turns found in the log.")

    if low_performing_turns:
        print("\n--- Low-Performing Turns (Score < 5) ---")
        for lp_turn in low_performing_turns:
            print(f"\nTurn {lp_turn['turn_number']}:")
            print(f"  User: {lp_turn['user_message']}")
            print(f"  Assistant: {lp_turn['assistant_response']}")
            print(f"  Scores: H:{lp_turn['scores'].get('helpfulness', 'N/A')}, R:{lp_turn['scores'].get('relevance', 'N/A')}, A:{lp_turn['scores'].get('alignment', 'N/A')}")
    else:
        print("\nNo low-performing turns identified.")

    print("-" * 40)

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