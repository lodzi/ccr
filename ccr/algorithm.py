import json, os
import numpy as np
import pandas as pd

DATA_DIR = "data"
WEIGHTS_JSON = os.path.join(DATA_DIR, "CCR_default_weights.json")

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
            for k, v in w.items():
                if k in DEFAULT_WEIGHTS:
                    DEFAULT_WEIGHTS[k] = float(v)
    except Exception:
        pass

DIMENSIONS = list(DEFAULT_WEIGHTS.keys())
FLAG_COLS = ["flag_stereotype","flag_misappropriation","flag_sensitive_timing","flag_other_risk","neg_sentiment_ratio_estimate"]

LABELS = {
    "CR_cultural_resonance": ("Cultural Resonance","How well the campaign taps into the audience’s cultural context, language, and symbols."),
    "OR_originality": ("Originality","Freshness and novelty of the concept compared to existing cultural work."),
    "TI_timeliness": ("Timeliness","Relevance to current trends, moments, or social context."),
    "IE_inclusivity_ethics": ("Inclusivity & Ethics","Sensitivity, fairness, and avoidance of stereotypes or appropriation."),
    "SH_shareability": ("Shareability","Likelihood of being shared, remixed, or reinterpreted."),
    "BF_brand_channel_fit": ("Brand & Channel Fit","How well the idea fits the brand voice and leverages the medium."),
    "CQ_craft_quality": ("Craft Quality","Overall execution quality: copywriting, visuals, sound, editing, rhythm."),
    "AU_authenticity_voice": ("Authenticity / Voice","Cultural credibility—feels organic and truthful rather than imposed."),
    "EM_emotional_impact": ("Emotional Impact","Strength of emotion triggered—humor, empathy, awe, tension."),
    "NA_narrative_strength": ("Narrative Strength","Clarity and memorability of the story or idea arc."),
    "PN_platform_nativeness": ("Platform Nativeness","Designed specifically for the platform, not a cross-post."),
    "CC_cultural_contribution": ("Cultural Contribution","Adds new cultural meaning—a phrase, visual code, or behavior."),
}

def _to_0_100(x):
    return (pd.to_numeric(x, errors="coerce") - 1.0)/4.0*100.0

def _concave(x100, gamma=0.85):
    x01 = np.clip(x100/100.0, 0, 1)
    y01 = np.power(x01, gamma)
    return 100.0 * y01

def _risk_penalty(flags):
    f = int(flags.get("flag_stereotype", 0)) + int(flags.get("flag_misappropriation", 0)) + int(flags.get("flag_sensitive_timing", 0)) + int(flags.get("flag_other_risk", 0))
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
