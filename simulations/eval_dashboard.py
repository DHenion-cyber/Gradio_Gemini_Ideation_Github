import streamlit as st
import pandas as pd
from trulens_eval import Tru
import matplotlib.pyplot as plt

def load_results():
    tru = Tru()
    records = tru.db.get_records_and_feedback(app_ids=["gemini_simulated_chat"])
    return pd.DataFrame.from_records(records)

st.title("TruLens Evaluation Dashboard")
df = load_results()

if not df.empty:
    st.dataframe(df[["input", "output", "feedbacks"]])
    
    def score_chart(df):
        metrics = ["Helpfulness", "Relevance", "Alignment", "User Empowerment", "Coaching Tone"]
        if "feedbacks" not in df.columns:
            st.warning("No feedbacks available.")
            return

        rows = []
        for idx, row in df.iterrows():
            scores = row["feedbacks"]
            if isinstance(scores, dict):
                rows.append({k: int(scores.get(k, 0)) for k in metrics})
        if not rows:
            return

        score_df = pd.DataFrame(rows)
        st.write("### Average Scores per Metric")
        st.bar_chart(score_df.mean())

        st.write("### Score Trends by Turn")
        st.line_chart(score_df)

    score_chart(df)
else:
    st.write("No records found yet.")