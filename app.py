import streamlit as st
import pandas as pd
import os
import time
import base64
import random
import json
from streamlit_autorefresh import st_autorefresh

# ======================
# 0. АВТООБНОВЛЕНИЕ (раз в 30 секунд)
# ======================
st_autorefresh(interval=30 * 1000, key="datarefresh")

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

/* Убираем принудительный черный цвет, чтобы цвета из карточек (красный/синий) работали */
.match-card-container b, .match-card-container span, .match-card-container div {
    /* Здесь больше нет принудительного черного цвета для всего подряд */
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

# ======================
# СИСТЕМА СПАСЕНИЯ ДАННЫХ
# ======================
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Работа с данными")

# 1. Скачивание (Бэкап)
if not df.empty:
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(
        label="📥 Скачать CSV (Бэкап)",
        data=csv_data,
        file_name='golf_results.csv',
        mime='text/csv',
        help="Скачайте файл в конце дня, чтобы данные не пропали!"
    )

# 2. Загрузка (Восстановление)
up_file = st.sidebar.file_uploader("🔄 Восстановить из файла", type="csv", help="Загрузите скачанный ранее файл, если данные обнулились")
if up_file:
    try:
        restored_df = pd.read_csv(up_file)
        restored_df.to_csv(FILE, index=False)
        st.sidebar.success("Данные успешно возвращены!")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.sidebar.error("Ошибка в файле!")

# 3. Безопасный сброс
st.sidebar.markdown("---")
if st.sidebar.button("🗑 Сбросить ВСЕ данные", key="reset_all_btn"):
    if os.path.exists(FILE): os.remove(FILE)
    if os.path.exists(SCH_FILE): os.remove(SCH_FILE)
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

# Кнопки ввода (Красная слева, Синяя справа + стили для яркости)
st.markdown("""
<style>
/* Красная кнопка (Команда А) */
div[data-testid="stHorizontalBlock"] button[key="win_a_btn"] {
    background-color: #ff4d4d !important;
    color: white !important;
    border: none;
}
/* Синяя кнопка (Команда Б) */
div[data-testid="stHorizontalBlock"] button[key="win_b_btn"] {
    background-color: #007bff !important;
    color: white !important;
    border: none;
}
/* Серая кнопка (Ничья) */
div[data-testid="stHorizontalBlock"] button[key="draw_btn"] {
    background-color: #555555 !important;
    color: white !important;
    border: none;
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: 
    if st.button(f"🔴 {team_a}", use_container_width=True, key="win_a_btn"): 
        save_result(1)
with c2: 
    if st.button("🤝 НИЧЬЯ", use_container_width=True, key="draw_btn"): 
        save_result(0)
with c3: 
    if st.button(f"🔵 {team_b}", use_container_width=True, key="win_b_btn"): 
        save_result(2)

# ======================
# 5. СТРАНИЦА ПАРЫ (ВИЗУАЛ)
# ======================
st.markdown("---")
m_df = df[df.match_id == match_id]
if not m_df.empty:
    l_col, m_col, r_col = st.columns([2, 5, 2])
    with l_col:
        st.image(get_base64_image(f"logo_{team_a}.png"), width=80)
        # Название левой команды КРАСНЫМ
        st.markdown(f"<h3 style='color:#ff4d4d !important;'>{team_a}</h3><p>{p_a}</p>", unsafe_allow_html=True)
    with r_col:
        st.markdown(f"<div style='text-align:right;'><img src='{get_base64_image(f'logo_{team_b}.png')}' width='80'></div>", unsafe_allow_html=True)
        # Название правой команды СИНИМ
        st.markdown(f"<div style='text-align:right;'><h3 style='color:#007bff !important;'>{team_b}</h3><p>{p_b}</p></div>", unsafe_allow_html=True)
    with m_col:
        def draw_row(h_range):
            html = '<div style="display:flex; justify-content:center; gap:5px; margin-bottom:10px;">'
            for h in h_range:
                res = m_df[m_df.hole == h].result.values
                bg = "#444"
                if len(res) > 0: 
                    # ИСПРАВЛЕНО: 1 — Красный (Команда А), 2 — Синий (Команда Б)
                    bg = "#ff4d4d" if res[0] == 1 else "#007bff" if res[0] == 2 else "#888"
                html += f'<div style="width:28px; height:28px; background:{bg}; border-radius:50%; border:1px solid white; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:bold; color:white;">{h}</div>'
            return html + '</div>'
            
        st.markdown(draw_row(range(1, 10)), unsafe_allow_html=True)
        st.markdown(draw_row(range(10, 19)), unsafe_allow_html=True)
        
        # --- НОВАЯ ЛОГИКА: СЧИТАЕМ ТУРНИРНЫЕ ОЧКИ (MATCH POINTS) ---
        main_pts_a, main_pts_b = 0.0, 0.0
        intervals = [range(1, 10), range(10, 19), range(1, 19)] if format_type == "9-9-18" else [range(1, 7), range(7, 13), range(13, 19), range(1, 19)]
        
        for r in intervals:
            subset = m_df[m_df.hole.isin(r)]
            if not subset.empty:
                aw, bw = len(subset[subset.result==1]), len(subset[subset.result==2])
                if aw == bw:
                    main_pts_a += 0.5; main_pts_b += 0.5
                elif aw > bw:
                    main_pts_a += 1.0
                else:
                    main_pts_b += 1.0

        # ВЫВОДИМ ОЧКИ МАТЧА (Красный слева, Синий справа)
        st.markdown(f"""
            <div style='text-align:center;'>
                <h1 style='font-size:80px; margin:0; line-height:1; font-weight:bold;'>
                    <span style='color:#ff4d4d;'>{main_pts_a:g}</span> 
                    <span style='color:white;'>:</span> 
                    <span style='color:#007bff;'>{main_pts_b:g}</span>
                </h1>
                <p style='color:#aaa; font-weight:bold; letter-spacing:2px; margin-top:5px; font-size:14px; text-transform:uppercase;'>Match Points</p>
            </div>
        """, unsafe_allow_html=True)

# ======================
# ОБЩАЯ СВОДНАЯ ТАБЛИЦА
# ======================
st.title("ПОЛОЖЕНИЕ КОМАНД")

# Фильтр по командам
all_t_options = ["Все команды"] + st.session_state.team_list
filter_t = st.selectbox("🎯 Выберите команду, чтобы посмотреть матчи только с её участием:", all_t_options)

if not df.empty:
    summary = []
    for t in st.session_state.team_list:
        t_pts = 0.0
        t_ud = 0
        details = []
        # Находим все матчи конкретной команды
        m_ids = df[df.match_id.str.contains(t)].match_id.unique()
        
        for m_id in m_ids:
            m_data = df[df.match_id == m_id]
            t_a, t_b = m_id.split("_vs_")
            
            # Считаем Match Points (1.0 или 0.5 за отрезок)
            ints = [range(1,10), range(10,19), range(1,19)] if format_type == "9-9-18" else [range(1,7), range(7,13), range(13,19), range(1,19)]
            for r in ints:
                sub = m_data[m_data.hole.isin(r)]
                if not sub.empty:
                    aw, bw = len(sub[sub.result==1]), len(sub[sub.result==2])
                    p = 0.0
                    if aw == bw: p = 0.5
                    elif (t == t_a and aw > bw) or (t == t_b and bw > aw): p = 1.0
                    
                    if p > 0:
                        t_pts += p
                        details.append(f"{p:g}")
            
            # Считаем U/D (Суммарная разница выигранных лунок)
            aw_total = len(m_data[m_data.result == 1])
            bw_total = len(m_data[m_data.result == 2])
            if t == t_a: t_ud += (aw_total - bw_total)
            else: t_ud += (bw_total - aw_total)

        # Формируем строку итога с детализацией
        det_str = f"({'+'.join(details)})" if details else ""
        summary.append({
            "КОМАНДА": t,
            "МАТЧИ": f"Завершено {len(m_ids)} из 3",
            "POINTS": t_pts,  # 👈 ДОБАВИЛИ (важно)
            "ИТОГ": f"{t_pts:g} {det_str}",
            "U/D": t_ud
        })

    # Сортировка: Сначала по очкам (ИТОГ), затем по разнице лунок (U/D)
    ldf = pd.DataFrame(summary).sort_values(
        by=["POINTS", "U/D"],
        ascending=False
    )
    ldf.insert(0, 'МЕСТО', range(1, len(ldf) + 1))
    ldf = ldf.drop(columns=["POINTS"])
    
    # Вывод в две колонки (как на скриншоте)
    # c1, c2 = st.columns(2)
    # mid = (len(ldf) + 1) // 2
    
    
    # with c1: st.table(ldf.iloc[:mid].reset_index(drop=True))
    # with c2: st.table(ldf.iloc[mid:].reset_index(drop=True))
    st.dataframe(ldf, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. КАРТОЧКИ МАТЧЕЙ (ДИЗАЙН С ОГРОМНЫМ СЧЕТОМ)
    unique_matches = df.match_id.unique()
    if filter_t != "Все команды":
        unique_matches = [m for m in unique_matches if filter_t in m]
    for i in range(0, len(unique_matches), 2):
        row = st.columns(2)
        for j in range(2):
            if i + j < len(unique_matches):
                curr_m = unique_matches[i+j]
                m_data = df[df.match_id == curr_m]
                t_a_n, t_b_n = curr_m.split("_vs_")
                
                # Считаем очки матча (Match Points)
                pts_a, pts_b = 0.0, 0.0
                intervals = [range(1, 10), range(10, 19), range(1, 19)] if format_type == "9-9-18" else [range(1, 7), range(7, 13), range(13, 19), range(1, 19)]
                
                def get_status_html(h_range):
                    sub = m_data[m_data.hole.isin(h_range)]
                    if sub.empty: return "<span></span>", "<span></span>"
                    a_w = len(sub[sub.result == 1])
                    b_w = len(sub[sub.result == 2])
                    diff = a_w - b_w
                    if diff > 0: 
                        return f"<b style='color:#ff4d4d; font-size:10px;'>{diff} UP</b>", f"<span style='color:#ccc; font-size:10px;'>{diff} DN</span>"
                    elif diff < 0:
                        return f"<span style='color:#ccc; font-size:10px;'>{abs(diff)} DN</span>", f"<b style='color:#007bff; font-size:10px;'>{abs(diff)} UP</b>"
                    else:
                        return "<b style='color:#777; font-size:10px;'>AS</b>", "<b style='color:#777; font-size:10px;'>AS</b>"
    
                def draw_status_row(h_range):
                    s_left, s_right = get_status_html(h_range)
                    row_html = f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;"><div style="width:40px; text-align:left;">{s_left}</div>'
                    row_html += '<div style="display:flex; gap:2px;">'
                    for h in h_range:
                        res = m_data[m_data.hole == h].result.values
                        bg = "#eee"
                        if len(res) > 0:
                            bg = "#ff4d4d" if res[0] == 1 else "#007bff" if res[0] == 2 else "#bbb"
                        row_html += f'<div style="width:8px; height:8px; background:{bg}; border-radius:50%;"></div>'
                    row_html += f'</div><div style="width:40px; text-align:right;">{s_right}</div></div>'
                    return row_html
    
                for r in intervals:
                    sub = m_data[m_data.hole.isin(r)]
                    if not sub.empty:
                        aw, bw = len(sub[sub.result==1]), len(sub[sub.result==2])
                        if aw == bw: pts_a += 0.5; pts_b += 0.5
                        elif aw > bw: pts_a += 1.0
                        else: pts_b += 1.0
    
                p_a_disp = m_data.iloc[-1]['pair_a'] if not m_data.empty else "Пара А"
                p_b_disp = m_data.iloc[-1]['pair_b'] if not m_data.empty else "Пара Б"
    
                with row[j]:
                    st.markdown(f"""
                    <div style="background:white; padding:15px; border-radius:15px; margin-bottom:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); border-left: 10px solid #ff4d4d; border-right: 10px solid #007bff; color: black !important;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <div style="width:25%; text-align:left;">
                                <img src="{get_base64_image(f'logo_{t_a_n}.png')}" width="35"><br>
                                <b style="color:#ff4d4d; font-size:12px;">{t_a_n}</b><br>
                                <span style="font-size:9px; color:#666;">{p_a_disp}</span>
                            </div>
                            <div style="width:50%; text-align:center;">
                                <div style="font-size:46px; font-weight:900; line-height:1; letter-spacing:-2px; margin-bottom:2px;">
                                    <span style="color:#ff4d4d;">{pts_a:g}</span>
                                    <span style="color:#000;">:</span>
                                    <span style="color:#007bff;">{pts_b:g}</span>
                                </div>
                                <div style="font-size:9px; font-weight:bold; color:#aaa; letter-spacing:1px; text-transform:uppercase;">Match Points</div>
                            </div>
                            <div style="width:25%; text-align:right;">
                                <img src="{get_base64_image(f'logo_{t_b_n}.png')}" width="35"><br>
                                <b style="color:#007bff; font-size:12px;">{t_b_n}</b><br>
                                <span style="font-size:9px; color:#666;">{p_b_disp}</span>
                            </div>
                        </div>
                        {draw_status_row(range(1, 10))}
                        {draw_status_row(range(10, 19))}
                        <div style="border-top:1px solid #eee; margin-top:8px; padding-top:8px;">
                            {draw_status_row(range(1, 19))}
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
