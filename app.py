import streamlit as st
import pandas as pd
import os
import time
import base64
import random
import json

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
# 3. SIDEBAR (С ОБЩИМ РАСПИСАНИЕМ ДЛЯ ВСЕХ УСТРОЙСТВ)
# ======================
st.sidebar.header("🎨 Настройки турнира")

# --- ФУНКЦИИ ДЛЯ ОБЩЕГО РАСПИСАНИЯ ---
SCH_FILE = "schedule.json"

def load_schedule():
    if os.path.exists(SCH_FILE):
        with open(SCH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_schedule(sch_list):
    with open(SCH_FILE, "w", encoding="utf-8") as f:
        json.dump(sch_list, f, ensure_ascii=False)

# Загружаем расписание при старте
if 'schedule' not in st.session_state:
    st.session_state.schedule = load_schedule()

# 1. Логотипы команд
with st.sidebar.expander("🖼 Логотипы команд"):
    target_t = st.selectbox("Команда:", st.session_state.team_list, key="sel_logo")
    t_logo = st.file_uploader(f"Загрузить лого для {target_t}", type=["png", "jpg"], key="up_logo")
    if t_logo:
        with open(f"logo_{target_t}.png", "wb") as f:
            f.write(t_logo.getbuffer())
        st.success("Сохранено!")
        st.rerun()

# 2. Управление списком клубов
with st.sidebar.expander("⚙️ Настройка списка клубов"):
    new_team_name = st.text_input("Название нового клуба:", key="new_team_input")
    if st.button("➕ Добавить клуб", key="add_team_btn"):
        if new_team_name and new_team_name not in st.session_state.team_list:
            st.session_state.team_list.append(new_team_name)
            save_teams(st.session_state.team_list)
            st.rerun()
    
    if len(st.session_state.team_list) > 0:
        team_to_del = st.selectbox("Удалить клуб:", st.session_state.team_list, key="del_team_sel")
        if st.button("🗑 Удалить", key="del_team_btn"):
            st.session_state.team_list.remove(team_to_del)
            save_teams(st.session_state.team_list)
            st.rerun()

# 3. МЕНЕДЖЕР РАСПИСАНИЯ
st.sidebar.markdown("---")
with st.sidebar.expander("📅 Создать расписание (Пары)"):
    st.write("Добавьте пары на сегодня:")
    m_ta = st.selectbox("Клуб А", st.session_state.team_list, key="m_ta")
    m_pa = st.text_input("Пара А (Фамилии)", "Иванов/Петров", key="m_pa")
    m_tb = st.selectbox("Клуб Б", [t for t in st.session_state.team_list if t != m_ta], key="m_tb")
    m_pb = st.text_input("Пара Б (Фамилии)", "Сидоров/Борисов", key="m_pb")
    
    if st.button("➕ Добавить игру в список"):
        match_info = {
            "id": f"{m_ta}_vs_{m_tb}",
            "label": f"{m_ta} ({m_pa}) vs {m_tb} ({m_pb})",
            "ta": m_ta, "pa": m_pa, "tb": m_tb, "pb": m_pb
        }
        # Проверка на дубликат и сохранение в файл
        if match_info["id"] not in [m["id"] for m in st.session_state.schedule]:
            st.session_state.schedule.append(match_info)
            save_schedule(st.session_state.schedule) # Теперь сохраняем на диск!
            st.success("Матч добавлен!")
            st.rerun()

# 4. ВЫБОР АКТИВНОГО МАТЧА
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Активная игра")

# Всегда подгружаем свежее расписание из файла
st.session_state.schedule = load_schedule()

if st.session_state.schedule:
    options = [m["label"] for m in st.session_state.schedule]
    selected_label = st.sidebar.selectbox("Какую игру судим?", options)
    
    active_m = next(m for m in st.session_state.schedule if m["label"] == selected_label)
    team_a, p_a = active_m["ta"], active_m["pa"]
    team_b, p_b = active_m["tb"], active_m["pb"]
else:
    st.sidebar.warning("Сначала добавьте игры в расписание выше!")
    team_a, p_a, team_b, p_b = "Клуб А", "Пара А", "Клуб Б", "Пара Б"

format_type = st.sidebar.selectbox("Формат зачета", ["9-9-18", "6-6-6-18"], key="fmt_sel")

# Скачивание и сброс
st.sidebar.markdown("---")
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 Скачать CSV", data=csv, file_name='golf_results.csv', mime='text/csv')

if st.sidebar.button("🗑 Сбросить ВСЕ данные", key="reset_all_btn"):
    if os.path.exists(FILE): os.remove(FILE)
    if os.path.exists(SCH_FILE): os.remove(SCH_FILE) # Удаляем и файл расписания
    if 'schedule' in st.session_state: del st.session_state.schedule
    st.rerun()

# ======================
# ВВОД МАРКЕРА
# ======================
st.header("📱 Ввод результатов (Маркер)")

if 'hole_num' not in st.session_state:
    st.session_state.hole_num = 1

# Кнопки переключения лунок без клавиатуры
ch1, ch2, ch3 = st.columns([1, 2, 1])
with ch1:
    if st.button("➖", use_container_width=True):
        st.session_state.hole_num = max(1, st.session_state.hole_num - 1)
with ch2:
    st.markdown(f"<h2 style='text-align:center; margin:0;'>Лунка {st.session_state.hole_num}</h2>", unsafe_allow_html=True)
with ch3:
    if st.button("➕", use_container_width=True):
        st.session_state.hole_num = min(18, st.session_state.hole_num + 1)

hole = st.session_state.hole_num
match_id = f"{team_a}_vs_{team_b}"

def save_result(val):
    global df
    new_data = pd.DataFrame([{"match_id": match_id, "hole": hole, "result": val, "pair_a": p_a, "pair_b": p_b}])
    mask = (df.match_id == match_id) & (df.hole == hole)
    df = pd.concat([df[~mask], new_data]).sort_values("hole")
    df.to_csv(FILE, index=False)
    st.toast(f"Лунка {hole} записана!")
    # Авто-переход на следующую лунку
    if st.session_state.hole_num < 18:
        st.session_state.hole_num += 1
    time.sleep(0.3)
    st.rerun()

# Кнопки ввода (Цвета теперь Красный и Синий)
c1, c2, c3 = st.columns(3)
with c1: 
    if st.button(f"🔵 {team_a}", use_container_width=True, key="win_a_btn"): save_result(1)
with c2: 
    if st.button("🤝 НИЧЬЯ", use_container_width=True, key="draw_btn"): save_result(0)
with c3: 
    if st.button(f"🔴 {team_b}", use_container_width=True, key="win_b_btn"): save_result(2)

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
# ОБЩАЯ СТАТИСТИКА (LEADERBOARD + CARDS)
# ======================
st.markdown("---")
st.title("📋 ПОЛОЖЕНИЕ КОМАНД")

if not df.empty:
    # 1. ТАБЛИЦА РЕЙТИНГА (Подсчет по Match Play: 9-9-18)
        # 1. ТАБЛИЦА РЕЙТИНГА (ИСПРАВЛЕННЫЙ ПОДСЧЕТ)
    stats = []
    for t in st.session_state.team_list:
        total_points = 0.0
        # Ищем все матчи команды
        m_ids = df[df.match_id.str.contains(t)].match_id.unique()
        
        for m_id in m_ids:
            m_data = df[df.match_id == m_id]
            t_a, t_b = m_id.split("_vs_")
            
            # Интервалы (9-9-18 или 6-6-6-18)
            intervals = [range(1, 10), range(10, 19), range(1, 19)] if format_type == "9-9-18" else [range(1, 7), range(7, 13), range(13, 19), range(1, 19)]
            
            for h_range in intervals:
                subset = m_data[m_data.hole.isin(h_range)]
                if subset.empty: continue # Пропускаем, если лунки еще не игрались
                
                a_w = len(subset[subset.result == 1])
                b_w = len(subset[subset.result == 2])
                
                # Очки: 1 за победу, 0.5 за ничью
                if a_w == b_w:
                    total_points += 0.5
                elif (t == t_a and a_w > b_w) or (t == t_b and b_w > a_w):
                    total_points += 1.0
        
        stats.append({"Команда": t, "Очки": total_points})
    
    ldf = pd.DataFrame(stats).sort_values("Очки", ascending=False)
    ldf = ldf.reset_index(drop=True) # Очищаем старые индексы
    ldf.index += 1                  # Делаем так, чтобы места начинались с 1

    
    # ЭТА СТРОЧКА УБИРАЕТ ЛИШНИЕ НУЛИ (2.5000 -> 2.5)
    ldf["Очки"] = ldf["Очки"].apply(lambda x: f"{x:g}") 
    
    # ВЫВОД ТАБЛИЦЫ В ДВЕ КОЛОНКИ
    c_tab1, c_tab2 = st.columns(2)
    half = len(ldf) // 2 + len(ldf) % 2
    with c_tab1: st.table(ldf.iloc[:half])
    with c_tab2: st.table(ldf.iloc[half:])

    st.markdown("---")

    # 2. КАРТОЧКИ МАТЧЕЙ (С добавлением статуса UP/DN)
    unique_matches = df.match_id.unique()
    for i in range(0, len(unique_matches), 2):
        row = st.columns(2)
        for j in range(2):
            if i + j < len(unique_matches):
                curr_m = unique_matches[i+j]
                m_data = df[df.match_id == curr_m]
                t_a_n, t_b_n = curr_m.split("_vs_")
                
                s_a = len(m_data[m_data.result == 1])
                s_b = len(m_data[m_data.result == 2])
                
                # Расчет UP/DN для центра карточки
                diff = s_a - s_b
                if diff > 0: status_info = f"{diff} UP {t_a_n}"
                elif diff < 0: status_info = f"{abs(diff)} UP {t_b_n}"
                else: status_info = "ALL SQUARE"

                p_a_display = m_data.iloc[-1]['pair_a'] if not m_data.empty else "Пара А"
                p_b_display = m_data.iloc[-1]['pair_b'] if not m_data.empty else "Пара Б"

                with row[j]:
                    st.markdown(f"""
                    <div class="match-card-container" style="background:white; padding:15px; border-radius:10px; border-left:10px solid #cc0000; display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.2);">
                        <div style="text-align:center; width:33%;">
                            <img src="{get_base64_image(f'logo_{t_a_n}.png')}" width="40"><br>
                            <b style="font-size: 14px;">{t_a_n}</b><br>
                            <span style="font-size: 10px; opacity: 0.8;">{p_a_display}</span>
                        </div>
                        <div style="text-align:center; width:34%;">
                            <h1 style="color:#cc0000 !important; margin:0; font-size:36px;">{s_a}:{s_b}</h1>
                            <div style="font-size:12px; font-weight:bold; color:black;">{status_info}</div>
                        </div>
                        <div style="text-align:center; width:33%;">
                            <img src="{get_base64_image(f'logo_{t_b_n}.png')}" width="40"><br>
                            <b style="font-size: 14px;">{t_b_n}</b><br>
                            <span style="font-size: 10px; opacity: 0.8;">{p_b_display}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Симуляция (18 лунок для полноты картины)
if st.sidebar.button("🚀 Демо-турнир", key="demo_tournament_btn"):
    demo = []
    for _ in range(4):
        t_a_d, t_b_d = random.sample(st.session_state.team_list, 2)
        for h in range(1, 19): # Теперь 18 лунок
            demo.append({"match_id": f"{t_a_d}_vs_{t_b_d}", "hole": h, "result": random.choice([1,0,2]), "pair_a": "Игрок А1/А2", "pair_b": "Игрок Б1/Б2"})
    pd.DataFrame(demo).to_csv(FILE, index=False)
    st.rerun()
