import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import sqlite3
import joblib
import os

def load_model():
    model_path = os.path.join(os.getcwd(), "model.pkl")
    return joblib.load(model_path)

model = load_model()

st.set_page_config(page_title="Digital Farm System", layout="wide")

BASE_URL = "https://digital-farm-backend.onrender.com"

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
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📋 AMU Records", "📈 Analytics", "🚨 Alerts", "🤖 AI Prediction", "📜 Prediction History"]
)

# ===============================
# 🔥 FIXED DATA FUNCTION (ONLY FIXED PART)
# ===============================
def get_data():
    try:
        df = pd.read_csv("https://raw.githubusercontent.com/RAMYA09876/Digital-Farm-Backend/main/amu_residue_records_6000.csv")

        # 👉 FIX: CREATE MRL COLUMN
        if "mrl" not in df.columns:
            
            if "residue_mg_per_kg" in df.columns:
                df["mrl"] = df["residue_mg_per_kg"]
                
            else:
                st.error(f"❌ No residue column found. Available columns: {list(df.columns)}")
                return pd.DataFrame()

        df["mrl"] = pd.to_numeric(df["mrl"], errors="coerce").fillna(0)

        df["result"] = df["mrl"].apply(lambda x: "Safe" if x <= 0.05 else "Unsafe")

        # 👉 FIX: RESULT
        def classify(row):
            ratio = row["residue_mg_per_kg"] / row["mrl_limit_mg_per_kg"]

            if ratio <= 1:
                return "Safe"
            elif ratio <= 1.5:
                return "Warning"
            else:
                return "Critical"

        df["risk_level"] = df.apply(classify, axis=1)

        # 👉 FIX: OTHER COLUMNS
        if "confidence" not in df.columns:
            df["confidence"] = 100

        if "timestamp" not in df.columns:
            df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df))

        return df

    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# ===============================
# DASHBOARD
# ===============================
if page == "📊 Dashboard":

    df = get_data()

    # ================= FILTER =================
    farm_list = df["farm_id"].unique()
    selected_farm = st.selectbox("Select Farm", ["All"] + list(farm_list))

    if selected_farm != "All":
        df = df[df["farm_id"] == selected_farm]

    st.title("📊 Dashboard Overview")

    if df.empty:
        st.warning("No data available")

    else:

        total_animals = len(df)
        total_records = len(df)

        df["result"] = df["result"].astype(str).str.strip().str.lower()

        safe_count = (df["result"] == "safe").sum()
        unsafe_count = (df["result"] == "unsafe").sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Animals", total_animals)
        col2.metric("Records", total_records)
        col3.metric("Safe", safe_count)
        col4.metric("Unsafe", unsafe_count)

        if unsafe_count > 0:
            st.error(f"⚠️ {unsafe_count} unsafe records detected! Immediate action required.")
            
        else:
            st.success("✅ All livestock products are within safe MRL limits.")

        # ================= OPTIMIZED CHART =================
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        if df["timestamp"].isnull().all():
            df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df))

        # Aggregate for better visualization
        trend_df = df.copy()
    
        trend_df["month"] = trend_df["timestamp"].dt.to_period("M").astype(str)
        
        trend_df = trend_df.groupby("month")["mrl"].mean().reset_index()

        trend_df = trend_df.sort_values("month")
        
        trend_df = trend_df.tail(12)


        fig_line = px.line(
            trend_df,
            x="month",
            y="mrl",
            title="Average Monthly MRL Trend",
            markers=True
        )

        st.plotly_chart(fig_line, use_container_width=True)

        fig_pie = px.pie(
            names=["Safe", "Unsafe"],
            values=[safe_count, unsafe_count],
            title="MRL Compliance Distribution",
            hole=0.5
        )

        st.plotly_chart(fig_pie, use_container_width=True)

        # ================= FARM ANALYSIS =================
        st.subheader("🏭 Farm-wise Risk Analysis")

        farm_summary = df.groupby("farm_id")["mrl"].mean().reset_index()

        fig_bar = px.bar(
            farm_summary,
            x="farm_id",
            y="mrl",
            title="Average Residue Level per Farm",
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

        # ================= AI INSIGHT =================
        max_farm = farm_summary.loc[farm_summary["mrl"].idxmax(), "farm_id"]

        st.warning(f"⚠️ Farm {max_farm} shows highest residue levels. Inspection required.")

# ===============================
# RECORDS
# ===============================
elif page == "📋 AMU Records":
    df = get_data()

    # ================= DOWNLOAD =================
    csv = df.to_csv(index=False)

    st.download_button(
        label="📥 Download Data",
        data=csv,
        file_name="amu_records.csv",
        mime="text/csv"
    )

    # ================= SEARCH =================
    search = st.text_input("Search by Drug Name")

    if search:
        df = df[df["drug_name"].str.contains(search, case=False)]

    st.dataframe(df, use_container_width=True)

# ===============================
# ANALYTICS
# ===============================
elif page == "📈 Analytics":

    conn = sqlite3.connect("digitalfarm.db")
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.warning("No data available")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        safe_count = (df["result"] == "Safe").sum()
        unsafe_count = (df["result"] == "Unsafe").sum()

        col1, col2 = st.columns(2)
        col1.metric("Safe Predictions", safe_count)
        col2.metric("Unsafe Predictions", unsafe_count)

        fig_pie = px.pie(df, names="result")
        st.plotly_chart(fig_pie)

        fig_line = px.line(
            df.sort_values("timestamp"),
            x="timestamp",
            y="confidence",
            color="result"
        )

        st.plotly_chart(fig_line)

        st.dataframe(df)

# ===============================
# ALERTS
# ===============================
elif page == "🚨 Alerts":

    df = get_data()

    st.title("🚨 Alerts")

    alerts_df = df[df["result"] == "Unsafe"]
    
    if alerts_df.empty:
        
        st.success("✅ No unsafe records found.")
    else:
        st.error(f"⚠️ {len(alerts_df)} unsafe records detected!")
        
        st.dataframe(alerts_df, use_container_width=True)

    try:
        alerts = requests.get(f"{BASE_URL}/alerts").json()
        st.dataframe(pd.DataFrame(alerts))
    except:
        st.success("No alerts")

# ===============================
# AI PREDICTION
# ===============================
elif page == "🤖 AI Prediction":

    from datetime import datetime
    import time

    st.title("🤖 AI Prediction")

    dose = st.number_input("Dose", value=500)
    days = st.number_input("Days", value=5)
    mrl = st.number_input("MRL", value=0.01)

    if st.button("Predict"):

        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                json={"dose": dose, "days": days, "mrl": mrl}
            )

            data = response.json()
            result = data.get("prediction")
            confidence = data.get("confidence", 0)

        except:
            st.error("Backend error")
            st.stop()

        conn = sqlite3.connect("digitalfarm.db")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dose REAL,
            days REAL,
            mrl REAL,
            result TEXT,
            confidence REAL,
            timestamp TEXT
        )
        """)

        cursor.execute("""
        INSERT INTO predictions (dose, days, mrl, result, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (dose, days, mrl, result, confidence, datetime.now()))

        conn.commit()
        conn.close()

        if result == "Unsafe":
            st.error(result)
        else:
            st.success(result)

        st.write("Confidence:", confidence)

# ===============================
# HISTORY
# ===============================
elif page == "📜 Prediction History":

    conn = sqlite3.connect("digitalfarm.db")
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    conn.close()

    st.write("Total records:", len(df))
    st.dataframe(df)