import streamlit as st

st.set_page_config(page_title="How the CCR Algorithm Works", page_icon="🧪", layout="wide")
st.title("How the CCR Algorithm Works")
st.markdown("### Transparent, interpretable, and adaptable")

st.markdown("""
The CCR Algorithm evaluates cultural creativity and relevance by balancing *craft, timing, and ethical sensitivity*.
Each score (1–5) is normalized (0–100), passed through a concave scaling function, weighted, boosted for timeliness, and reduced for cultural risks.

**Key features:**
- **12 dimensions** of creativity and cultural fit
- **Concave scaling** to reward above-average work more than mediocre work
- **Risk penalties** for stereotypes, appropriation, or negative sentiment
- **Light de-biasing** across raters for fairness
- **Output:** a single **CCR Score (0–100%)** indicating cultural creativity & relevance
""")
