
import os, json, re
from datetime import date
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Culturally Creative & Relevant Rater", page_icon="🗂️", layout="wide")

DATA_DIR = "data"
RATINGS_CSV = os.path.join(DATA_DIR, "CCR_ratings.csv")
RESULTS_CSV = os.path.join(DATA_DIR, "CCR_results.csv")
WEIGHTS_JSON = os.path.join(DATA_DIR, "CCR_default_weights.json")

os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_WEIGHTS = {
  "CR_cultural_resonance": 0.18,
  "OR_originality": 0.12,
  "TI_timeliness": 0.10,
  "IE_inclusivity_ethics": 0.08,
  "SH_shareability": 0.10,
  "BF_brand_channel_fit": 0.08,
  "CQ_craft_quality": 0.08,
  "AU_authenticity_voice": 0.06,
  "EM_emotional_impact": 0.06,
  "NA_narrative_strength": 0.05,
  "PN_platform_nativeness": 0.05,
  "CC_cultural_contribution": 0.04,
}
if os.path.exists(WEIGHTS_JSON):
    try:
        with open(WEIGHTS_JSON, "r", encoding="utf-8") as f:
            w = json.load(f)
            DEFAULT_WEIGHTS.update({k: float(v) for k,v in w.items() if k in DEFAULT_WEIGHTS})
    except Exception:
        pass

DIMENSIONS = list(DEFAULT_WEIGHTS.keys())
FLAG_COLS = ["flag_stereotype","flag_misappropriation","flag_sensitive_timing","flag_other_risk","neg_sentiment_ratio_estimate"]

LABELS = {
    "CR_cultural_resonance": ("Cultural Resonance","Does it truly tap into the audience’s culture/scene? Insider cues, language, symbols."),
    "OR_originality": ("Originality","Is the concept surprising and fresh vs. prior work?"),
    "TI_timeliness": ("Timeliness","Is the timing right with trends, moments or seasons?"),
    "IE_inclusivity_ethics": ("Inclusivity & Ethics","Respectful and inclusive; no stereotypes or appropriation."),
    "SH_shareability": ("Shareability","Likely to be shared/remixed? Hooks, quotables, participatory formats."),
    "BF_brand_channel_fit": ("Brand & Channel Fit","Matches brand codes and exploits the channel’s strengths."),
    "CQ_craft_quality": ("Craft Quality","Execution: visuals, copy, sound, edit, pacing."),
    "AU_authenticity_voice": ("Authenticity / Voice","Does it feel credible and ‘of the culture’ rather than forced?"),
    "EM_emotional_impact": ("Emotional Impact","Does it trigger emotion (humor, awe, tension, empathy)?"),
    "NA_narrative_strength": ("Narrative Strength","Is there a memorable story/arc people can retell?"),
    "PN_platform_nativeness": ("Platform-Nativeness","Is it designed for the platform (not a generic port)?"),
    "CC_cultural_contribution": ("Cultural Contribution","Does it add something new (meme, slogan, norm) to culture?"),
}

CHANNEL_OPTIONS = ["TikTok","Instagram","YouTube","OOH","TV","Radio","Integrated","Other"]
AUDIENCE_OPTIONS = [
    "BE urban 16-24","BE Gen Z 18-24","BE mainstream 25-44",
    "NL mainstream 25-44","EU mainstream 25-44","FR urban 18-34","DE mainstream 18-49",
    "Other..."
]
RATER_OPTIONS = ["Lode","Maarten"]

def ensure_csv(path):
    if not os.path.exists(path):
        cols = ["campaign_id","rater_id","rater_notes",
                "campaign_name","brand","channel","scene_audience","country","submit_date_iso","asset_youtube_url",
                *DIMENSIONS, *FLAG_COLS]
        pd.DataFrame(columns=cols).to_csv(path, index=False)

def load_ratings():
    ensure_csv(RATINGS_CSV)
    try:
        return pd.read_csv(RATINGS_CSV)
    except Exception:
        return pd.DataFrame(columns=["campaign_id","rater_id","rater_notes",
                                     "campaign_name","brand","channel","scene_audience","country","submit_date_iso","asset_youtube_url",
                                     *DIMENSIONS, *FLAG_COLS])

def save_rating(row: dict):
    df = load_ratings()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RATINGS_CSV, index=False)

def next_campaign_id(df: pd.DataFrame) -> str:
    if df.empty or "campaign_id" not in df.columns or df["campaign_id"].dropna().empty:
        return "CMP001"
    last = str(df["campaign_id"].dropna().iloc[-1])
    m = re.match(r"([A-Za-z]*)(\d+)$", last)
    if m:
        prefix, num = m.group(1) or "CMP", m.group(2)
        return f"{prefix}{int(num)+1:03d}"
    return f"CMP{len(df)+1:03d}"

def _to_0_100(x):
    return (pd.to_numeric(x, errors="coerce") - 1.0)/4.0*100.0

def _concave(x100, gamma=0.85):
    x01 = np.clip(x100/100.0, 0, 1)
    y01 = np.power(x01, gamma)
    return 100.0 * y01

def _risk_penalty(flags):
    f = int(flags.get("flag_stereotype", 0)) + int(flags.get("flag_misappropriation", 0)) \
        + int(flags.get("flag_sensitive_timing", 0)) + int(flags.get("flag_other_risk", 0))
    p = -3.0 * f
    if f >= 2: p += -4.0
    p += -12.0 * float(flags.get("neg_sentiment_ratio_estimate", 0.0))
    return p

def _timeliness_boost(ti100):
    return 0.98 + 0.08 * (ti100/100.0)

def _normalize_weights(w: dict) -> dict:
    s = sum(max(0.0, float(v)) for v in w.values()) or 1.0
    return {k: max(0.0, float(v))/s for k,v in w.items()}

def compute_ccr_single(scores_1to5: dict, weights: dict, flags: dict) -> float:
    w_norm = _normalize_weights(weights)
    scaled = {d: _concave(_to_0_100(scores_1to5.get(d, 3.0))) for d in DIMENSIONS}
    core = sum(w_norm[d]*scaled[d] for d in DIMENSIONS)
    ti100_raw = _to_0_100(scores_1to5.get("TI_timeliness", 3.0))
    core *= _timeliness_boost(ti100_raw)
    out = core + _risk_penalty(flags)
    return float(np.clip(out, 0.0, 100.0))

def live_ccr_preview(scores: dict, flags: dict) -> float:
    return compute_ccr_single(scores, DEFAULT_WEIGHTS, flags)

def compute_results(weights: dict = None) -> pd.DataFrame:
    if weights is None: weights = DEFAULT_WEIGHTS
    df = load_ratings()
    if df.empty: return pd.DataFrame()
    for c in FLAG_COLS:
        if c not in df.columns: df[c] = 0
    def row_ccr(row):
        scores = {d: row.get(d, 3.0) for d in DIMENSIONS}
        flags = {c: row.get(c, 0) for c in FLAG_COLS}
        return compute_ccr_single(scores, weights, flags)
    df["CCR_rater"] = df.apply(row_ccr, axis=1)
    if "rater_id" in df.columns and df["rater_id"].notna().any():
        z = df.groupby("rater_id")["CCR_rater"].transform(lambda s: (s - s.mean()) / (s.std(ddof=0) + 1e-9))
        df["CCR_rater"] = 0.85*df["CCR_rater"] + 0.15*(50 + 10*z)
    agg = {**{d: "mean" for d in DIMENSIONS}, **{c: "mean" for c in FLAG_COLS}, "CCR_rater":"mean",
           "campaign_name":"first","brand":"first","channel":"first","scene_audience":"first","country":"first","asset_youtube_url":"first"}
    grouped = df.groupby("campaign_id", dropna=False).agg(agg).reset_index()
    grouped.rename(columns={"CCR_rater":"CCR_mean"}, inplace=True)
    grouped.to_csv(RESULTS_CSV, index=False)
    return grouped

# Session state
if "step" not in st.session_state: st.session_state.step = "Campaign Information"
if "info" not in st.session_state:
    df0 = load_ratings()
    st.session_state.info = {
        "campaign_id": next_campaign_id(df0),
        "campaign_name": "", "brand": "", "channel": CHANNEL_OPTIONS[0],
        "scene_audience_choice": AUDIENCE_OPTIONS[0], "scene_audience_custom": "",
        "country": "BE", "submit_date_iso": str(date.today()),
        "asset_youtube_url": "", "rater_id": "Lode", "rater_notes": "",
    }
if "scores" not in st.session_state: st.session_state.scores = {d: 3.0 for d in DIMENSIONS}
if "risks" not in st.session_state: st.session_state.risks = {"flag_stereotype":0,"flag_misappropriation":0,"flag_sensitive_timing":0,"flag_other_risk":0,"neg_sentiment_ratio_estimate":0.0}

# Title & CSS
st.title("Culturally Creative & Relevant Rater")
st.markdown("<style>.sticky-right{position:sticky;top:12px;}</style>", unsafe_allow_html=True)

# Stepper
try:
    st.session_state.step = st.segmented_control("Step", options=["Campaign Information","Evaluation","Results"], default=st.session_state.step)
except Exception:
    st.session_state.step = st.radio("Step", ["Campaign Information","Evaluation","Results"],
                                     index=["Campaign Information","Evaluation","Results"].index(st.session_state.step), horizontal=True)

# Campaign Information
if st.session_state.step == "Campaign Information":
    st.subheader("Campaign Information")
    c_left, c_right = st.columns(2)
    with c_left:
        st.session_state.info["campaign_id"] = st.text_input("Campaign ID *", value=st.session_state.info["campaign_id"])
        bn1, bn2 = st.columns(2)
        with bn1:
            st.session_state.info["brand"] = st.text_input("Brand", value=st.session_state.info["brand"])
        with bn2:
            st.session_state.info["campaign_name"] = st.text_input("Name", value=st.session_state.info["campaign_name"])
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
                                                               value=st.session_state.info["asset_youtube_url"],
                                                               placeholder="https://www.youtube.com/watch?v=...")
    st.session_state.info["rater_notes"] = st.text_area("Rater notes", value=st.session_state.info["rater_notes"],
                                                        height=90, placeholder="Key observations, insider cues, etc.")
    if st.button("Next →", type="primary"):
        st.session_state.step = "Evaluation"
        st.rerun()

# Evaluation
elif st.session_state.step == "Evaluation":
    st.subheader("Evaluation")
    left, right = st.columns([1.65, 1])
    with left:
        for d in DIMENSIONS:
            title, desc = LABELS[d]
            st.markdown(f"**{title}**")
            st.caption(desc)
            st.session_state.scores[d] = st.slider("", 1.0, 5.0, st.session_state.scores[d], 0.5, key=f"score_{d}")
        r1, r2, r3, r4 = st.columns(4)
        with r1: st.session_state.risks["flag_stereotype"] = int(st.checkbox("Stereotype", value=bool(st.session_state.risks["flag_stereotype"])))
        with r2: st.session_state.risks["flag_misappropriation"] = int(st.checkbox("Misappropriation", value=bool(st.session_state.risks["flag_misappropriation"])))
        with r3: st.session_state.risks["flag_sensitive_timing"] = int(st.checkbox("Sensitive timing", value=bool(st.session_state.risks["flag_sensitive_timing"])))
        with r4: st.session_state.risks["flag_other_risk"] = int(st.checkbox("Other risk", value=bool(st.session_state.risks["flag_other_risk"])))
        st.session_state.risks["neg_sentiment_ratio_estimate"] = st.slider("Negative sentiment ratio (0–1)", 0.0, 1.0, float(st.session_state.risks["neg_sentiment_ratio_estimate"]), 0.01)
        st.write("")
        if st.button("Save evaluation", type="primary"):
            info = st.session_state.info
            audience = info["scene_audience_custom"] if info["scene_audience_choice"] == "Other..." else info["scene_audience_choice"]
            if not info["campaign_id"].strip():
                st.error("Campaign ID is required.")
            else:
                row = {"campaign_id": info["campaign_id"].strip(),
                       "campaign_name": info["campaign_name"].strip(),
                       "brand": info["brand"].strip(),
                       "channel": info["channel"],
                       "scene_audience": audience.strip(),
                       "country": info["country"].strip(),
                       "submit_date_iso": info["submit_date_iso"].strip(),
                       "asset_youtube_url": info["asset_youtube_url"].strip(),
                       "rater_id": info["rater_id"],
                       "rater_notes": info["rater_notes"],
                       **st.session_state.scores, **st.session_state.risks}
                save_rating(row)
                df_after = load_ratings()
                st.session_state.info["campaign_id"] = next_campaign_id(df_after)
                st.success("Saved.")
                st.session_state.step = "Results"
                st.rerun()
    with right:
        st.markdown('<div class="sticky-right">', unsafe_allow_html=True)
        live = live_ccr_preview(st.session_state.scores, st.session_state.risks)
        st.subheader("📊 Live CCR")
        st.markdown(f"<div style='font-size:72px;font-weight:800;line-height:1;'> {live:.0f}% </div>", unsafe_allow_html=True)
        st.caption("Weighted by the improved algorithm")
        if st.session_state.info["asset_youtube_url"]:
            st.markdown("---"); st.caption("YouTube preview"); st.video(st.session_state.info["asset_youtube_url"])
        st.markdown('</div>', unsafe_allow_html=True)

# Results
else:
    st.subheader("Results")
    st.markdown("**Dataset (all evaluations)**")
    st.dataframe(load_ratings(), use_container_width=True)
    st.markdown("---")
    st.markdown("**Per-campaign results**")
    res = compute_results()
    if not res.empty:
        st.dataframe(res, use_container_width=True)
        st.download_button("Download CCR_results.csv", res.to_csv(index=False).encode("utf-8"),
                           file_name="CCR_results.csv", mime="text/csv")
    else:
        st.info("No results yet — add at least one evaluation.")
