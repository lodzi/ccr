import streamlit as st
import pandas as pd

st.set_page_config(page_title="How the CCR Algorithm Works", page_icon="🧪", layout="wide")
st.title("How the CCR Algorithm Works")

st.markdown("""
### Transparency and Methodology

The Culturally Creative & Relevant (CCR) Algorithm measures the creative and cultural value of campaigns in a transparent, data-informed way.  
It combines quantitative structure with qualitative judgment, translating expert assessment into a single percentage score.

---
""")

st.header("The Dimensions and Weights")

data = [
    ("Cultural Resonance", 0.18, "How well the campaign taps into the audience’s cultural context, language, and symbols."),
    ("Originality", 0.12, "Freshness and novelty of the concept compared to existing cultural work."),
    ("Timeliness", 0.10, "Relevance to current trends, moments, or social context."),
    ("Inclusivity & Ethics", 0.08, "Sensitivity, fairness, and avoidance of stereotypes or appropriation."),
    ("Shareability", 0.10, "Likelihood of being shared, remixed, or reinterpreted."),
    ("Brand & Channel Fit", 0.08, "How well the idea fits the brand voice and leverages the medium."),
    ("Craft Quality", 0.08, "Overall execution quality: copywriting, visuals, sound, editing, rhythm."),
    ("Authenticity / Voice", 0.06, "Cultural credibility—feels organic and truthful rather than imposed."),
    ("Emotional Impact", 0.06, "Strength of emotion triggered—humor, empathy, awe, tension."),
    ("Narrative Strength", 0.05, "Clarity and memorability of the story or idea arc."),
    ("Platform Nativeness", 0.05, "Designed specifically for the platform, not a cross-post."),
    ("Cultural Contribution", 0.04, "Adds new cultural meaning—a phrase, visual code, or behavior."),
]

df = pd.DataFrame(data, columns=["Dimension", "Weight", "Description"])
st.table(df)

st.markdown("""
---
### Scoring Process

Each campaign is evaluated across the 12 dimensions on a scale from 1 (low) to 5 (high).  
The algorithm then applies several steps to produce a consistent and interpretable CCR Score.

1. **Normalization**  
   Convert all 1–5 ratings into a 0–100 range.

2. **Concave Scaling**  
   A mild non-linear curve (gamma = 0.85) rewards outstanding work exponentially more than average work.

3. **Weighting**  
   Multiply each scaled dimension by its corresponding weight from the table above.

4. **Timeliness Boost**  
   Campaigns strongly aligned with cultural or social timing can receive up to an 8% bonus.

5. **Risk Penalty**  
   Deductions are applied for problematic or insensitive aspects:
   - -3 points per ethical/cultural flag  
   - -4 additional if two or more flags apply  
   - -12 × (estimated negative sentiment ratio)

6. **Final CCR Score**  
   All values are summed, adjusted for boosts and penalties, and then clamped between 0 and 100.  
   The result represents the campaign’s **Cultural Creativity & Relevance** percentage.

---
### Version and Improvement

This framework is a living system. It will evolve through dialogue, data, and collective feedback.  
If you believe the weighting should shift, or that new dimensions should be considered, you are welcome to share suggestions.

**Feedback and collaboration:** [hello@thisisdefiant.com](mailto:hello@thisisdefiant.com)

---
""")

# Back button
st.markdown(
    """
    <div style='text-align:center; margin-top:40px;'>
        <a href='/' style='text-decoration:none;'>
            <button style='
                background-color:#111;
                color:white;
                border:none;
                border-radius:8px;
                padding:12px 28px;
                font-size:16px;
                cursor:pointer;
            '>Back to CCR Rater</button>
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
