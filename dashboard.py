import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Ken's Global Farm Dashboard", layout="wide")

# ---------- Detect screen width ----------
st.markdown("""
    <script>
    const width = window.innerWidth;
    window.parent.postMessage({func:'setWidth', width: width}, '*')
    </script>
    """, unsafe_allow_html=True)

if 'screen_width' not in st.session_state:
    st.session_state.screen_width = 1000  # default

def width_listener():
    import streamlit.components.v1 as components
    components.html("""
        <script>
        const sendWidth = () => {
            const w = window.innerWidth;
            window.parent.postMessage({func:'setWidth', width: w}, '*')
        };
        window.addEventListener('resize', sendWidth);
        sendWidth();
        </script>
    """, height=0)

width_listener()

# ---------- Header with Pig Logo ----------
st.markdown(
    """
    <div style='display:flex; align-items:center; gap:10px'>
        <img src='https://cdn-icons-png.flaticon.com/512/616/616408.png' width='50' height='50'>
        <h1 style='margin:0'>Ken's Global Farm Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ---------- Key Metrics with Icons ----------
metrics = [
    ("🌡️ Temperature", "28°C", "+1°C"),
    ("💧 Humidity", "70%", "-2%"),
    ("🐷 Piglets", "120", "+3"),
    ("⚠️ Alerts", "3", None)
]

if st.session_state.screen_width >= 768:
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        if delta:
            col.metric(label, value, delta)
        else:
            col.metric(label, value)
else:
    for label, value, delta in metrics:
        if delta:
            st.metric(label, value, delta)
        else:
            st.metric(label, value)

# ---------- Health Overview ----------
st.subheader("Health Overview")
dates = pd.date_range(end=datetime.today(), periods=7)
weights = [5, 5.5, 6, 6.3, 6.8, 7, 7.2]
health_df = pd.DataFrame({"Date": dates, "Avg Weight (kg)": weights})
fig_weight = px.line(health_df, x="Date", y="Avg Weight (kg)", markers=True)
st.plotly_chart(fig_weight, use_container_width=True)

# ---------- Environment Monitoring with Icons ----------
st.subheader("Environment Monitoring")
hours = [0, 6, 12, 18, 24]
temp_values = [26, 27, 29, 30, 28]
humidity_values = [65, 68, 70, 72, 70]

env_df = pd.DataFrame({
    "Hour": hours,
    "🌡️ Temperature (°C)": temp_values,
    "💧 Humidity (%)": humidity_values
})

fig_env = px.line(env_df, x="Hour", y=["🌡️ Temperature (°C)", "💧 Humidity (%)"], markers=True)
fig_env.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    )
)
st.plotly_chart(fig_env, use_container_width=True)

# ---------- Alerts with Icons ----------
st.subheader("Active Alerts")
alerts = [
    {"message": "🐷 Piglet #45 not feeding", "severity": "red"},
    {"message": "🌡️ Barn 2 overheating", "severity": "orange"},
    {"message": "✅ All others stable", "severity": "green"},
]

if st.session_state.screen_width >= 768:
    cols = st.columns(len(alerts))
    for col, alert in zip(cols, alerts):
        color = {"red": "#ff4c4c", "orange": "#ffb84c", "green": "#4caf50"}[alert["severity"]]
        col.markdown(
            f"<div style='background-color:{color}; padding:15px; border-radius:10px; color:white; font-weight:bold; text-align:center'>{alert['message']}</div>",
            unsafe_allow_html=True
        )
else:
    for alert in alerts:
        color = {"red": "#ff4c4c", "orange": "#ffb84c", "green": "#4caf50"}[alert["severity"]]
        st.markdown(
            f"<div style='background-color:{color}; padding:15px; border-radius:10px; color:white; font-weight:bold; margin-bottom:10px'>{alert['message']}</div>",
            unsafe_allow_html=True
        )

# ---------- Piglet Records with Icons ----------
st.subheader("Piglet Records")
piglets_data = pd.DataFrame({
    "Piglet ID": ["001", "002", "003", "045"],
    "Weight (kg)": [7.0, 6.8, 7.1, 4.5],
    "Status": ["Healthy", "Healthy", "Healthy", "Sick"]
})

if st.session_state.screen_width >= 768:
    st.dataframe(piglets_data)
else:
    for _, row in piglets_data.iterrows():
        if row["Status"] == "Healthy":
            status_icon = "❤️"
            status_color = "#4caf50"
        else:
            status_icon = "❌"
            status_color = "#ff4c4c"
        
        st.markdown(f"""
            <div style='background-color:#f9f9f9; padding:15px; border-radius:12px; margin-bottom:12px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1)'>
                <p><strong>🐷 ID:</strong> {row['Piglet ID']}</p>
                <p><strong>⚖️ Weight:</strong> {row['Weight (kg)']} kg</p>
                <p><strong>{status_icon} Status:</strong> 
                   <span style='color:{status_color}; font-weight:bold'>{row['Status']}</span></p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<p style='font-size:12px; color:gray'>Fully responsive: stacked metrics, charts, alerts, and piglet cards optimized for mobile view.</p>", unsafe_allow_html=True)
