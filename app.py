import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Golf TV Live", layout="wide")

FILE = "scores.csv"

# ======================
# СИСТЕМНАЯ ЛОГИКА (Команды)
# ======================
# Инициализируем список команд в памяти, если его еще нет
if 'team_list' not in st.session_state:
    st.session_state.team_list = ["Team A", "Team B"]

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
    background: url("https://images.unsplash.com/photo-1535131749006-b7f58c99034b");
    background-size: cover;
    background-position: center;
}
.block-container {
    background: rgba(0, 0, 0, 0.75);
    padding: 30px;
    border-radius: 20px;
    max-width: 1200px;
    margin-top: 50px;
}
h1, h2, h3, label, p, .stMarkdown {
    color: white !important;
}
/* Сделаем метрики крупнее и белее */
[data-testid="stMetricValue"] {
    color: white !important;
    font-size: 48px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# SIDEBAR (DESIGN & TEAMS)
# ======================
st.sidebar.header("🎨 Дизайн и Настройки")

logo = st.sidebar.file_uploader("Логотип турнира", type=["png", "jpg", "jpeg"])
bg_url = st.sidebar.text_input("URL фона (опционально)")
format_type = st.sidebar.selectbox("Формат игры", ["9-9-18", "6-6-6-18"])

st.sidebar.markdown("---")
st.sidebar.subheader("👥 Команды")

# Добавление новой команды
new_team = st.sidebar.text_input("Введите название команды")
if st.sidebar.button("➕ Добавить команду"):
    if new_team and new_team not in st.session_state.team_list:
        st.session_state.team_list.append(new_team)
        st.rerun()

# Отображение текущих команд с возможностью очистки
if st.sidebar.button("🗑 Очистить список"):
    st.session_state.team_list = []
    st.rerun()

# Применение кастомного фона
if bg_url:
    st.markdown(f"<style>.stApp {{ background-image: url('{bg_url}'); }}</style>", unsafe_allow_html=True)

# ======================
# HEADER (Логотип и Название в одну линию)
# ======================
header_col1, header_col2 = st.columns([1, 4])

with header_col1:
    if logo:
        st.image(logo, width=100)
    else:
        # Заглушка, если лого нет, чтобы текст не прыгал влево
        st.markdown("### ⛳")

with header_col2:
    # Выравниваем текст по вертикали относительно логотипа
    st.markdown("<h1 style='margin-top: 10px;'>GOLF LIVE</h1>", unsafe_allow_html=True)

# ======================
# INPUT
# ======================
st.header("📱 Live Marker Input")

c1, c2 = st.columns(2)

with c1:
    player = st.text_input("Игрок")
    # Используем динамический список из session_state
    team = st.selectbox("Команда", options=st.session_state.team_list)
    hole = st.selectbox("Лунка", list(range(1, 19)))

with c2:
    par = st.selectbox("Пар", [3, 4, 5])
    strokes = st.number_input("Удары", 1, 15, 4)
    putts = st.number_input("Патты", 0, 6, 2)

if st.button("💾 Сохранить результат"):
    new_data = pd.DataFrame([{
        "team": team,
        "player": player,
        "hole": hole,
        "par": par,
        "strokes": strokes,
        "putts": putts
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE, index=False)
    st.success(f"Данные для {player} сохранены!")

# ======================
# MATCH LOGIC (Улучшенная обработка для N-команд)
# ======================
st.markdown("## 🏆 LIVE MATCH")

if not df.empty and len(st.session_state.team_list) >= 2:
    # Для примера логики "Матч" возьмем первые две команды из списка
    t1, t2 = st.session_state.team_list[0], st.session_state.team_list[1]
    
    match = df.groupby(["hole", "team"])["strokes"].min().unstack()
    # Гарантируем наличие колонок даже если по ним еще нет данных
    for t in [t1, t2]:
        if t not in match.columns:
            match[t] = 999
            
    match = match.fillna(999)

    a_score, b_score = 0, 0
    results = []

    for _, row in match.iterrows():
        a, b = row[t1], row[t2]
        if a == 999 or b == 999:
            results.append("—")
        elif a < b:
            a_score += 1
            results.append(f"🟢 {t1}")
        elif b < a:
            b_score += 1
            results.append(f"🔴 {t2}")
        else:
            results.append("🔵 AS")

    # Scoreboard
    sc1, sc2, sc3 = st.columns([2, 3, 2])
    with sc1:
        st.metric(t1, a_score)
    with sc2:
        if a_score > b_score:
            st.markdown(f"<h2 style='text-align:center;color:#00ff88;'>{t1} UP</h2>", unsafe_allow_html=True)
        elif b_score > a_score:
            st.markdown(f"<h2 style='text-align:center;color:#ff4d4d;'>{t2} UP</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='text-align:center;color:#4da6ff;'>ALL SQUARE</h2>", unsafe_allow_html=True)
    with sc3:
        st.metric(t2, b_score)

    st.dataframe(match[[t1, t2]].replace(999, "-"), use_container_width=True)

# ======================
# TEAM VIEW
# ======================
st.markdown("---")
st.subheader("🏌️ Детальная статистика")

if st.session_state.team_list:
    tabs = st.tabs(st.session_state.team_list)
    for i, tab in enumerate(tabs):
        current_t = st.session_state.team_list[i]
        with tab:
            st.dataframe(df[df["team"] == current_t], use_container_width=True)
