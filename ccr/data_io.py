import os, re
import pandas as pd
from .algorithm import DIMENSIONS, FLAG_COLS

DATA_DIR = "data"
RATINGS_CSV = os.path.join(DATA_DIR, "CCR_ratings.csv")
RESULTS_CSV = os.path.join(DATA_DIR, "CCR_results.csv")
os.makedirs(DATA_DIR, exist_ok=True)

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
