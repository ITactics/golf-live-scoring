import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="Golf TV Scoreboard", layout="wide")

# ======================
# DB
# ======================
engine = create_engine(st.secrets["DB_URL"])

def load_data():
    return pd.read_sql("select * from scores", engine)

df = load_data()

st.title("📺 GOLF LIVE BROADCAST")

# ======================
# TEAMS
# ======================
st.sidebar.header("🏌️ Матч")

team1 = st.sidebar.text_input("Команда 1")
team2 = st.sidebar.text_input("Команда 2")

if team1 == "" or team2 == "":
    st.warning("Введите команды в боковой панели")
    st.stop()

# ======================
# MATCH LOGIC
# ======================
if not df.empty:

    match = df.groupby(["hole", "team"])["strokes"].min().unstack()

    match = match.reindex(columns=[team1, team2]).fillna(999)

    results = []
    a_score = 0
    b_score = 0

    for _, row in match.iterrows():

        a = row.get(team1, 999)
        b = row.get(team2, 999)

        if a == 999 or b == 999:
            results.append("⚪")
            continue

        if a < b:
            a_score += 1
            results.append("🟢")
        elif b < a:
            b_score += 1
            results.append("🔴")
        else:
            results.append("🔵")

    # ======================
    # TV HEADER
    # ======================
    st.markdown("## 📺 LIVE MATCH")

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.metric(team1, a_score)

    with col2:
        if a_score > b_score:
            st.markdown(f"<h1 style='text-align:center;color:green;'>🟢 {team1} LEADING</h1>", unsafe_allow_html=True)
        elif b_score > a_score:
            st.markdown(f"<h1 style='text-align:center;color:red;'>🔴 {team2} LEADING</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align:center;color:blue;'>🔵 ALL SQUARE</h1>", unsafe_allow_html=True)

    with col3:
        st.metric(team2, b_score)

    # ======================
    # HOLE BOARD (TV STYLE)
    # ======================
    st.markdown("### 🏌️ Hole by Hole")

    board = match.copy()
    board["Result"] = results

    def style(val):
        if val == "🟢":
            return "background-color: #2ecc71"
        if val == "🔴":
            return "background-color: #e74c3c"
        if val == "🔵":
            return "background-color: #3498db"
        return "background-color: #bdc3c7"

    st.dataframe(
        board.style.applymap(style, subset=["Result"]),
        use_container_width=True
    )

# ======================
# EMPTY STATE
# ======================
else:
    st.info("Нет данных — добавьте результаты")
