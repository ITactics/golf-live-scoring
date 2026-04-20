import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Golf TV Live", layout="wide")

FILE = "scores.csv"
TEAMS_FILE = "teams.txt"  # Файл для хранения названий команд

# ======================
# СИСТЕМНАЯ ЛОГИКА (Команды)
# ======================
def load_teams():
    if os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Team A", "Team B"]

def save_teams(teams):
    with open(TEAMS_FILE, "w", encoding="utf-8") as f:
        for team in teams:
            f.write(f"{team}\n")

if 'team_list' not in st.session_state:
    st.session_state.team_list = load_teams()

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
st.sidebar.subheader("👥 Менеджер команд")

# 1. Добавление
new_team = st.sidebar.text_input("Название новой команды")
if st.sidebar.button("➕ Добавить"):
    if new_team and new_team not in st.session_state.team_list:
        st.session_state.team_list.append(new_team)
        if 'save_teams' in globals(): save_teams(st.session_state.team_list)
        st.rerun()

# 2. Удаление конкретной команды
if len(st.session_state.team_list) > 0:
    team_to_delete = st.sidebar.selectbox("Выбрать команду для удаления", options=st.session_state.team_list)
    if st.sidebar.button("🗑 Удалить выбранную"):
        st.session_state.team_list.remove(team_to_delete)
        if 'save_teams' in globals(): save_teams(st.session_state.team_list)
        st.rerun()

st.sidebar.markdown("---")
# Кнопка полной очистки (на всякий случай)
if st.sidebar.button("⚠️ Сбросить всё к Team A/B"):
    st.session_state.team_list = ["Team A", "Team B"]
    if 'save_teams' in globals(): save_teams(st.session_state.team_list)
    st.rerun()

if bg_url:
    st.markdown(f"<style>.stApp {{ background-image: url('{bg_url}'); }}</style>", unsafe_allow_html=True)

# ======================
# HEADER (Выравнивание лого)
# ======================
header_col1, header_col2 = st.columns([1, 6]) # Подобрал пропорции для красоты

with header_col1:
    if logo:
        st.image(logo, width=100)
    else:
        st.markdown("<h1 style='margin:0;'>⛳</h1>", unsafe_allow_html=True)

with header_col2:
    st.markdown("<h1 style='margin-top: 15px; margin-left: -20px;'>GOLF LIVE</h1>", unsafe_allow_html=True)

# ======================
# INPUT
# ======================
st.header("📱 Live Marker Input")

c1, c2 = st.columns(2)

with c1:
    player = st.text_input("Игрок")
    # Список команд теперь всегда актуален
    team = st.selectbox("Команда", options=st.session_state.team_list)
    hole = st.selectbox("Лунка", list(range(1, 19)))

with c2:
    par = st.selectbox("Пар", [3, 4, 5])
    strokes = st.number_input("Удары", 1, 15, 4)
    putts = st.number_input("Патты", 0, 6, 2)

if st.button("💾 Сохранить результат"):
    new_data = pd.DataFrame([{"team": team, "player": player, "hole": hole, "par": par, "strokes": strokes, "putts": putts}])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE, index=False)
    st.success(f"Данные для {player} ({team}) сохранены!")

# ======================
# MATCH LOGIC
# ======================
st.markdown("## 🏆 LIVE MATCH")

if not df.empty and len(st.session_state.team_list) >= 2:
    # Берем первые две команды из актуального списка
    t1 = st.session_state.team_list[0]
    t2 = st.session_state.team_list[1]
    
    match = df.groupby(["hole", "team"])["strokes"].min().unstack()
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

    sc1, sc2, sc3 = st.columns([2, 3, 2])
    with sc1:
        st.metric(t1, a_score)
    with sc2:
        if a_score > b_score:
            st.markdown(f"<h2 style='text-align:center;color:#00ff88;'>{t1} LEADING</h2>", unsafe_allow_html=True)
        elif b_score > a_score:
            st.markdown(f"<h2 style='text-align:center;color:#ff4d4d;'>{t2} LEADING</h2>", unsafe_allow_html=True)
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


# ======================
# ДЕМО-РЕЖИМ (Добавьте в конец файла)
# ======================
st.sidebar.markdown("---")
if st.sidebar.button("🚀 Запустить демо-матч"):
    # Создаем тестовые данные
    demo_data = [
        {"team": "BMW", "player": "Иван", "hole": 1, "par": 4, "strokes": 4, "putts": 2},
        {"team": "Audi", "player": "Петр", "hole": 1, "par": 4, "strokes": 5, "putts": 3},
        {"team": "BMW", "player": "Иван", "hole": 2, "par": 3, "strokes": 3, "putts": 1},
        {"team": "Audi", "player": "Петр", "hole": 2, "par": 3, "strokes": 3, "putts": 2},
        {"team": "BMW", "player": "Иван", "hole": 3, "par": 5, "strokes": 6, "putts": 2},
        {"team": "Audi", "player": "Петр", "hole": 3, "par": 5, "strokes": 4, "putts": 1},
    ]
    
    # Убеждаемся, что эти команды есть в списке
    st.session_state.team_list = ["BMW", "Audi"]
    save_teams(st.session_state.team_list)
    
    # Сохраняем в CSV
    demo_df = pd.DataFrame(demo_data)
    demo_df.to_csv(FILE, index=False)
    
    st.rerun()

