import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Piglet Monitoring Dashboard", layout="wide")

# ---------- Header ----------
st.title("🐷 Sunrise Piggery Dashboard")
st.markdown(f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ---------- Key Metrics ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Temperature", "28°C", delta="+1°C")
col2.metric("💧 Humidity", "70%", delta="-2%")
col3.metric("🐷 Piglets", "120", delta="+3")
col4.metric("⚠️ Alerts", "3")

# ---------- Health Overview ----------
st.subheader("Health Overview")
dates = pd.date_range(end=datetime.today(), periods=7)
weights = [5, 5.5, 6, 6.3, 6.8, 7, 7.2]  # mock data
health_df = pd.DataFrame({"Date": dates, "Avg Weight (kg)": weights})
fig_weight = px.line(health_df, x="Date", y="Avg Weight (kg)", markers=True)
st.plotly_chart(fig_weight, use_container_width=True)

# ---------- Environment Monitoring ----------
st.subheader("Environment Monitoring")
hours = [0, 6, 12, 18, 24]
temp_values = [26, 27, 29, 30, 28]
humidity_values = [65, 68, 70, 72, 70]
env_df = pd.DataFrame({
    "Hour": hours,
    "Temperature (°C)": temp_values,
    "Humidity (%)": humidity_values
})
fig_env = px.line(env_df, x="Hour", y=["Temperature (°C)", "Humidity (%)"], markers=True)
st.plotly_chart(fig_env, use_container_width=True)

# ---------- Alerts ----------
st.subheader("Active Alerts")
alerts = [
    {"message": "Piglet #45 not feeding", "severity": "red"},
    {"message": "Barn 2 overheating", "severity": "orange"},
    {"message": "All others stable", "severity": "green"},
]

for alert in alerts:
    color = {"red": "#ff4c4c", "orange": "#ffb84c", "green": "#4caf50"}[alert["severity"]]
    st.markdown(f"<p style='color:{color}; font-weight:bold'>🟢 {alert['message']}</p>", unsafe_allow_html=True)

# ---------- Piglet Records ----------
st.subheader("Piglet Records")
piglets_data = pd.DataFrame({
    "Piglet ID": ["001", "002", "003", "045"],
    "Weight (kg)": [7.0, 6.8, 7.1, 4.5],
    "Status": ["Healthy", "Healthy", "Healthy", "Sick"]
})

# Interactive selection
selected_piglet = st.selectbox("Select Piglet to view details", piglets_data["Piglet ID"])
piglet_info = piglets_data[piglets_data["Piglet ID"] == selected_piglet].iloc[0]

st.markdown(f"**Piglet ID:** {piglet_info['Piglet ID']}")
st.markdown(f"**Weight:** {piglet_info['Weight (kg)']} kg")
status_color = "#4caf50" if piglet_info["Status"] == "Healthy" else "#ff4c4c"
st.markdown(f"<p style='color:{status_color}; font-weight:bold'>Status: {piglet_info['Status']}</p>", unsafe_allow_html=True)

# ---------- Responsive Layout Note ----------
st.markdown("<p style='font-size:12px; color:gray'>This dashboard is mobile-friendly. Cards and charts resize automatically.</p>", unsafe_allow_html=True)
