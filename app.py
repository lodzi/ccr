import streamlit as st
from ccr.state import init_state
from ccr.ui import inject_css, header, stepper, page_campaign_info, page_evaluation, page_results, footer

st.set_page_config(page_title="Culturally Creative & Relevant Rater", page_icon="🧪", layout="wide")

init_state()
inject_css()
header()
stepper()

if st.session_state.step == "Campaign Information":
    page_campaign_info()
elif st.session_state.step == "Evaluation":
    page_evaluation()
else:
    page_results()

footer()
