import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Golf Live", layout="wide")

st.title("⛳ Golf Match Play (MVP)")

# ======================
# LOCAL STORAGE (CSV)
# ======================
FILE = "scores.csv"

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["team", "player", "hole", "par", "strokes", "putts"])

# ======================
# TEAMS
# ======================
st.header("🏌️ Команды")

team1 = st.text_input("Команда 1", value="Team A")
team2 = st.text_input("Команда 2", value="Team B")

# ======================
# INPUT
# ======================
st.header("📱 Ввод результата")

col1, col2 = st.columns(2)

with col1:
    player = st.text_input("Игрок")
    team = st.selectbox("Команда", [team1, team2])
    hole = st.selectbox("Лунка", list(range(1, 19)))

with col2:
    par = st.selectbox("Пар", [3, 4, 5])
    strokes = st.number_input("Удары", 1, 15, 4)
    putts = st.number_input("Патты", 0, 6, 2)

if st.button("Сохранить"):
    new_row = pd.DataFrame([{
        "team": team,
        "player": player,
        "hole": hole,
        "par": par,
        "strokes": strokes,
        "putts": putts
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE, index=False)

    st.success("Сохранено!")

# ======================
# SCOREBOARD
# ======================
st.header("🏆 Матч")

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
    # STATUS
    # ======================
    if a_score > b_score:
        st.success(f"🟢 {team1} ведёт {a_score - b_score} UP")
    elif b_score > a_score:
        st.error(f"🔴 {team2} ведёт {b_score - a_score} UP")
    else:
        st.info("🔵 ALL SQUARE")

    # ======================
    # TABLE
    # ======================
    match["Result"] = results + [""] * (len(match) - len(results))
    st.dataframe(match, use_container_width=True)

# ======================
# RAW DATA
# ======================
st.markdown("---")
st.subheader("📋 Все данные")
st.dataframe(df)
