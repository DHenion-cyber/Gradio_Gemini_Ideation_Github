import json
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
            except Exception:
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
                "user_msg": turn.get("message", ""),
                "assistant_response": turn.get("assistant_response", ""),
                "low_scores": low_scores
            })
    return flagged

def export_to_csv(log_data, output_path="simulations/exports/session_eval.csv"):
    fieldnames = ["Turn", "User Message", "Assistant Response", "Helpfulness", "Relevance", "Alignment", "User Empowerment", "Coaching Tone"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, turn in enumerate(log_data):
            writer.writerow({
                "Turn": i + 1,
                "User Message": turn.get("message", ""),
                "Assistant Response": turn.get("assistant_response", ""),
                "Helpfulness": turn.get("scores", {}).get("Helpfulness", ""),
                "Relevance": turn.get("scores", {}).get("Relevance", ""),
                "Alignment": turn.get("scores", {}).get("Alignment", ""),
                "User Empowerment": turn.get("scores", {}).get("User Empowerment", ""),
                "Coaching Tone": turn.get("scores", {}).get("Coaching Tone", "")
            })

    print(f"✅ Exported CSV to {output_path}")

def export_to_pdf(log_data, summary_data, output_path="simulations/exports/session_eval.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Session Evaluation Summary")
    y -= 30

    c.setFont("Helvetica", 10)
    for key, value in summary_data["avg_scores"].items():
        c.drawString(margin, y, f"{key}: {value:.2f}")
        y -= 15

    c.drawString(margin, y, f"Weighted Score: {summary_data['weighted_average']:.2f}")
    y -= 30

    for i, turn in enumerate(log_data):
        if y < 100:
            c.showPage()
            y = height - margin
        user = turn.get("user", "")[:100]
        assistant = turn.get("assistant", "")[:100]
        scores = turn.get("scores", {})
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, f"Turn {i+1}")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(margin, y, f"User: {user}")
        y -= 15
        c.drawString(margin, y, f"Assistant: {assistant}")
        y -= 15
        for k, v in scores.items():
            c.drawString(margin + 10, y, f"{k}: {v}")
            y -= 12
        y -= 10

    c.save()
    print(f"✅ Exported PDF to {output_path}")

def main(log_file_path):
    with open(log_file_path, "r") as f:
        log_data = json.load(f)

    summary = generate_weighted_score_summary(log_data)
    flagged = flag_poor_turns(log_data)

    export_to_csv(log_data)
    export_to_pdf(log_data, summary)

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