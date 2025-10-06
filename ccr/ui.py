import streamlit as st
from .algorithm import DEFAULT_WEIGHTS, DIMENSIONS, FLAG_COLS, LABELS, live_ccr_preview
from .state import CHANNEL_OPTIONS, AUDIENCE_OPTIONS
from .data_io import load_ratings, save_rating, next_campaign_id
from .components import youtube_iframe

def inject_css():
    st.markdown("""
    <style>
    @media (min-width: 1100px) {
      section.main > div.block-container { padding-right: 420px !important; }
    }
    #fixed-live-panel {
      position: fixed; top: 90px; right: 16px; width: 340px;
      max-height: calc(100vh - 120px); overflow: auto; padding: 16px;
      border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.12);
      background: white; z-index: 999; border: 1px solid rgba(0,0,0,0.06);
    }
    html[data-theme="dark"] #fixed-live-panel { background: #262730; border-color: rgba(255,255,255,0.08); }
    @media (min-width: 1100px) { #left-params { max-width: 900px; margin-right: 440px; } }
    @media (max-width: 1099px) { #fixed-live-panel { display: none; } section.main > div.block-container { padding-right: 1.5rem !important; } }
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

def header():
    st.title("Culturally Creative & Relevant Rater")
    st.markdown("<p style='color:gray; font-style:italic; margin-top:-10px;'>by Defiant</p>", unsafe_allow_html=True)

def stepper():
    try:
        st.session_state.step = st.segmented_control("Step", options=["Campaign Information","Evaluation","Results"], default=st.session_state.step)
    except Exception:
        st.session_state.step = st.radio("Step", ["Campaign Information","Evaluation","Results"],
                                         index=["Campaign Information","Evaluation","Results"].index(st.session_state.step), horizontal=True)

def panel_fixed_right():
    live = live_ccr_preview(st.session_state.scores, st.session_state.risks)
    html = f"""
    <div id="fixed-live-panel">
      <h3 style="margin-top:0;">Live CCR</h3>
      <div style="font-size:72px;font-weight:800;line-height:1;margin-bottom:8px;">{live:.0f}%</div>
      <div style="opacity:.8;margin-bottom:10px;">Weighted by the improved algorithm</div>
    """
    if st.session_state.info.get("asset_youtube_url"):
        html += "<hr style='opacity:.2;'><div style='opacity:.8;margin-bottom:6px;'>YouTube preview</div>"
        iframe = youtube_iframe(st.session_state.info["asset_youtube_url"])
        if iframe: html += iframe
    st.markdown(html + "</div>", unsafe_allow_html=True)

def page_campaign_info():
    st.subheader("Campaign Information")
    c_left, c_right = st.columns(2)
    with c_left:
        st.session_state.info["campaign_id"] = st.text_input("Campaign ID *", value=st.session_state.info["campaign_id"])
        bn1, bn2 = st.columns(2)
        with bn1: st.session_state.info["brand"] = st.text_input("Brand", value=st.session_state.info["brand"])
        with bn2: st.session_state.info["campaign_name"] = st.text_input("Name", value=st.session_state.info["campaign_name"])
        st.session_state.info["channel"] = st.selectbox("Channel", CHANNEL_OPTIONS,
                            index=CHANNEL_OPTIONS.index(st.session_state.info["channel"]) if st.session_state.info["channel"] in CHANNEL_OPTIONS else 0)
    with c_right:
        st.session_state.info["scene_audience_choice"] = st.selectbox("Audience", AUDIENCE_OPTIONS,
                            index=AUDIENCE_OPTIONS.index(st.session_state.info["scene_audience_choice"]) if st.session_state.info["scene_audience_choice"] in AUDIENCE_OPTIONS else 0)
        if st.session_state.info["scene_audience_choice"] == "Other...":
            st.session_state.info["scene_audience_custom"] = st.text_input("Custom audience", value=st.session_state.info["scene_audience_custom"])
        st.session_state.info["country"] = st.text_input("Country", value=st.session_state.info["country"])
        st.session_state.info["submit_date_iso"] = st.text_input("Date (YYYY-MM-DD)", value=st.session_state.info["submit_date_iso"])
        st.session_state.info["rater_id"] = st.selectbox("Rater", ["Lode","Maarten"],
                            index=["Lode","Maarten"].index(st.session_state.info["rater_id"]) if st.session_state.info["rater_id"] in ["Lode","Maarten"] else 0)
    st.session_state.info["asset_youtube_url"] = st.text_input("YouTube URL (optional)",
                        value=st.session_state.info["asset_youtube_url"], placeholder="https://www.youtube.com/watch?v=...")
    st.session_state.info["rater_notes"] = st.text_area("Rater notes", value=st.session_state.info["rater_notes"],
                        height=90, placeholder="Key observations, insider cues, etc.")
    if st.button("Next →", type="primary"):
        st.session_state.step = "Evaluation"; st.rerun()

def sliders_and_risks():
    for d in DIMENSIONS:
        title, desc = LABELS[d]
        st.markdown(f"**{title}**"); st.caption(desc)
        current_val = float(st.session_state.scores.get(d, 3.0))
        st.session_state.scores[d] = st.slider("", 1.0, 5.0, current_val, 0.5, key=f"score_{d}")
    r1, r2, r3, r4 = st.columns(4)
    with r1: st.session_state.risks["flag_stereotype"] = int(st.checkbox("Stereotype", value=bool(st.session_state.risks["flag_stereotype"])))
    with r2: st.session_state.risks["flag_misappropriation"] = int(st.checkbox("Misappropriation", value=bool(st.session_state.risks["flag_misappropriation"])))
    with r3: st.session_state.risks["flag_sensitive_timing"] = int(st.checkbox("Sensitive timing", value=bool(st.session_state.risks["flag_sensitive_timing"])))
    with r4: st.session_state.risks["flag_other_risk"] = int(st.checkbox("Other risk", value=bool(st.session_state.risks["flag_other_risk"])))
    st.session_state.risks["neg_sentiment_ratio_estimate"] = st.slider("Negative sentiment ratio (0–1)", 0.0, 1.0, float(st.session_state.risks["neg_sentiment_ratio_estimate"]), 0.01)

def page_evaluation():
    st.subheader("Evaluation")
    panel_fixed_right()
    st.markdown('<div id="left-params">', unsafe_allow_html=True)
    sliders_and_risks()
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Save evaluation", type="primary"):
        info = st.session_state.info
        audience = info["scene_audience_custom"] if info["scene_audience_choice"] == "Other..." else info["scene_audience_choice"]
        row = {"campaign_id": info["campaign_id"].strip(),"campaign_name": info["campaign_name"].strip(),"brand": info["brand"].strip(),
               "channel": info["channel"],"scene_audience": audience.strip(),"country": info["country"].strip(),"submit_date_iso": info["submit_date_iso"].strip(),
               "asset_youtube_url": info["asset_youtube_url"].strip(),"rater_id": info["rater_id"],"rater_notes": info["rater_notes"],
               **st.session_state.scores, **st.session_state.risks}
        if not row["campaign_id"]: st.error("Campaign ID is required.")
        else:
            save_rating(row); df_after = load_ratings()
            st.session_state.info["campaign_id"] = next_campaign_id(df_after)
            st.success("Saved. Moving to Results…"); st.session_state.step = "Results"; st.rerun()

def page_results():
    st.subheader("Results")
    st.markdown("**Dataset (all evaluations)**")
    st.dataframe(load_ratings(), use_container_width=True)

def footer():
    st.divider()
    st.markdown("""
    <div style='text-align:center;color:gray;'>
      If you enjoy using the CCR Rater, show 
      <a href='https://www.thisisdefiant.com' target='_blank' style='color:inherit;text-decoration:underline;'>Defiant</a>
      some love.<br>
      Have suggestions about the algorithm? 
      <a href='mailto:hello@thisisdefiant.com' style='color:inherit;text-decoration:underline;'>Tell us what you think</a>
      or learn more in 
      <a href='/How_the_Algorithm_Works' style='color:inherit;text-decoration:underline;'>How the Algorithm Works</a>.
    </div>
    <p style='text-align:center;color:gray;'>© Defiant 2025</p>
    """, unsafe_allow_html=True)
