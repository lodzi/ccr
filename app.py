
import os, json, re
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Culturally Creative & Relevant Rater", page_icon="🗂️", layout="wide")

# --------- Constants ---------
DATA_DIR = "data"
RATINGS_CSV = os.path.join(DATA_DIR, "CCR_ratings.csv")
RESULTS_CSV = os.path.join(DATA_DIR, "CCR_results.csv")

DEFAULT_WEIGHTS = {
  "CR_cultural_resonance": 0.22,
  "OR_originality": 0.18,
  "TI_timeliness": 0.12,
  "IE_inclusivity_ethics": 0.10,
  "SH_shareability": 0.15,
  "BF_brand_channel_fit": 0.13,
  "CQ_craft_quality": 0.10
}
DIMENSIONS = list(DEFAULT_WEIGHTS.keys())

AUDIENCE_OPTIONS = [
    "BE urban 16-24",
    "BE Gen Z 18-24",
    "BE mainstream 25-44",
    "NL mainstream 25-44",
    "EU mainstream 25-44",
    "FR urban 18-34",
    "DE mainstream 18-49",
    "Other...",
]
CHANNEL_OPTIONS = ["TikTok","Instagram","YouTube","OOH","TV","Radio","Integrated","Other"]
RATER_OPTIONS = ["Lode","Maarten"]

os.makedirs(DATA_DIR, exist_ok=True)

# --------- Helpers ---------
def ensure_csv(path):
    if not os.path.exists(path):
        cols = ["campaign_id","rater_id","rater_notes","campaign_name","brand","channel","scene_audience","country","submit_date_iso","asset_youtube_url",*DIMENSIONS,"flag_stereotype","flag_misappropriation","flag_sensitive_timing","flag_other_risk","neg_sentiment_ratio_estimate"]
        pd.DataFrame(columns=cols).to_csv(path, index=False)

def load_ratings():
    ensure_csv(RATINGS_CSV)
    try:
        return pd.read_csv(RATINGS_CSV)
    except Exception:
        return pd.DataFrame(columns=["campaign_id","rater_id","rater_notes","campaign_name","brand","channel","scene_audience","country","submit_date_iso","asset_youtube_url",*DIMENSIONS,"flag_stereotype","flag_misappropriation","flag_sensitive_timing","flag_other_risk","neg_sentiment_ratio_estimate"])

def save_rating(row: dict):
    df = load_ratings()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RATINGS_CSV, index=False)

def to_0_100(x):
    import pandas as pd
    return (pd.to_numeric(x, errors="coerce") - 1.0)/4.0*100.0

def compute_results(weights: dict) -> pd.DataFrame:
    df = load_ratings()
    if df.empty: 
        return pd.DataFrame()

    for d in DIMENSIONS:
        df[f"{d}_100"] = to_0_100(df[d])
    df["CCR_rater"] = 0.0
    for d, w in weights.items():
        df["CCR_rater"] += w * df[f"{d}_100"]

    agg = {**{d: "mean" for d in DIMENSIONS},
           **{f"{d}_100": "mean" for d in DIMENSIONS},
           **{c: "mean" for c in ["flag_stereotype","flag_misappropriation","flag_sensitive_timing","flag_other_risk","neg_sentiment_ratio_estimate"] if c in df.columns},
           "CCR_rater": "mean",
           "campaign_name":"first",
           "brand":"first",
           "channel":"first",
           "scene_audience":"first",
           "country":"first",
           "asset_youtube_url":"first"}
    grouped = df.groupby("campaign_id", dropna=False).agg(agg).reset_index()
    grouped["CCR_mean"] = grouped["CCR_rater"]
    grouped.to_csv(RESULTS_CSV, index=False)
    return grouped

def live_ccr_preview(scores: dict, weights: dict) -> float:
    total = 0.0
    for d,w in weights.items():
        s100 = (scores.get(d, 3.0) - 1.0)/4.0*100.0
        total += w * s100
    return max(0.0, min(100.0, total))

def next_campaign_id(df: pd.DataFrame) -> str:
    if df.empty or "campaign_id" not in df.columns or df["campaign_id"].dropna().empty:
        return "CMP001"
    last = str(df["campaign_id"].dropna().iloc[-1])
    m = re.match(r"([A-Za-z]*)(\d+)$", last)
    if m:
        prefix, num = m.group(1) or "CMP", m.group(2)
        nxt = int(num) + 1
        return f"{prefix}{nxt:03d}"
    return f"CMP{len(df)+1:03d}"

# --------- Session State Defaults ---------
if "step" not in st.session_state:
    st.session_state.step = "Campagne-info"
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

# --------- Header ---------
st.title("Culturally Creative & Relevant Rater")

# --------- Stepper (segmented control) ---------
try:
    st.session_state.step = st.segmented_control(
        "Stap",
        options=["Campagne-info","Score","Output"],
        default=st.session_state.step,
    )
except Exception:
    # fallback to radio if segmented_control not available
    st.session_state.step = st.radio("Stap", ["Campagne-info","Score","Output"], index=["Campagne-info","Score","Output"].index(st.session_state.step), horizontal=True)

# --------- RENDER: Campagne-info ---------
if st.session_state.step == "Campagne-info":
    st.subheader("Campagne-info")
    c_left, c_right = st.columns(2)
    with c_left:
        st.session_state.info["campaign_id"] = st.text_input("Campaign ID *", value=st.session_state.info["campaign_id"])
        bn1, bn2 = st.columns(2)
        with bn1:
            st.session_state.info["brand"] = st.text_input("Brand", value=st.session_state.info["brand"])
        with bn2:
            st.session_state.info["campaign_name"] = st.text_input("Name", value=st.session_state.info["campaign_name"])
        st.session_state.info["channel"] = st.selectbox("Channel", CHANNEL_OPTIONS, index=CHANNEL_OPTIONS.index(st.session_state.info["channel"]) if st.session_state.info["channel"] in CHANNEL_OPTIONS else 0)
    with c_right:
        st.session_state.info["scene_audience_choice"] = st.selectbox("Audience", AUDIENCE_OPTIONS, index=AUDIENCE_OPTIONS.index(st.session_state.info["scene_audience_choice"]) if st.session_state.info["scene_audience_choice"] in AUDIENCE_OPTIONS else 0)
        if st.session_state.info["scene_audience_choice"] == "Other...":
            st.session_state.info["scene_audience_custom"] = st.text_input("Custom audience", value=st.session_state.info["scene_audience_custom"])
        st.session_state.info["country"] = st.text_input("Country", value=st.session_state.info["country"])
        st.session_state.info["submit_date_iso"] = st.text_input("Date", value=st.session_state.info["submit_date_iso"])
        st.session_state.info["rater_id"] = st.selectbox("Rater", ["Lode","Maarten"], index=["Lode","Maarten"].index(st.session_state.info["rater_id"]) if st.session_state.info["rater_id"] in ["Lode","Maarten"] else 0)
    st.session_state.info["asset_youtube_url"] = st.text_input("YouTube URL (optioneel)", value=st.session_state.info["asset_youtube_url"], placeholder="https://www.youtube.com/watch?v=...")
    st.session_state.info["rater_notes"] = st.text_area("Rater notes", value=st.session_state.info["rater_notes"], height=90, placeholder="Kernobservaties, insider cues, etc.")

    if st.button("Volgende →", type="primary"):
        st.session_state.step = "Score"
        st.rerun()

# --------- RENDER: Score ---------
elif st.session_state.step == "Score":
    st.subheader("Score")
    DESCRIPTIONS = {
        "CR_cultural_resonance": {"title":"Cultural Resonance", "desc":"Raakt de campagne de cultuur/scene van de doelgroep? Insider cues, taal, symbolen."},
        "OR_originality": {"title":"Originality", "desc":"Is het concept verrassend en vernieuwend vs. wat al bestaat?"},
        "TI_timeliness": {"title":"Timeliness", "desc":"Sluit dit aan bij het momentum: trends, events, seizoen?"},
        "IE_inclusivity_ethics": {"title":"Inclusivity & Ethics", "desc":"Respectvol en inclusief, zonder stereotypes of toe-eigening?"},
        "SH_shareability": {"title":"Shareability", "desc":"Hoe deelbaar is het? Hook, quotables, remixedbaarheid."},
        "BF_brand_channel_fit": {"title":"Brand & Channel Fit", "desc":"Matcht met merkcodes en benut het kanaal optimaal?"},
        "CQ_craft_quality": {"title":"Craft Quality", "desc":"Sterke uitvoering: beeld/copy/sound/edit/montage."},
    }
    left, right = st.columns([1.6, 1])
    with left:
        for d in DIMENSIONS:
            st.markdown(f"**{DESCRIPTIONS[d]['title']}**")
            st.caption(DESCRIPTIONS[d]['desc'])
            st.session_state.scores[d] = st.slider("", 1.0, 5.0, st.session_state.scores[d], 0.5, key=f"score_{d}")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.session_state.risks["flag_stereotype"] = int(st.checkbox("Stereotype", value=bool(st.session_state.risks["flag_stereotype"])))
        with r2:
            st.session_state.risks["flag_misappropriation"] = int(st.checkbox("Misappropriation", value=bool(st.session_state.risks["flag_misappropriation"])))
        with r3:
            st.session_state.risks["flag_sensitive_timing"] = int(st.checkbox("Sensitive timing", value=bool(st.session_state.risks["flag_sensitive_timing"])))
        with r4:
            st.session_state.risks["flag_other_risk"] = int(st.checkbox("Other risk", value=bool(st.session_state.risks["flag_other_risk"])))
        st.session_state.risks["neg_sentiment_ratio_estimate"] = st.slider("Neg sentiment ratio", 0.0, 1.0, float(st.session_state.risks["neg_sentiment_ratio_estimate"]), 0.01)
    with right:
        live_ccr = live_ccr_preview(st.session_state.scores, DEFAULT_WEIGHTS)
        st.subheader("📊 Live Score")
        st.markdown(f"<div style='font-size:72px;font-weight:800;line-height:1;'> {live_ccr:.0f}% </div>", unsafe_allow_html=True)
        st.caption("CCR – gewogen (default weights)")
        if st.session_state.info["asset_youtube_url"]:
            st.markdown("---")
            st.caption("YouTube preview")
            st.video(st.session_state.info["asset_youtube_url"])

    if st.button("Save rating now", type="primary"):
        info = st.session_state.info
        scene_audience = info["scene_audience_custom"] if info["scene_audience_choice"] == "Other..." else info["scene_audience_choice"]
        if not info["campaign_id"].strip():
            st.error("Campaign ID is verplicht.")
        else:
            row = {
                "campaign_id": info["campaign_id"].strip(),
                "campaign_name": info["campaign_name"].strip(),
                "brand": info["brand"].strip(),
                "channel": info["channel"],
                "scene_audience": scene_audience.strip(),
                "country": info["country"].strip(),
                "submit_date_iso": info["submit_date_iso"].strip(),
                "asset_youtube_url": info["asset_youtube_url"].strip(),
                "rater_id": info["rater_id"],
                "rater_notes": info["rater_notes"],
                **st.session_state.scores,
                **st.session_state.risks,
            }
            save_rating(row)
            # increment campaign id for next entry
            df_after = load_ratings()
            st.session_state.info["campaign_id"] = next_campaign_id(df_after)
            st.success("Rating opgeslagen.")
            # Navigate to Output
            st.session_state.step = "Output"
            st.rerun()

# --------- RENDER: Output ---------
else:  # Output
    st.subheader("Output")
    st.markdown("**Dataset (alle ratings)**")
    st.dataframe(load_ratings(), use_container_width=True)
    st.markdown("---")
    st.markdown("**Per-campagne resultaten**")
    res = compute_results(DEFAULT_WEIGHTS)
    if not res.empty:
        st.dataframe(res, use_container_width=True)
        st.download_button("Download CCR_results.csv", res.to_csv(index=False).encode("utf-8"),
                           file_name="CCR_results.csv", mime="text/csv")
    else:
        st.info("Nog geen resultaten – voeg eerst één of meer ratings toe.")
