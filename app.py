import streamlit as st
import pandas as pd
import os
import base64
import random

# ======================
# НАСТРОЙКИ
# ======================
st.set_page_config(page_title="Golf TV Live", layout="wide")

FILE = "tournament_results.csv"
TEAMS_FILE = "teams_list.txt"

# ======================
# УТИЛИТЫ
# ======================
@st.cache_data
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
    return "https://via.placeholder.com/40"

def load_teams():
    if os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Gorki", "Strawberry", "МГГК", "Целеево", "Forest"]

def save_teams(teams):
    with open(TEAMS_FILE, "w", encoding="utf-8") as f:
        for team in teams:
            f.write(f"{team}\n")

# ======================
# INIT
# ======================
if 'team_list' not in st.session_state:
    st.session_state.team_list = load_teams()

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["match_id", "hole", "result", "pair_a", "pair_b"])
    df.to_csv(FILE, index=False)

# ======================
# СТИЛИ
# ======================
st.markdown("""
<style>
.stApp {
    background: url("https://images.unsplash.com/photo-1505842465776-3d90f6163104");
    background-size: cover;
}
.block-container {
    background: rgba(0, 0, 0, 0.75);
    padding: 30px;
    border-radius: 20px;
}
h1, h2, h3, p, label { color: white !important; }

.match-card-container * {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# ======================
# SIDEBAR
# ======================
st.sidebar.header("🎨 Настройки турнира")

# Логотипы
with st.sidebar.expander("🖼 Логотипы"):
    target_t = st.selectbox("Команда:", st.session_state.team_list)
    t_logo = st.file_uploader("Загрузить логотип", type=["png", "jpg"])
    if t_logo:
        with open(f"logo_{target_t}.png", "wb") as f:
            f.write(t_logo.getbuffer())
        st.rerun()

# Управление командами
with st.sidebar.expander("⚙️ Команды"):
    new_team = st.text_input("Новая команда")
    if st.button("➕ Добавить"):
        if new_team and new_team not in st.session_state.team_list:
            st.session_state.team_list.append(new_team)
            save_teams(st.session_state.team_list)
            st.rerun()

    if len(st.session_state.team_list) > 1:
        del_team = st.selectbox("Удалить:", st.session_state.team_list)
        if st.button("🗑 Удалить"):
            if del_team not in "".join(df.match_id.values):
                st.session_state.team_list.remove(del_team)
                save_teams(st.session_state.team_list)
                st.rerun()
            else:
                st.warning("Команда уже участвует в матчах")

# CSV
if not df.empty:
    st.sidebar.download_button(
        "📥 Скачать CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="golf_results.csv"
    )

# ======================
# МАТЧ
# ======================
st.sidebar.subheader("👥 Матч")

if len(st.session_state.team_list) < 2:
    st.warning("Добавьте минимум 2 команды")
    st.stop()

team_a = st.sidebar.selectbox("Команда А", st.session_state.team_list)
available_b = [t for t in st.session_state.team_list if t != team_a]

team_b = st.sidebar.selectbox("Команда Б", available_b)

p_a = st.sidebar.text_input("Пара А", "Игроки А")
p_b = st.sidebar.text_input("Пара Б", "Игроки Б")

# нормализация match_id
teams_sorted = sorted([team_a, team_b])
match_id = f"{teams_sorted[0]}_vs_{teams_sorted[1]}"

if st.sidebar.button("🗑 Сброс"):
    if os.path.exists(FILE):
        os.remove(FILE)
    st.rerun()

# ======================
# ВВОД
# ======================
st.header("📱 Ввод результатов")

hole = st.selectbox("Лунка", list(range(1, 19)))

def save_result(val):
    df_local = pd.read_csv(FILE)

    new_row = pd.DataFrame([{
        "match_id": match_id,
        "hole": hole,
        "result": val,
        "pair_a": p_a,
        "pair_b": p_b
    }])

    mask = (df_local.match_id == match_id) & (df_local.hole == hole)
    df_local = pd.concat([df_local[~mask], new_row])

    df_local.to_csv(FILE, index=False)
    st.rerun()

c1, c2, c3 = st.columns(3)
with c1:
    if st.button(f"🏆 {team_a}"): save_result(1)
with c2:
    if st.button("🤝"): save_result(0)
with c3:
    if st.button(f"🏆 {team_b}"): save_result(2)

# ======================
# ВИЗУАЛ МАТЧА
# ======================
df = pd.read_csv(FILE)
m_df = df[df.match_id == match_id]

if not m_df.empty:
    col1, col2, col3 = st.columns([2,5,2])

    with col1:
        st.image(get_base64_image(f"logo_{team_a}.png"), width=80)
        st.write(team_a, p_a)

    with col3:
        st.image(get_base64_image(f"logo_{team_b}.png"), width=80)
        st.write(team_b, p_b)

    with col2:
        def draw(range_h):
            html = ""
            for h in range_h:
                res = m_df[m_df.hole == h].result.values
                color = "#444"
                if len(res):
                    color = "#00ff88" if res[0]==1 else "#ff4d4d" if res[0]==2 else "#888"
                html += f'<span style="background:{color};padding:5px;margin:2px;border-radius:50%">{h}</span>'
            return html

        st.markdown(draw(range(1,10)), unsafe_allow_html=True)
        st.markdown(draw(range(10,19)), unsafe_allow_html=True)

        a_w = len(m_df[m_df.result==1])
        b_w = len(m_df[m_df.result==2])
        st.markdown(f"# {a_w} : {b_w}")

# ======================
# ТАБЛИЦА (FIXED)
# ======================
st.markdown("---")
st.title("📋 Таблица")

stats = {t: {"Очки":0,"Победы":0,"Ничьи":0,"Поражения":0} for t in st.session_state.team_list}

for m in df.match_id.unique():
    m_data = df[df.match_id == m]
    if len(m_data) < 18:
        continue

    a,b = m.split("_vs_")

    a_w = len(m_data[m_data.result==1])
    b_w = len(m_data[m_data.result==2])

    if a_w > b_w:
        stats[a]["Очки"]+=3
        stats[a]["Победы"]+=1
        stats[b]["Поражения"]+=1
    elif b_w > a_w:
        stats[b]["Очки"]+=3
        stats[b]["Победы"]+=1
        stats[a]["Поражения"]+=1
    else:
        stats[a]["Очки"]+=1
        stats[b]["Очки"]+=1
        stats[a]["Ничьи"]+=1
        stats[b]["Ничьи"]+=1

ldf = pd.DataFrame([
    {"Команда":t, **v} for t,v in stats.items()
]).sort_values(["Очки","Победы"], ascending=False)

st.dataframe(ldf, use_container_width=True)

# ======================
# ДЕМО
# ======================
if st.sidebar.button("🚀 Демо"):
    demo = []
    for _ in range(4):
        a,b = random.sample(st.session_state.team_list,2)
        for h in range(1,19):
            demo.append({
                "match_id": f"{min(a,b)}_vs_{max(a,b)}",
                "hole": h,
                "result": random.choice([0,1,2]),
                "pair_a":"A",
                "pair_b":"B"
            })
    pd.DataFrame(demo).to_csv(FILE, index=False)
    st.rerun()
