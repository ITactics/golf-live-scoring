import streamlit as st
import pandas as pd
import os
import time
import base64
import random

# ======================
# 1. СИСТЕМНЫЕ НАСТРОЙКИ
# ======================
st.set_page_config(page_title="Golf TV Live", layout="wide")

FILE = "tournament_results.csv"
TEAMS_FILE = "teams_list.txt"

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
    return "https://flaticon.com"

def load_teams():
    if os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Gorki", "Strawberry", "МГГК", "Целеево", "Forest"]

def save_teams(teams):
    with open(TEAMS_FILE, "w", encoding="utf-8") as f:
        for team in teams: f.write(f"{team}\n")

if 'team_list' not in st.session_state:
    st.session_state.team_list = load_teams()

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["match_id", "hole", "result", "pair_a", "pair_b"])
    df.to_csv(FILE, index=False)

# ======================
# 2. СТИЛИ (ФИКСАЦИЯ ЦВЕТОВ)
# ======================
st.markdown("""
<style>
.stApp { background: url("https://unsplash.com"); background-size: cover; }
.block-container { background: rgba(0, 0, 0, 0.75); padding: 30px; border-radius: 20px; }
h1, h2, h3, p, label { color: white !important; }

/* Принудительный черный текст внутри белых карточек */
.match-card-container * {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# ======================
# 3. SIDEBAR (МЕНЕДЖЕР)
# ======================
st.sidebar.header("🎨 Настройки турнира")

# Логотипы команд
with st.sidebar.expander("🖼 Логотипы команд"):
    target_t = st.selectbox("Команда:", st.session_state.team_list, key="sel_logo")
    t_logo = st.file_uploader(f"Загрузить лого для {target_t}", type=["png", "jpg"], key="up_logo")
    if t_logo:
        with open(f"logo_{target_t}.png", "wb") as f:
            f.write(t_logo.getbuffer())
        st.success("Сохранено!")
        st.rerun()

# Управление списком команд
st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Управление списком команд"):
    new_team_name = st.text_input("Название новой команды:", key="new_team_input")
    if st.button("➕ Добавить в базу", key="add_team_btn"):
        if new_team_name and new_team_name not in st.session_state.team_list:
            st.session_state.team_list.append(new_team_name)
            save_teams(st.session_state.team_list)
            st.rerun()
    
    if len(st.session_state.team_list) > 0:
        team_to_del = st.selectbox("Удалить из базы:", st.session_state.team_list, key="del_team_sel")
        if st.button("🗑 Удалить команду", key="del_team_btn"):
            st.session_state.team_list.remove(team_to_del)
            save_teams(st.session_state.team_list)
            st.rerun()

# Скачивание результатов
st.sidebar.markdown("---")
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 Скачать итоги (CSV)", data=csv, file_name='golf_results.csv', mime='text/csv')

# Текущий матч (С защитой от дублей)
st.sidebar.markdown("---")
st.sidebar.subheader("👥 Состав текущего матча")
col_sa, col_sb = st.sidebar.columns(2)
with col_sa:
    team_a = st.selectbox("Команда А", st.session_state.team_list, key="ta_sel")
    p_a = st.text_input("Пара А (ФИО)", "Иванов/Петров", key="pa_input")
with col_sb:
    # Защита: нельзя выбрать ту же команду
    available_b = [t for t in st.session_state.team_list if t != team_a]
    team_b = st.selectbox("Команда Б", available_b, key="tb_sel")
    if len(st.session_state.team_list) < 2:
    st.warning("Добавьте минимум 2 команды")
    st.stop()
    if not available_b:
        st.warning("Нельзя выбрать одинаковые команды")
        st.stop()
        p_b = st.text_input("Пара Б (ФИО)", "Сидоров/Борисов", key="pb_input")

format_type = st.sidebar.selectbox("Формат", ["9-9-18", "6-6-6-18"], key="fmt_sel")

if st.sidebar.button("🗑 Сбросить ВСЕ данные", key="reset_all_btn"):
    if os.path.exists(FILE): os.remove(FILE)
    st.rerun()

# ======================
# 4. ВВОД МАРКЕРА
# ======================
st.header("📱 Ввод результатов (Маркер)")
hole = st.selectbox("Выберите лунку:", list(range(1, 19)), key="hole_sel")
teams_sorted = sorted([team_a, team_b])
match_id = f"{teams_sorted[0]}_vs_{teams_sorted[1]}"

def save_result(val):
    global df
    new_data = pd.DataFrame([{"match_id": match_id, "hole": hole, "result": val, "pair_a": p_a, "pair_b": p_b}])
    mask = (df.match_id == match_id) & (df.hole == hole)
    df = pd.concat([df[~mask], new_data]).sort_values("hole")
    df.to_csv(FILE, index=False)
    st.toast(f"Лунка {hole} записана!")
    time.sleep(0.4)
    st.rerun()

c1, c2, c3 = st.columns(3)
with c1: 
    if st.button(f"🏆 {team_a}", use_container_width=True, key="win_a_btn"): save_result(1)
with c2: 
    if st.button("🤝 НИЧЬЯ", use_container_width=True, key="draw_btn"): save_result(0)
with c3: 
    if st.button(f"🏆 {team_b}", use_container_width=True, key="win_b_btn"): save_result(2)

# ======================
# 5. СТРАНИЦА ПАРЫ (ВИЗУАЛ)
# ======================
st.markdown("---")
m_df = df[df.match_id == match_id]
if not m_df.empty:
    l_col, m_col, r_col = st.columns([2, 5, 2])
    with l_col:
        st.image(get_base64_image(f"logo_{team_a}.png"), width=80)
        st.subheader(team_a); st.write(p_a)
    with r_col:
        st.markdown(f"<div style='text-align:right;'><img src='{get_base64_image(f'logo_{team_b}.png')}' width='80'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:right;'><h3>{team_b}</h3><p>{p_b}</p></div>", unsafe_allow_html=True)
    with m_col:
        def draw_row(h_range):
            html = '<div style="display:flex; justify-content:center; gap:5px; margin-bottom:10px;">'
            for h in h_range:
                res = m_df[m_df.hole == h].result.values
                bg = "#444"
                if len(res) > 0: bg = "#00ff88" if res[0] == 1 else "#ff4d4d" if res[0] == 2 else "#888"
                html += f'<div style="width:28px; height:28px; background:{bg}; border-radius:50%; border:1px solid white; display:flex; align-items:center; justify-content:center; font-size:10px;">{h}</div>'
            return html + '</div>'
        st.markdown(draw_row(range(1, 10)), unsafe_allow_html=True)
        st.markdown(draw_row(range(10, 19)), unsafe_allow_html=True)
        a_w, b_w = len(m_df[m_df.result == 1]), len(m_df[m_df.result == 2])
        st.markdown(f"<h1 style='text-align:center; font-size:60px;'>{a_w} : {b_w}</h1>", unsafe_allow_html=True)

# ======================
# ОБЩАЯ СТАТИСТИКА ТУРНИРА
# ======================
st.markdown("---")
st.title("📋 ПОЛОЖЕНИЕ КОМАНД")

if not df.empty:
# 1. Таблица рейтинга (НОРМАЛЬНАЯ ЛОГИКА)
stats = {team: {"Очки": 0, "Победы": 0, "Ничьи": 0, "Поражения": 0} 
         for team in st.session_state.team_list}

matches = df.match_id.unique()

for m in matches:
    m_data = df[df.match_id == m]
    
    # ❗ считаем только завершенные матчи
    if len(m_data) < 18:
        continue

    team_a_m, team_b_m = m.split("_vs_")
    
    a_wins = len(m_data[m_data.result == 1])
    b_wins = len(m_data[m_data.result == 2])

    if a_wins > b_wins:
        stats[team_a_m]["Очки"] += 3
        stats[team_a_m]["Победы"] += 1
        stats[team_b_m]["Поражения"] += 1

    elif b_wins > a_wins:
        stats[team_b_m]["Очки"] += 3
        stats[team_b_m]["Победы"] += 1
        stats[team_a_m]["Поражения"] += 1

    else:
        stats[team_a_m]["Очки"] += 1
        stats[team_b_m]["Очки"] += 1
        stats[team_a_m]["Ничьи"] += 1
        stats[team_b_m]["Ничьи"] += 1

ldf = pd.DataFrame([
    {"Команда": team, **vals} for team, vals in stats.items()
]).sort_values(["Очки", "Победы"], ascending=False)

    # 2. Карточки матчей
    unique_matches = df.match_id.unique()
    for i in range(0, len(unique_matches), 2):
        row = st.columns(2)
        for j in range(2):
            if i + j < len(unique_matches):
                curr_m = unique_matches[i+j]
                m_data = df[df.match_id == curr_m]
                t_a_n, t_b_n = curr_m.split("_vs_")
                s_a, s_b = len(m_data[m_data.result == 1]), len(m_data[m_data.result == 2])
                
                p_a_display = m_data.iloc[-1]['pair_a'] if not m_data.empty else "Пара А"
                p_b_display = m_data.iloc[-1]['pair_b'] if not m_data.empty else "Пара Б"

                logo_a_v4 = get_base64_image(f"logo_{t_a_n}.png")
                logo_b_v4 = get_base64_image(f"logo_{t_b_n}.png")

                with row[j]:
                    st.markdown(f"""
                    <div class="match-card-container" style="background:white; padding:15px; border-radius:10px; border-left:10px solid #cc0000; display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.2);">
                        <div style="text-align:center; width:33%;">
                            <img src="{logo_a_v4}" width="40"><br>
                            <b style="font-size: 14px;">{t_a_n}</b><br>
                            <span style="font-size: 11px; opacity: 0.8;">{p_a_display}</span>
                        </div>
                        <div style="text-align:center; width:34%;">
                            <h1 style="color:#cc0000 !important; margin:0; font-size: 38px; font-weight: bold;">{s_a}:{s_b}</h1>
                            <div style="font-size: 10px; opacity: 0.6;">LIVE</div>
                        </div>
                        <div style="text-align:center; width:33%;">
                            <img src="{logo_b_v4}" width="40"><br>
                            <b style="font-size: 14px;">{t_b_n}</b><br>
                            <span style="font-size: 11px; opacity: 0.8;">{p_b_display}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Симуляция
if st.sidebar.button("🚀 Демо-турнир", key="demo_tournament_btn"): # Добавлен уникальный ключ
    demo = []
    for _ in range(4):
        t_a_d, t_b_d = random.sample(st.session_state.team_list, 2)
        for h in range(1, 11):
            demo.append({"match_id": f"{t_a_d}_vs_{t_b_d}", "hole": h, "result": random.choice([1,0,2]), "pair_a": "Игрок А", "pair_b": "Игрок Б"})
    pd.DataFrame(demo).to_csv(FILE, index=False)
    st.rerun()
