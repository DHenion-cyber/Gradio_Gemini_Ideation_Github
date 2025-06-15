"""Exports conversation exchanges from session JSON files to a JSONL file for evals."""
import os
import json

print(">>> Export script started!")

SESSIONS_DIR = "sessions"
OUTPUT_JSONL = "evals/sample_data/coaching_convos_from_sessions.jsonl"

def extract_convos_from_session(session_path):
    with open(session_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    # Look for conversation history
    if "conversation_history" in session_data:
        history = session_data["conversation_history"]
    else:
        print(f"No 'conversation_history' key in {session_path}, skipping.")
        return []

    exchanges = []
    # Look for user-assistant turn pairs based on 'role' and 'text'
    for i in range(len(history) - 1):
        turn = history[i]
        next_turn = history[i + 1]
        if (
            isinstance(turn, dict) and turn.get("role") == "user"
            and isinstance(next_turn, dict) and next_turn.get("role") == "assistant"
        ):
            exchanges.append({
                "input": turn.get("text", "").strip(),
                "ideal": next_turn.get("text", "").strip()
            })
    print(f"Found {len(exchanges)} exchanges in {os.path.basename(session_path)}")
    return exchanges

def main():
    print(">>> Calling main()")
    os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
    all_exchanges = []

    if not os.path.exists(SESSIONS_DIR):
        print(f"Sessions directory not found: {SESSIONS_DIR}")
        return

    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
    print(f"Session files found: {session_files}")

    for fname in session_files:
        session_path = os.path.join(SESSIONS_DIR, fname)
        try:
            exchanges = extract_convos_from_session(session_path)
            all_exchanges.extend(exchanges)
        except Exception as e:
            print(f"Error reading {session_path}: {e}")

    if all_exchanges:
        with open(OUTPUT_JSONL, "w", encoding="utf-8") as out_f:
            for ex in all_exchanges:
                if ex["input"] and ex["ideal"]:
                    out_f.write(json.dumps(ex) + "\n")
        print(f"Wrote {len(all_exchanges)} exchanges to {OUTPUT_JSONL}")
    else:
        print("No exchanges found. Check your session file structure.")

if __name__ == "__main__":
    main()
