import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from streamlit_autorefresh import st_autorefresh
import cv2
from pyzbar import pyzbar
from ultralytics import YOLO
import numpy as np

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
    password = "your_app_password"
    recipient = "farmer_email@example.com"

    subject = f"🚨 Sick Piglet Alert: {piglet_info['barcode']}"
    notes_safe = piglet_info.get('notes', '').replace("{", "{{").replace("}", "}}")

    body = f"""A sick piglet has been detected.

Barcode: {piglet_info['barcode']}
Breed: {piglet_info['breed']}
Weight: {piglet_info['weight']} kg
Location: {piglet_info['location']}
Health Status: {piglet_info['health_status']}
Notes: {notes_safe}
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
            from_="+1234567890",
            to="+1987654321"
        )
        st.success(f"✅ SMS sent for piglet {piglet_info['barcode']} (SID {message.sid})")
    except Exception as e:
        st.error(f"❌ SMS failed: {e}")

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="Piglets Monitoring Dashboard", layout="wide")
init_alerts_table()

# Sidebar
st.sidebar.header("Dashboard Settings")
refresh_interval = st.sidebar.slider("Auto-refresh interval (seconds)", 5, 300, 30, 5)
auto_refresh_enabled = st.sidebar.checkbox("Enable Auto-Refresh", value=True)

if auto_refresh_enabled:
    st_autorefresh(interval=refresh_interval * 1000, key="refresh")

st.title("🐖 Piglets Monitoring Dashboard")

# Table selection
table_name = st.selectbox("Select Piglet Table", ["<All Piglets>", "MalePiglets", "FemalePiglets"], index=0)

# Load data
if table_name == "<All Piglets>":
    df = pd.concat([get_data("MalePiglets"), get_data("FemalePiglets")], ignore_index=True)
else:
    df = get_data(table_name)

# Filters
locations = st.multiselect("Filter by Location", sorted(df["location"].dropna().unique()))
health_statuses = st.multiselect("Filter by Health Status", sorted(df["health_status"].dropna().unique()))
if locations: df = df[df["location"].isin(locations)]
if health_statuses: df = df[df["health_status"].isin(health_statuses)]

# Alerts for sick piglets from table
for piglet in df[df["health_status"]=="Sick"].to_dict("records"):
    if not already_alerted(piglet["barcode"]):
        send_email_alert(piglet)
        send_sms_alert(piglet)
        mark_alerted(piglet["barcode"], table_name)

# -----------------------------
# Charts
# -----------------------------
col1, col2, col3 = st.columns(3)
if not df.empty:
    col1.plotly_chart(px.histogram(df, x="breed", title="Breed Distribution"), width="stretch")
    col2.plotly_chart(px.histogram(df, x="weight", nbins=10, title="Weight Distribution (kg)"), width="stretch")
    col3.plotly_chart(px.pie(df, names="health_status", title="Health Status Breakdown"), width="stretch")

# Top 5 heaviest
st.subheader("🏋️ Top 5 Heaviest Piglets")
if not df.empty:
    top5_df = df.nlargest(5, "weight")[["barcode","breed","weight","location","health_status"]]
    st.dataframe(top5_df, width="stretch")

# CSV download
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Filtered Piglets CSV", csv, "filtered_piglets.csv", "text/csv")

# Records table
st.subheader("📋 Piglet Records")
if not df.empty:
    st.dataframe(df, width="stretch")
else:
    st.warning("No records found with current filters.")

# -----------------------------
# Real-time Barcode Scanner
# -----------------------------
st.subheader("📹 Live Barcode Monitoring")
barcode_frame = st.image([])
cap_barcode = cv2.VideoCapture(0)
if st.button("Start Barcode Scanner"):
    for _ in range(200):
        ret, frame = cap_barcode.read()
        if not ret: break
        for barcode in pyzbar.decode(frame):
            x,y,w,h = barcode.rect
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            data = barcode.data.decode("utf-8")
            cv2.putText(frame,data,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
            if not already_alerted(data):
                record = df[df["barcode"]==data].to_dict("records")
                if record:
                    send_email_alert(record[0])
                    send_sms_alert(record[0])
                    mark_alerted(data, table_name)
        barcode_frame.image(frame, channels="BGR")

# -----------------------------
# YOLOv8 Visual Detection with Health Overlay
# -----------------------------
st.subheader("📹 Live Visual Piglet Monitoring (Object Detection)")
visual_frame = st.image([])
model = YOLO("yolov8n.pt")  # replace with custom model for health status
cap_yolo = cv2.VideoCapture(0)
alert_panel = st.empty()  # panel to show live alerts

recent_alerts = []

if st.button("Start Visual Monitoring"):
    for _ in range(200):
        ret, frame = cap_yolo.read()
        if not ret: break
        results = model(frame)
        annotated_frame = frame.copy()
        for box, cls_id, conf in zip(results[0].boxes.xyxy, results[0].boxes.cls, results[0].boxes.conf):
            x1,y1,x2,y2 = map(int,box)
            if cls_id == 1 and conf>0.5:  # sick piglet class
                color = (0,0,255)  # red
                label = f"Sick ({conf:.2f})"
                pig_id = f"camera_{x1}_{y1}"
                if not already_alerted(pig_id):
                    info = {"barcode": pig_id,"breed":"Unknown","weight":"Unknown","location":"Camera Area","health_status":"Sick","notes":""}
                    send_email_alert(info)
                    send_sms_alert(info)
                    mark_alerted(pig_id,"CameraFeed")
                    recent_alerts.append(info)
            else:
                color = (0,255,0)
                label = f"Healthy ({conf:.2f})"
            cv2.rectangle(annotated_frame,(x1,y1),(x2,y2),color,2)
            cv2.putText(annotated_frame,label,(x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)
        visual_frame.image(annotated_frame, channels="BGR")
        if recent_alerts:
            alert_panel.table(pd.DataFrame(recent_alerts))
