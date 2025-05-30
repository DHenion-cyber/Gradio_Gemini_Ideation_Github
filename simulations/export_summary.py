import json
import os
from typing import Dict, Any

def generate_weighted_score_summary(log_data):
    weight_map = {
        "Helpfulness": 0.3,
        "Relevance": 0.2,
        "Alignment": 0.2,
        "User Empowerment": 0.2,
        "Coaching Tone": 0.1
    }

    totals = {key: 0 for key in weight_map}
    counts = {key: 0 for key in weight_map}
    weighted_total = 0
    total_weight = 0

    for turn in log_data:
        for key, weight in weight_map.items():
            try:
                score = int(turn.get("scores", {}).get(key, 0))
                totals[key] += score
                counts[key] += 1
                weighted_total += score * weight
                total_weight += weight
            except:
                continue

    avg_scores = {
        key: (totals[key] / counts[key]) if counts[key] else 0
        for key in weight_map
    }

    weighted_avg = weighted_total / total_weight if total_weight else 0

    return {
        "avg_scores": avg_scores,
        "weighted_average": weighted_avg
    }

def flag_poor_turns(log_data, threshold=3):
    flagged = []
    for i, turn in enumerate(log_data):
        low_scores = {
            k: int(v)
            for k, v in turn.get("scores", {}).items()
            if int(v) < threshold
        }
        if low_scores:
            flagged.append({
                "turn": i + 1,
                "user_msg": turn.get("message", ""), # Changed from "user" to "message"
                "assistant_response": turn.get("assistant_response", ""), # Changed from "assistant" to "assistant_response"
                "low_scores": low_scores
            })
    return flagged

def main(log_file_path):
    with open(log_file_path, "r") as f:
        log_data = json.load(f)

    summary = generate_weighted_score_summary(log_data)
    flagged = flag_poor_turns(log_data)

    print("\nAverage Scores per Metric:")
    for k, v in summary["avg_scores"].items():
        print(f"  {k}: {v:.2f}")

    print(f"\nWeighted Session Score: {summary['weighted_average']:.2f}")

    if flagged:
        print(f"\n⚠️ {len(flagged)} turns flagged for low scores:")
        for f in flagged:
            print(f"\nTurn {f['turn']}")
            print(f"User: {f['user_msg']}")
            print(f"Assistant: {f['assistant_response']}")
            print(f"Low Scores: {f['low_scores']}")
    else:
        print("\n✅ No low-scoring turns.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python export_summary.py path/to/log.json")
    else:
        main(sys.argv[1])