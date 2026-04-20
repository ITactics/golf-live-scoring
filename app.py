import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Golf Live Scoreboard", layout="wide")

# ======================
# DATA STORAGE
# ======================
SCORES_FILE = "scores.csv"
PLAYERS_FILE = "players.csv"

if not os.path.exists(SCORES_FILE):
    pd.DataFrame(columns=["Team", "Player", "Hole", "Par", "Strokes", "Putts"]).to_csv(SCORES_FILE, index=False)

if not os.path.exists(PLAYERS_FILE):
    pd.DataFrame(columns=["Player", "Team"]).to_csv(PLAYERS_FILE, index=False)

scores = pd.read_csv(SCORES_FILE)
players = pd.read_csv(PLAYERS_FILE)

st.title("⛳ PGA Style Live Match Scoreboard")

# ======================
# ADD PLAYER
# ======================
with st.expander("➕ Add Player"):
    name = st.text_input("Player Name")
    team = st.selectbox("Team", ["A", "B"])

    if st.button("Add Player"):
        players.loc[len(players)] = [name, team]
        players.to_csv(PLAYERS_FILE, index=False)
        st.success("Player added!")

# ======================
# MARKER INPUT
# ======================
st.header("📱 Marker Input")

if not players.empty:

    player = st.selectbox("Player", players["Player"].tolist())
    team = players[players["Player"] == player]["Team"].values[0]

    hole = st.selectbox("Hole", list(range(1, 19)))
    par = st.selectbox("Par", [3, 4, 5])

    strokes = st.number_input("Strokes", 1, 15, 4)
    putts = st.number_input("Putts", 0, 6, 2)

    if st.button("Save Score"):
        scores.loc[len(scores)] = [team, player, hole, par, strokes, putts]
        scores.to_csv(SCORES_FILE, index=False)
        st.success("Saved!")

# ======================
# CALCULATIONS
# ======================
if not scores.empty:

    st.markdown("---")
    st.header("🏆 LIVE MATCH SCOREBOARD")

    df = scores.copy()

    # team best score per hole (match play logic)
    hole_match = df.groupby(["Hole", "Team"])["Strokes"].min().unstack()

    hole_match = hole_match.dropna()

    results = []

    for _, row in hole_match.iterrows():
        if row["A"] < row["B"]:
            results.append(("A", 1))
        elif row["A"] > row["B"]:
            results.append(("B", 1))
        else:
            results.append(("AS", 0))

    result_df = pd.DataFrame(results, columns=["Winner", "Point"])

    a_points = sum(1 for r in results if r[0] == "A")
    b_points = sum(1 for r in results if r[0] == "B")

    # ======================
    # MATCH STATUS
    # ======================
    if a_points > b_points:
        status = f"🟢 Team A is {a_points - b_points} UP"
    elif b_points > a_points:
        status = f"🔴 Team B is {b_points - a_points} UP"
    else:
        status = "🔵 ALL SQUARE"

    st.subheader(status)

    # ======================
    # SCOREBOARD TABLE
    # ======================
    display = hole_match.copy()
    display["Winner"] = result_df["Winner"].values

    def color(val):
        if val == "A":
            return "background-color: green"
        elif val == "B":
            return "background-color: red"
        else:
            return "background-color: blue"

    st.dataframe(
        display.style.applymap(color, subset=["Winner"]),
        use_container_width=True
    )

    # ======================
    # BIG SCORE CARDS
    # ======================
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Team A", a_points)

    with col2:
        st.metric("Team B", b_points)

    # ======================
    # PLAYER STATS
    # ======================
    st.markdown("---")
    st.header("📊 Player Stats")

    stats = df.groupby("Player").agg({
        "Strokes": "sum",
        "Putts": "sum",
        "Hole": "count"
    }).rename(columns={"Hole": "Holes Played"})

    st.dataframe(stats, use_container_width=True)
