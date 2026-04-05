import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import sqlite3
import joblib

def load_model():
    return joblib.load("model.pkl")

model = load_model()


# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="Digital Farm System", layout="wide")

st.markdown("""
<style>

/* ===== PREMIUM KPI CARDS ===== */
.kpi-card {
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    background: linear-gradient(145deg, #0f172a, #020617);
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.05);
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}

.kpi-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
}

/* Glow animation */
.kpi-card::before {
    content: "";
    position: absolute;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(0,255,255,0.15), transparent);
    animation: glow 6s linear infinite;
    top: -50%;
    left: -50%;
}

@keyframes glow {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Text styles */
.kpi-value {
    font-size: 32px;
    font-weight: 700;
    margin-top: 10px;
}

.kpi-label {
    font-size: 14px;
    opacity: 0.7;
}

.kpi-icon {
    font-size: 28px;
}

/* Gradient colors */
.safe { color: #22c55e; }
.unsafe { color: #ef4444; }

</style>
""", unsafe_allow_html=True)

# ===============================
# COUNTER ANIMATION
# ===============================
def animate_counter(value, speed=0.01):
    import time
    placeholder = st.empty()
    for i in range(0, int(value)+1, max(1, int(value/40)+1)):
        placeholder.markdown(f"<h2>{i}</h2>", unsafe_allow_html=True)
        time.sleep(0.01)
    placeholder.markdown(f"<h2>{value}</h2>", unsafe_allow_html=True)

# ===============================
# PROFESSIONAL LIGHT UI
# ===============================
st.markdown("""
<style>

/* ===== DARK BACKGROUND ===== */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #e2e8f0;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: #020617;
}

/* ===== CARD ===== */
.card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    text-align: center;
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-6px) scale(1.03);
}

/* ===== ICON ===== */
.card-icon {
    font-size: 30px;
    margin-bottom: 10px;
}

/* ===== SECTION ===== */
.section {
    background: rgba(255,255,255,0.04);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}

.fade-in {
    animation: fadeInUp 0.6s ease-in-out;
}

@keyframes fadeInUp {
    from {opacity: 0; transform: translateY(20px);}
    to {opacity: 1; transform: translateY(0);}
}

/* ===== TEXT COLORS ===== */
.safe { color: #22c55e; }
.unsafe { color: #ef4444; }

/* ===== GRADIENT CARDS ===== */
.card {
    background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(16,185,129,0.2));
    backdrop-filter: blur(14px);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 8px 25px rgba(0,0,0,0.6);
    transition: all 0.4s ease;
    border: 1px solid rgba(255,255,255,0.1);
}

.card:hover {
    transform: translateY(-8px) scale(1.05);
    box-shadow: 0 15px 40px rgba(0,0,0,0.8);
}

/* ICON */
.card-icon {
    font-size: 35px;
    margin-bottom: 10px;
}

/* COUNT TEXT */
.card h2 {
    font-size: 32px;
    font-weight: bold;
    margin-top: 10px;
}

/* ANIMATION */
.fade-in {
    animation: fadeInUp 0.8s ease-in-out;
}

@keyframes fadeInUp {
    from {opacity: 0; transform: translateY(30px);}
    to {opacity: 1; transform: translateY(0);}
}

</style>
""", unsafe_allow_html=True)

BASE_URL = "http://127.0.0.1:8000"

# ===============================
# LOGIN SYSTEM
# ===============================
USERS = {
    "admin": "1234",
    "farmer": "farm123",
    "vet": "vet123"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username

            if username == "admin":
                st.session_state.role = "Admin"
            elif username == "vet":
                st.session_state.role = "Veterinarian"
            else:
                st.session_state.role = "Farmer"

            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ===============================
# BACKEND CHECK
# ===============================
try:
    res = requests.get(BASE_URL)
    if res.status_code == 200:
        st.success("✅ Backend connected")
except:
    st.error("❌ Backend NOT reachable")

# ===============================
# SIDEBAR
# ===============================
st.sidebar.markdown("""
<div style="text-align:center; margin-bottom:20px;">
    <h2>🚜 Digital Farm</h2>
    <p style="color:gray;">Smart Monitoring System</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📋 AMU Records", "📈 Analytics", "🚨 Alerts", "🤖 AI Prediction", "📜 Prediction History"]
)


# ===============================
# DATA
# ===============================
def get_data():
    import sqlite3
    import pandas as pd

    try:
        conn = sqlite3.connect("digitalfarm.db")

        df = pd.read_sql_query(
            "SELECT * FROM predictions ORDER BY id DESC",
            conn
        )

        conn.close()

        return df

    except Exception as e:
        print("ERROR:", e)
        return pd.DataFrame()

# ===============================
# DASHBOARD
# ===============================
if page == "📊 Dashboard":

    df = get_data()

    st.title("📊 Dashboard Overview")

    if df.empty:
        st.warning("No data available")

    else:
        with st.spinner("Loading dashboard..."):
            import time
            time.sleep(1)

            # ================= KPI CARDS =================
            total_animals = len(df)
            total_records = len(df)
            safe_count = (df["result"] == "Safe").sum()
            unsafe_count = (df["result"] == "Unsafe").sum()

            col1, col2, col3, col4 = st.columns(4)
            
            col1.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">🐄</div>
                <div class="kpi-label">Animals</div>
                <div class="kpi-value">{total_animals}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col2.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">📦</div>
                <div class="kpi-label">Records</div>
                <div class="kpi-value">{total_records}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon safe">✅</div>
                <div class="kpi-label">Safe</div>
                <div class="kpi-value safe">{safe_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col4.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon unsafe">⚠️</div>
                <div class="kpi-label">Unsafe</div>
                <div class="kpi-value unsafe">{unsafe_count}</div>
            </div>
            """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)

            # ================= CHART SECTION =================
            col_left, col_right = st.columns([2, 1])

            # -------- LEFT (LINE CHART) --------
            with col_left:
                st.markdown('<div class="section fade-in">', unsafe_allow_html=True)
                st.subheader("📈 Safety Trend")

                trend_df = df.groupby("id")["mrl"].mean().reset_index()

                fig_line = px.line(
                    trend_df,
                    x="id",
                    y="mrl",
                    markers=True
                )

                fig_line.update_layout(
                    plot_bgcolor="#020617",
                    paper_bgcolor="#020617",
                    font=dict(color="white")
                )

                st.plotly_chart(fig_line, width="stretch")
                st.markdown("</div>", unsafe_allow_html=True)

            # -------- RIGHT (PIE CHART) --------
            with col_right:
                st.markdown('<div class="section fade-in">', unsafe_allow_html=True)
                st.subheader("🥧 Safety Split")

                fig_pie = px.pie(
                    names=["Safe", "Unsafe"],
                    values=[safe_count, unsafe_count],
                    hole=0.6
                )

                fig_pie.update_layout(
                    plot_bgcolor="#020617",
                    paper_bgcolor="#020617",
                    font=dict(color="white")
                )

                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ================= TABLE =================
            st.markdown('<div class="section fade-in">', unsafe_allow_html=True)
            st.subheader("📋 Latest Records")
            st.dataframe(df.head(10), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ===============================
# RECORDS
# ===============================
elif page == "📋 AMU Records":
    df = get_data()
    st.dataframe(df, use_container_width=True)

# ===============================
# ANALYTICS
# ===============================
elif page == "📈 Analytics":

    st.title("📈 Analytics Dashboard")

    conn = sqlite3.connect("digitalfarm.db")
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.warning("No data available")
    else:
        # Clean data
        df["result"] = df["result"].astype(str).str.strip()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # ---------------- METRICS ----------------
        st.subheader("📊 Prediction Summary")
        
        col1, col2 = st.columns(2)
        
        safe_count = (df["result"] == "Safe").sum()
        unsafe_count = (df["result"] == "Unsafe").sum()
        
        col1.metric("Safe Predictions", safe_count)
        col2.metric("Unsafe Predictions", unsafe_count)

        # ---------------- PIE CHART ----------------
        import plotly.express as px

        fig_pie = px.pie(
            df,
            names="result",
            title="Prediction Distribution"
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

        # ---------------- LINE CHART ----------------
        df_time = df.sort_values("timestamp")
        
        fig_line = px.line(
            df_time,
            x="timestamp",
            y="confidence",
            color="result",
            title="Confidence Over Time"
        )

        st.plotly_chart(fig_line, use_container_width=True)

        # ---------------- TABLE ----------------
        st.subheader("📄 Prediction Data")
        st.dataframe(df)

# ===============================
# ALERTS
# ===============================
elif page == "🚨 Alerts":
    try:
        alerts = requests.get(f"{BASE_URL}/alerts").json()
        st.dataframe(pd.DataFrame(alerts))
    except:
        st.success("No alerts")


# ===============================
# AI PREDICTION
# ===============================
elif page == "🤖 AI Prediction":

    import sqlite3
    from datetime import datetime
    import time
    import requests

    st.title("🤖 AI Prediction")
    st.markdown("### Enter Details")

    col1, col2, col3 = st.columns(3)

    dose = col1.number_input("💉 Dose", value=500)
    days = col2.number_input("📅 Days", value=5)
    mrl = col3.number_input("🧪 MRL", value=0.01)

    predict = st.button("🚀 Predict Now")

   

    # ===== PREDICTION =====
    if predict:

        with st.spinner("Analyzing data..."):
            time.sleep(1)

            try:
                response = requests.post(
                    "http://127.0.0.1:8000/predict",
                    json={
                        "dose": dose,
                        "days": days,
                        "mrl": mrl
                    }
                )

                data = response.json()

                result = data.get("prediction") or data.get("result")
                confidence = data.get("confidence", 0)

            except Exception as e:
                st.error("❌ Backend not reachable")
                st.stop()

        # ===== SAVE TO DB =====
        conn = sqlite3.connect("digitalfarm.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO predictions (dose, days, mrl, result, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (dose, days, mrl, result, confidence, datetime.now()))

        conn.commit()
        conn.close()

        # ===== DISPLAY RESULT =====
        st.markdown("### Prediction Result")

        if result == "Unsafe":
            st.error(f"⚠️ {result}")
        else:
            st.success(f"✅ {result}")

        st.progress(confidence / 100)
        st.write(f"**Confidence:** {confidence}%")

        
        
# ===============================
# HISTORY
# ===============================
elif page == "📜 Prediction History":

    st.title("📜 Prediction History")

    conn = sqlite3.connect("digitalfarm.db")
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.warning("No predictions yet")
    else:
        st.success(f"{len(df)} records found")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "history.csv"
        )