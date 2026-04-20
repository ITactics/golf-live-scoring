import streamlit as st
import pandas as pd
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st_autorefresh(interval=2000)

FILE = "data.csv"

# INIT
if not os.path.exists(FILE):
    pd.DataFrame(columns=[
        "Team","Player","Hole","Par",
        "Strokes","Putts","Fairway","GIR"
    ]).to_csv(FILE,index=False)

df = pd.read_csv(FILE)

st.title("⛳ Golf Match Play Live")

# ===== INPUT =====
st.header("📱 Marker Input")

team = st.selectbox("Team", ["A","B"])
player = st.text_input("Player")
hole = st.selectbox("Hole", list(range(1,19)))
par = st.selectbox("Par", [3,4,5])
strokes = st.number_input("Strokes",1,15)
putts = st.number_input("Putts",0,6)

fairway = st.checkbox("Fairway Hit")
gir = st.checkbox("GIR")

if st.button("Save"):
    df.loc[len(df)] = [team,player,hole,par,strokes,putts,fairway,gir]
    df.to_csv(FILE,index=False)
    st.success("Saved")

# ===== CALCULATIONS =====
if not df.empty:

    # auto GIR if not checked
    df["Auto_GIR"] = df["Strokes"] <= (df["Par"] - 2)
    df["GIR_Final"] = df["GIR"] | df["Auto_GIR"]

    # up & down
    df["UpDown"] = (~df["GIR_Final"]) & (df["Strokes"] <= df["Par"])

    # ===== TEAM RESULT =====
    hole_result = df.groupby(["Hole","Team"])["Strokes"].min().unstack()

    hole_result["Result"] = hole_result.apply(
        lambda x: 1 if x["A"] < x["B"]
        else (-1 if x["A"] > x["B"] else 0),
        axis=1
    )

    total = hole_result["Result"].sum()

    st.header(f"🏆 Match Score: {total}")

    # ===== COLORS =====
    def color(val):
        if val == 1:
            return "background-color: green"
        elif val == -1:
            return "background-color: red"
        else:
            return "background-color: blue"

    st.dataframe(
        hole_result.style.applymap(color, subset=["Result"]),
        use_container_width=True
    )

    # ===== STATS =====
    st.header("📊 Stats")

    stats = df.groupby("Player").agg({
        "Putts":"sum",
        "Fairway":"mean",
        "GIR_Final":"mean",
        "UpDown":"mean"
    })

    st.dataframe(stats)
