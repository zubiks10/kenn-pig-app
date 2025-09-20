import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from streamlit_autorefresh import st_autorefresh  # <-- Auto-refresh

# -----------------------------
# Database Helper
# -----------------------------
def get_data(table_name):
    conn = sqlite3.connect("piglets.db")
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def init_alerts_table():
    conn = sqlite3.connect("piglets.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AlertsSent (
        barcode TEXT PRIMARY KEY,
        table_name TEXT,
        alerted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def already_alerted(barcode):
    conn = sqlite3.connect("piglets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM AlertsSent WHERE barcode=?", (barcode,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def mark_alerted(barcode, table_name):
    conn = sqlite3.connect("piglets.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO AlertsSent (barcode, table_name) VALUES (?, ?)", (barcode, table_name))
    conn.commit()
    conn.close()

# -----------------------------
# Alert Functions
# -----------------------------
def send_email_alert(piglet_info):
    sender = "your_email@gmail.com"
    password = "your_app_password"  # from Gmail App Passwords
    recipient = "farmer_email@example.com"

    subject = f"🚨 Sick Piglet Alert: {piglet_info['barcode']}"
    body = f"""
    A sick piglet has been detected.

    Barcode: {piglet_info['barcode']}
    Breed: {piglet_info['breed']}
    Weight: {piglet_info['weight']} kg
    Location: {piglet_info['location']}
    Health Status: {piglet_info['health_status']}
    Notes: {piglet_info['notes']}
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        st.success(f"✅ Email sent for piglet {piglet_info['barcode']}")
    except Exception as e:
        st.error(f"❌ Email failed: {e}")

def send_sms_alert(piglet_info):
    account_sid = "your_twilio_sid"
    auth_token = "your_twilio_auth_token"
    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            body=f"🚨 Sick Piglet Alert! Barcode: {piglet_info['barcode']}, Location: {piglet_info['location']}, Breed: {piglet_info['breed']}, Weight: {piglet_info['weight']}kg",
            from_="+1234567890",  # Your Twilio number
            to="+1987654321"      # Farmer’s phone number
        )
        st.success(f"✅ SMS sent for piglet {piglet_info['barcode']} (SID {message.sid})")
    except Exception as e:
        st.error(f"❌ SMS failed: {e}")

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="Piglets Monitoring Dashboard", layout="wide")
init_alerts_table()

# Auto-refresh every 30 seconds
st_autorefresh(interval=30 * 1000, key="refresh")

st.title("🐖 Piglets Monitoring Dashboard (auto-refresh every 30s)")

# Dropdowns
table_name = st.selectbox(
    "Select Piglet Table",
    ["MalePiglets", "FemalePiglets"],
    index=0
)

df = get_data(table_name)

locations = st.multiselect("Filter by Location", sorted(df["location"].dropna().unique()))
health_statuses = st.multiselect("Filter by Health Status", sorted(df["health_status"].dropna().unique()))

# Apply filters
if locations:
    df = df[df["location"].isin(locations)]
if health_statuses:
    df = df[df["health_status"].isin(health_statuses)]

# Alerts
sick_piglets = df[df["health_status"] == "Sick"].to_dict("records")
for piglet in sick_piglets:
    if not already_alerted(piglet["barcode"]):
        send_email_alert(piglet)
        send_sms_alert(piglet)
        mark_alerted(piglet["barcode"], table_name)

# Show charts
col1, col2, col3 = st.columns(3)

with col1:
    if not df.empty:
        st.plotly_chart(px.histogram(df, x="breed", title="Breed Distribution"), width="auto")

with col2:
    if not df.empty:
        st.plotly_chart(px.histogram(df, x="weight", nbins=10, title="Weight Distribution (kg)"), width="auto")

with col3:
    if not df.empty:
        st.plotly_chart(px.pie(df, names="health_status", title="Health Status Breakdown"), width="auto")

# Records Table
st.subheader("📋 Piglet Records")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No records found with current filters.")
