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
# DATA (ОБНОВЛЕННЫЙ)
# ======================
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    # Создаем пустой файл с НОВЫМИ колонками, которые нужны для кнопок
    df = pd.DataFrame(columns=["match_id", "hole", "result", "pair_a", "pair_b"])
    df.to_csv(FILE, index=False)

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
# SIDEBAR (ОБНОВЛЕННЫЙ ПО ТЗ)
# ======================
st.sidebar.header("🎨 Дизайн и Настройки")

# 1. Логотип и фон (твоя логика сохранена)
uploaded_logo = st.sidebar.file_uploader("Логотип турнира", type=["png", "jpg", "jpeg"])
if uploaded_logo is not None:
    with open("temp_logo.png", "wb") as f:
        f.write(uploaded_logo.getbuffer())
    st.rerun()

bg_url = st.sidebar.text_input("URL фона (опционально)")
if bg_url:
    st.markdown(f"<style>.stApp {{ background-image: url('{bg_url}'); }}</style>", unsafe_allow_html=True)

# 2. ВЫБОР ВАРИАНТА ТУРНИРА (из нового ТЗ)
st.sidebar.markdown("---")
tour_variant = st.sidebar.radio(
    "Вариант турнира:",
    ["Вариант 1 (Красные vs Синие)", "Вариант 2 (14-16 команд)"]
)
format_type = st.sidebar.selectbox("Формат игры", ["9-9-18", "6-6-6-18"])

# 3. СОСТАВ ТЕКУЩЕГО МАТЧА (для Маркера)
st.sidebar.markdown("---")
st.sidebar.subheader("👥 Состав текущего матча")

col_a, col_b = st.sidebar.columns(2)
with col_a:
    st.write("**ПАРА А**")
    # Если Вариант 1 — выбор из "Красные/Синие", если Вариант 2 — из твоего списка команд
    list_for_a = ["Красные", "Синие"] if "Вариант 1" in tour_variant else st.session_state.team_list
    team_a = st.selectbox("Команда А", list_for_a, key="t_a")
    p_a1 = st.text_input("Игрок 1", "Слесарев", key="p_a1")
    p_a2 = st.text_input("Игрок 2", "Иванов", key="p_a2")

with col_b:
    st.write("**ПАРА Б**")
    list_for_b = ["Красные", "Синие"] if "Вариант 1" in tour_variant else st.session_state.team_list
    team_b = st.selectbox("Команда Б", list_for_b, index=1 if len(list_for_b)>1 else 0, key="t_b")
    p_b1 = st.text_input("Игрок 1", "Петров", key="p_b1")
    p_b2 = st.text_input("Игрок 2", "Сидоров", key="p_b2")

# 4. Твой старый Менеджер команд (скрыт в раскрывашку, чтобы не мешать маркеру)
with st.sidebar.expander("⚙️ Управление общим списком команд"):
    new_team = st.text_input("Название новой команды")
    if st.button("➕ Добавить"):
        if new_team and new_team not in st.session_state.team_list:
            st.session_state.team_list.append(new_team)
            save_teams(st.session_state.team_list)
            st.rerun()
    
    if len(st.session_state.team_list) > 0:
        team_to_delete = st.selectbox("Удалить команду", options=st.session_state.team_list)
        if st.button("🗑 Удалить"):
            st.session_state.team_list.remove(team_to_delete)
            save_teams(st.session_state.team_list)
            st.rerun()

# ======================
# HEADER (Логотип и Название)
# ======================
header_col1, header_col2 = st.columns([1, 6]) 

with header_col1:
    if os.path.exists("temp_logo.png"):
        st.image("temp_logo.png", width=100)
    else:
        st.markdown("<h1 style='margin:0;'>⛳</h1>", unsafe_allow_html=True)

with header_col2:
    st.markdown("<h1 style='margin-top: 15px; margin-left: -20px;'>GOLF LIVE</h1>", unsafe_allow_html=True)

# ======================
# СТРАНИЦА МАРКЕРА (ОБНОВЛЕННЫЙ ВВОД ПО ТЗ)
# ======================
st.markdown("---")
st.header("📱 Страница Маркера")

# Сетка лунок
hole_to_edit = st.selectbox("Выберите лунку для записи результата:", list(range(1, 19)))

st.write(f"Результат лунки №{hole_to_edit} для матча: **{team_a}** vs **{team_b}**")

# Три кнопки как на рисунке в ТЗ
col_btn1, col_btn2, col_btn3 = st.columns(3)

# Функция для сохранения результата
def save_winner(winner_val):
    global df
    # winner_val: 1 (Победа А), 0 (Ничья), 2 (Победа Б)
    new_entry = pd.DataFrame([{
        "match_id": f"{team_a}_vs_{team_b}", 
        "hole": hole_to_edit, 
        "result": winner_val,
        "pair_a": f"{p_a1}/{p_a2}",
        "pair_b": f"{p_b1}/{p_b2}"
    }])
    # Удаляем старую запись этой лунки для этого матча, если она была, и добавляем новую
    mask = (df['match_id'] == f"{team_a}_vs_{team_b}") & (df['hole'] == hole_to_edit)
    df = pd.concat([df[~mask], new_entry]).sort_values("hole")
    df.to_csv(FILE, index=False)
    st.toast(f"Лунка {hole_to_edit} сохранена!", icon="✅")
    time.sleep(0.5)
    st.rerun()

with col_btn1:
    if st.button(f"🏆 ВЫИГРЫШ {team_a}", use_container_width=True):
        save_winner(1)

with col_btn2:
    if st.button("🤝 НИЧЬЯ", use_container_width=True):
        save_winner(0)

with col_btn3:
    if st.button(f"🏆 ВЫИГРЫШ {team_b}", use_container_width=True):
        save_winner(2)

# ======================
# MATCH LOGIC (ОБНОВЛЕН ПОД ТЗ: КРУЖКИ И ФАМИЛИИ)
# ======================
st.markdown(f"## 🏆 LIVE MATCH: {team_a} vs {team_b}")

# Фильтруем данные только для текущего матча
current_match_id = f"{team_a}_vs_{team_b}"
m_df = df[df["match_id"] == current_match_id]

if not m_df.empty:
    # --- 1. ЛОГИКА ОТРЕЗКОВ (9-9-18 / 6-6-6-18) ---
    if format_type == "9-9-18":
        segments = [("Front 9", range(1, 10)), ("Back 9", range(10, 19)), ("Overall", range(1, 19))]
    else:
        segments = [("1st Six", range(1, 7)), ("2nd Six", range(7, 13)), ("3rd Six", range(13, 19)), ("Overall", range(1, 19))]

    seg_results = []
    total_points_a, total_points_b = 0, 0

    for name, h_range in segments:
        a_wins = len(m_df[(m_df["hole"].isin(h_range)) & (m_df["result"] == 1)])
        b_wins = len(m_df[(m_df["hole"].isin(h_range)) & (m_df["result"] == 2)])
        
        if a_wins > b_wins:
            seg_results.append((name, f"🟢 {team_a} / 🔴 {team_b}"))
            total_points_a += 1
        elif b_wins > a_wins:
            seg_results.append((name, f"🟢 {team_b} / 🔴 {team_a}"))
            total_points_b += 1
        else:
            seg_results.append((name, f"🔵 AS"))

    # Вывод карточек отрезков (ТВ-стиль)
    cols = st.columns(len(seg_results))
    for i, (name, res) in enumerate(seg_results):
        with cols[i]:
            st.markdown(f'<div style="background:rgba(255,255,255,0.1);padding:10px;border-radius:10px;text-align:center;"><p style="margin:0;font-size:12px;color:#aaa;">{name}</p><p style="margin:0;font-size:14px;font-weight:bold;">{res}</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- 2. ВИЗУАЛИЗАЦИЯ "КРУЖКИ В РЯД" (ПО ТВОЕМУ РИСУНКУ) ---
    c_left, c_mid, c_right = st.columns([2, 5, 2])

    with c_left:
        st.markdown(f"<h3 style='margin:0;'>{team_a}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#00ff88; font-size:20px; font-weight:bold;'>{p_a1}<br>{p_a2}</p>", unsafe_allow_html=True)

    with c_right:
        st.markdown(f"<div style='text-align:right;'><h3 style='margin:0;'>{team_b}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#ff4d4d; font-size:20px; font-weight:bold; text-align:right;'>{p_b1}<br>{p_b2}</p></div>", unsafe_allow_html=True)

    with c_mid:
        def draw_circles_row(h_range):
            html = '<div style="display:flex; justify-content:center; gap:8px; margin-bottom:10px;">'
            for h in h_range:
                res = m_df[m_df["hole"] == h]["result"].values
                color, text_c = "#444", "#888" # Не сыграно
                if len(res) > 0:
                    if res[0] == 1: color, text_c = "#00ff88", "black"
                    elif res[0] == 2: color, text_c = "#ff4d4d", "white"
                    else: color, text_c = "#888", "white" # Ничья
                html += f'<div style="width:32px; height:32px; background:{color}; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:bold; color:{text_c}; border:1px solid white;">{h}</div>'
            return html + '</div>'

        st.markdown(draw_circles_row(range(1, 10)), unsafe_allow_html=True)
        st.markdown(draw_circles_row(range(10, 19)), unsafe_allow_html=True)

        # Счет матча
        total_a = len(m_df[m_df["result"] == 1])
        total_b = len(m_df[m_df["result"] == 2])
        diff = total_a - total_b
        
        if diff > 0: status_text = f"{diff} UP"
        elif diff < 0: status_text = f"{abs(diff)} DN"
        else: status_text = "ALL SQUARE"
        
        st.markdown(f"<h1 style='text-align:center; font-size:60px; margin:0;'>{total_a} : {total_b}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#4da6ff; font-weight:bold; font-size:20px;'>{status_text}</p>", unsafe_allow_html=True)
        
        if len(m_df) == 18:
            st.markdown("<p style='text-align:center; color:#FFD700; font-weight:bold;'>МАТЧ ЗАВЕРШЕН</p>", unsafe_allow_html=True)
else:
    st.info("Ожидание данных от маркера...")

    
# ======================
# ТАБЛИЦА ВСЕХ МАТЧЕЙ (ДЕТАЛЬНО)
# ======================
st.markdown("---")
with st.expander("📊 Посмотреть все записи (Лог матча)"):
    if not df.empty:
        # Показываем таблицу, заменяя цифры 1, 0, 2 на понятные слова
        display_log = df.copy()
        display_log['Результат'] = display_log['result'].map({1: "Победа А", 0: "Ничья", 2: "Победа Б"})
        st.dataframe(display_log[["match_id", "hole", "Результат"]], use_container_width=True)
    else:
        st.write("Записей пока нет")

# ======================
# ОБЩАЯ СТРАНИЦА (Как на листке ТЗ)
# ======================
st.markdown("---")
st.header("📋 ОБЩАЯ СТРАНИЦА ТУРНИРА")

# Для "Общей страницы" нам нужно считать итоги матчей
if not df.empty:
    # 1. Создаем список уникальных команд
    all_teams = list(set(df['match_id'].str.split('_vs_').str[0].tolist() + 
                         df['match_id'].str.split('_vs_').str[1].tolist()))
    
    leaderboard_data = []
    
    for t_name in all_teams:
        # Считаем, сколько всего лунок выиграла эта команда во всех матчах
        # (Когда она была командой А и результат 1, или когда была Б и результат 2)
        wins_as_a = len(df[(df['match_id'].str.startswith(t_name)) & (df['result'] == 1)])
        wins_as_b = len(df[(df['match_id'].str.endswith(t_name)) & (df['result'] == 2)])
        total_wins = wins_as_a + wins_as_b
        
        leaderboard_data.append({
            "КОМАНДА": t_name,
            "1 ДЕНЬ": total_wins, # Здесь можно добавить логику разделения по дням
            "2 ДЕНЬ": 0,
            "3 ДЕНЬ": 0,
            "ИТОГО": total_wins
        })
    
    # Создаем таблицу и сортируем по убыванию (как на рисунке)
    final_ldf = pd.DataFrame(leaderboard_data).sort_values("ИТОГО", ascending=False)
    
    # Выводим строгую таблицу (st.table ближе к виду на листке)
    st.table(final_ldf)
else:
    st.info("Здесь будет общая таблица турнира, когда появятся результаты первых лунок.")

# ======================
# ДЕМО-РЕЖИМ (Новая версия под кнопки)
# ======================
import random
import time

st.sidebar.markdown("---")
if st.sidebar.button("🚀 Запустить симуляцию матча"):
    demo_data = []
    
    # Берем команды из тех, что вписаны в Sidebar прямо сейчас
    t_a = team_a_label if 'team_a_label' in locals() else "Команда А"
    t_b = team_b_label if 'team_b_label' in locals() else "Команда Б"
    m_id = f"{t_a}_vs_{t_b}"
    
    # Генерируем результаты для всех 18 лунок
    for h in range(1, 19):
        # Случайный результат: 1 (Выигрыш А), 0 (Ничья), 2 (Выигрыш Б)
        res = random.choice([1, 0, 2])
        
        demo_data.append({
            "match_id": m_id,
            "hole": h,
            "result": res,
            "pair_a": "Демо Игрок А",
            "pair_b": "Демо Игрок Б"
        })
    
    # Сохраняем в файл с правильными колонками
    new_df = pd.DataFrame(demo_data)
    new_df.to_csv(FILE, index=False)
    
    st.toast('Симуляция матча завершена! ⛳', icon='🔥')
    time.sleep(1)
    st.rerun()
