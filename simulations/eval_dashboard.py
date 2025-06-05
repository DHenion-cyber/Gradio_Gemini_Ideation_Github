import streamlit as st
from trulens_eval import Tru
from trulens.dashboard.streamlit import trulens_leaderboard
from trulens.core import session as core_session

st.set_page_config(layout="wide")

tru = Tru(database_url="sqlite:///default.sqlite")

st.title("TruLens Evaluation Dashboard")

# Explicitly get records and print them
session = core_session.TruSession()
lms = session.connector.db
df, feedback_col_names = lms.get_records_and_feedback(app_ids=None)

trulens_leaderboard(tru)