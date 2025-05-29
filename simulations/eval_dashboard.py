import streamlit as st
import pandas as pd
from trulens_eval import Tru

def load_results():
    tru = Tru()
    records = tru.db.get_records_and_feedback(app_ids=["gemini_simulated_chat"])
    return pd.DataFrame.from_records(records)

st.title("TruLens Evaluation Dashboard")
df = load_results()

if not df.empty:
    st.dataframe(df[["input", "output", "feedbacks"]])
else:
    st.write("No records found yet.")