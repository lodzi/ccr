from datetime import date
import streamlit as st
from .algorithm import DIMENSIONS
from .data_io import load_ratings, next_campaign_id

CHANNEL_OPTIONS = ["TikTok","Instagram","YouTube","OOH","TV","Radio","Integrated","Other"]
AUDIENCE_OPTIONS = ["BE urban 16-24","BE Gen Z 18-24","BE mainstream 25-44","NL mainstream 25-44","EU mainstream 25-44","FR urban 18-34","DE mainstream 18-49","Other..."]

def init_state():
    if "step" not in st.session_state:
        st.session_state.step = "Campaign Information"
    if "info" not in st.session_state:
        df0 = load_ratings()
        st.session_state.info = {
            "campaign_id": next_campaign_id(df0),
            "campaign_name": "",
            "brand": "",
            "channel": CHANNEL_OPTIONS[0],
            "scene_audience_choice": AUDIENCE_OPTIONS[0],
            "scene_audience_custom": "",
            "country": "BE",
            "submit_date_iso": str(date.today()),
            "asset_youtube_url": "",
            "rater_id": "Lode",
            "rater_notes": "",
        }
    if "scores" not in st.session_state:
        st.session_state.scores = {d: 3.0 for d in DIMENSIONS}
    if "risks" not in st.session_state:
        st.session_state.risks = {"flag_stereotype":0,"flag_misappropriation":0,"flag_sensitive_timing":0,"flag_other_risk":0,"neg_sentiment_ratio_estimate":0.0}
