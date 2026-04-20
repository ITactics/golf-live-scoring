import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Golf TV Live", layout="wide")

FILE = "scores.csv"

# ======================
# DATA
# ======================
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["team", "player", "hole", "par", "strokes", "putts"])

# ======================
# STYLE (TV LOOK)
# ======================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1d13, #000000);
    color: white;
}
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}
h1, h2, h3, label, p {
    color: white !important;
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08);
    padding: 10px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# SIDEBAR (DESIGN)
# ======================
st.sidebar.header("🎨 Дизайн")

logo = st.sidebar.file_uploader("Логотип турнира", type=["png", "jpg", "jpeg"])
bg_url = st.sidebar.text_input("URL фона (опционально)")

format_type = st.sidebar.selectbox("Формат игры", ["9-9-18", "6-6-6-18"])

team1 = st.sidebar.text_input("Команда 1", "Team A")
team2 = st.sidebar.text_input("Команда 2", "Team B")

# background image
if bg_url:
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{bg_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)

# ======================
# HEADER
# ======================
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if logo:
        st.image(logo, width=120)

with col_title:
    st.title("⛳ GOLF LIVE TV SCOREBOARD")

# ======================
# INPUT
# ======================
st.header("📱 Live Marker Input")

c1, c2 = st.columns(2)

with c1:
    player = st.text_input("Игрок")
    team = st.selectbox("Команда", [team1, team2])
    hole = st.selectbox("Лунка", list(range(1, 19)))

with c2:
    par = st.selectbox("Пар", [3, 4, 5])
    strokes = st.number_input("Удары", 1, 15, 4)
    putts = st.number_input("Патты", 0, 6, 2)

if st.button("💾 Сохранить"):
    new = pd.DataFrame([{
        "team": team,
        "player": player,
        "hole": hole,
        "par": par,
        "strokes": strokes,
        "putts": putts
    }])

    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(FILE, index=False)
    st.success("Сохранено")

# ======================
# FILTER FORMAT
# ======================
if format_type == "9-9-18":
    holes_allowed = list(range(1, 19))
else:
    holes_allowed = list(range(1, 19))

df = df[df["hole"].isin(holes_allowed)]

# ======================
# MATCH LOGIC
# ======================
st.markdown("## 🏆 LIVE MATCH")

if not df.empty:

    match = df.groupby(["hole", "team"])["strokes"].min().unstack()
    match = match.reindex(columns=[team1, team2]).fillna(999)

    a_score = 0
    b_score = 0
    results = []

    for _, row in match.iterrows():

        a = row.get(team1, 999)
        b = row.get(team2, 999)

        if a == 999 or b == 999:
            results.append("")
            continue

        if a < b:
            a_score += 1
            results.append(f"🟢 {team1}")
        elif b < a:
            b_score += 1
            results.append(f"🔴 {team2}")
        else:
            results.append("🔵 AS")

    # ======================
    # SCOREBOARD TV STYLE
    # ======================
    col1, col2, col3 = st.columns([2,3,2])

    with col1:
        st.metric(team1, a_score)

    with col2:
        if a_score > b_score:
            st.markdown(f"<h1 style='text-align:center;color:#00ff88;'>🟢 {team1} LEADING</h1>", unsafe_allow_html=True)
        elif b_score > a_score:
            st.markdown(f"<h1 style='text-align:center;color:#ff4d4d;'>🔴 {team2} LEADING</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align:center;color:#4da6ff;'>🔵 ALL SQUARE</h1>", unsafe_allow_html=True)

    with col3:
        st.metric(team2, b_score)

    # ======================
    # HOLE TABLE
    # ======================
    match["Result"] = results + [""] * (len(match) - len(results))

    st.dataframe(match, use_container_width=True)

# ======================
# TEAM VIEW (CLICK FEEL)
# ======================
st.markdown("---")
st.subheader("🏌️ Команды")

tab1, tab2 = st.tabs([team1, team2])

with tab1:
    st.dataframe(df[df["team"] == team1])

with tab2:
    st.dataframe(df[df["team"] == team2])
