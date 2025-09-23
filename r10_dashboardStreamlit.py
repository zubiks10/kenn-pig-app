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
import time

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
# Streamlit Setup
# -----------------------------
st.set_page_config(page_title="Piglets Monitoring Dashboard", layout="wide")
init_alerts_table()

# -----------------------------
# Custom CSS for Colors & Layout
# -----------------------------
st.markdown("""
<style>
.css-1d391kg { background-color: #f0f8ff; color: #333333; }
.css-1v3fvcr h2 { color: #2196F3; font-weight: bold; }
.css-1d391kg ~ div { background-color: #fffaf0; }
h1, h2, h3 { color: #FF5722; }

.button3d-green { background: linear-gradient(to bottom, #4CAF50 0%, #2E7D32 100%); border:none; color:white; padding:10px 24px; font-size:16px; cursor:pointer; border-radius:12px; box-shadow:0 5px #666; transition:0.2s;}
.button3d-green:hover { background: linear-gradient(to bottom, #66BB6A 0%, #388E3C 100%);}
.button3d-green:active { box-shadow:0 2px #666; transform:translateY(4px);}
.button3d-red { background: linear-gradient(to bottom, #F44336 0%, #C62828 100%); border:none; color:white; padding:10px 24px; font-size:16px; cursor:pointer; border-radius:12px; box-shadow:0 5px #666; transition:0.2s;}
.button3d-red:hover { background: linear-gradient(to bottom, #EF5350 0%, #B71C1C 100%);}
.button3d-red:active { box-shadow:0 2px #666; transform:translateY(4px);}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("Dashboard Settings")
refresh_interval = st.sidebar.slider("Auto-refresh interval (seconds)", 5, 300, 30, 5)
auto_refresh_enabled = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
if auto_refresh_enabled:
    st_autorefresh(interval=refresh_interval * 1000, key="refresh")

# -----------------------------
# Load & Filter Data
# -----------------------------
st.markdown("<h1 style='color:#2196F3'>🐖 Piglytics Monitoring Dashboard</h1>", unsafe_allow_html=True)
table_name = st.selectbox("Select Piglet Table", ["<All Piglets>", "MalePiglets", "FemalePiglets"], index=0)
if table_name == "<All Piglets>":
    df = pd.concat([get_data("MalePiglets"), get_data("FemalePiglets")], ignore_index=True)
else:
    df = get_data(table_name)

locations = st.multiselect("Filter by Location", sorted(df["location"].dropna().unique()))
health_statuses = st.multiselect("Filter by Health Status", sorted(df["health_status"].dropna().unique()))
if locations: df = df[df["location"].isin(locations)]
if health_statuses: df = df[df["health_status"].isin(health_statuses)]

# -----------------------------
# Session State
# -----------------------------
if 'monitoring_active' not in st.session_state: st.session_state.monitoring_active=False
if 'recent_barcode_alerts' not in st.session_state: st.session_state.recent_barcode_alerts=[]
if 'cap_camera' not in st.session_state: st.session_state.cap_camera=cv2.VideoCapture(0)
if 'model' not in st.session_state: st.session_state.model=YOLO("yolov8n.pt")

# -----------------------------
# Alerts for Sick Piglets
# -----------------------------
for piglet in df[df["health_status"]=="Sick"].to_dict("records"):
    if not already_alerted(piglet["barcode"]):
        send_email_alert(piglet)
        send_sms_alert(piglet)
        mark_alerted(piglet["barcode"], table_name)
        st.session_state.recent_barcode_alerts.append(piglet)

# -----------------------------
# Dynamic Sidebar Color
# -----------------------------
if any(df['health_status']=='Sick'):
    st.markdown("""<style>.css-1d391kg { background-color: #ffebee !important; color: #b71c1c !important; }</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>.css-1d391kg { background-color: #f0f8ff !important; color: #333333 !important; }</style>""", unsafe_allow_html=True)

# -----------------------------
# Charts (Flashing Sick Piglets)
# -----------------------------
st.markdown("<h2 style='color:#2196F3'>📊 Charts Overview</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
flash_frame = int(time.time()*2) % 2  # alternates 0/1 every 0.5s

if not df.empty:
    # Breed chart flashing
    df_breed = df.copy()
    df_breed['flash'] = 0
    df_breed.loc[df_breed['health_status']=='Sick','flash'] = flash_frame
    breed_colors = {b:"#D32F2F" if df_breed[(df_breed['breed']==b)&(df_breed['flash']==1)].shape[0]>0 else "#90CAF9" for b in df_breed['breed'].unique()}
    col1.plotly_chart(px.histogram(df_breed, x="breed", color="breed", color_discrete_map=breed_colors,
                                   title="Breed Distribution (Flashing Sick)"), use_container_width=True)

    # Weight chart flashing
    df_weight = df.copy()
    df_weight['flash'] = 0
    df_weight.loc[df_weight['health_status']=='Sick','flash'] = flash_frame
    weight_colors = {"Healthy":"#4CAF50","Sick":"#F44336","Unknown":"#FFC107"}
    if st.session_state.recent_barcode_alerts:
        weight_colors["Sick"] = "#D32F2F" if flash_frame==1 else "#F44336"
    col2.plotly_chart(px.histogram(df_weight, x="weight", color="health_status", barmode="overlay",
                                   color_discrete_map=weight_colors, title="Weight Distribution (Flashing Sick)"),
                      use_container_width=True)

    # Health Status pie chart
    color_map={"Healthy":"#4CAF50","Sick":"#F44336","Unknown":"#FFC107"}
    if st.session_state.recent_barcode_alerts: color_map["Sick"]="#D32F2F" if flash_frame==1 else "#F44336"
    col3.plotly_chart(px.pie(df, names="health_status", color="health_status", color_discrete_map=color_map,
                             title="Health Status Breakdown"), use_container_width=True)

# -----------------------------
# Table Highlighting
# -----------------------------
def highlight_recent(row):
    color=""
    if row['barcode'] in [a['barcode'] for a in st.session_state.recent_barcode_alerts]:
        color="background-color: #FFCDD2;"
    elif row['health_status']=="Sick":
        color="background-color: #F28C8C;"
    elif row['health_status']=="Healthy":
        color="background-color: #B8F28C;"
    return [color]*len(row)

st.markdown("<h2 style='color:#E91E63'>📋 Piglet Records</h2>", unsafe_allow_html=True)
if not df.empty:
    st.dataframe(df.style.apply(highlight_recent, axis=1), width="stretch")
else:
    st.warning("No records found with current filters.")

# -----------------------------
# Alert Banner Pulsing
# -----------------------------
if st.session_state.recent_barcode_alerts:
    banner_color = "#ff1744" if flash_frame==1 else "#FF5252"
    st.markdown(f"""<div style="background-color:{banner_color};padding:10px;border-radius:5px;color:white;font-weight:bold">
        🚨 {len(st.session_state.recent_barcode_alerts)} New Sick Piglet Alert(s)!
    </div>""", unsafe_allow_html=True)

# -----------------------------
# Camera Monitoring
# -----------------------------
st.markdown("<h2 style='color:#E91E63'>📹 Live Monitoring</h2>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Start Monitoring", key="start"):
        st.session_state.monitoring_active=True
with col2:
    if st.button("🛑 Stop Monitoring", key="stop"):
        st.session_state.monitoring_active=False
        if st.session_state.cap_camera: st.session_state.cap_camera.release()

camera_display=st.empty()
alert_panel=st.empty()

def process_frame(frame):
    alerts=[]
    if frame is None: return frame, alerts
    for barcode in pyzbar.decode(frame):
        x, y, w, h = barcode.rect
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        data = barcode.data.decode("utf-8")
        cv2.putText(frame,data,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
        if not already_alerted(data):
            record=df[df["barcode"]==data].to_dict("records")
            if record:
                send_email_alert(record[0])
                send_sms_alert(record[0])
                mark_alerted(data, table_name)
                alerts.append(record[0])
    try:
        results=st.session_state.model(frame)
        if results:
            for box, cls_id, conf in zip(results[0].boxes.xyxy, results[0].boxes.cls, results[0].boxes.conf):
                x1,y1,x2,y2=map(int,box)
                color=(0,0,255) if time.time()%1>0.5 else (0,100,255)
                label=f"Sick ({conf:.2f})" if cls_id==1 and conf>0.5 else f"Healthy ({conf:.2f})"
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
                cv2.putText(frame,label,(x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)
                if cls_id==1 and conf>0.5:
                    pig_id=f"camera_{x1}_{y1}"
                    if not already_alerted(pig_id):
                        info={"barcode":pig_id,"breed":"Unknown","weight":"Unknown","location":"Camera Area","health_status":"Sick","notes":""}
                        send_email_alert(info)
                        send_sms_alert(info)
                        mark_alerted(pig_id,"CameraFeed")
                        alerts.append(info)
    except Exception as e:
        st.error(f"YOLO prediction failed: {e}")
    return frame, alerts

if st.session_state.monitoring_active:
    while st.session_state.monitoring_active:
        ret, frame = st.session_state.cap_camera.read()
        if not ret or frame is None:
            st.warning("⚠️ Unable to read from camera.")
            time.sleep(0.1)
            continue
        annotated_frame, alerts = process_frame(frame)
        camera_display.image(annotated_frame, channels="BGR")
        if alerts:
            st.session_state.recent_barcode_alerts.extend(alerts)
            alert_panel.table(pd.DataFrame(st.session_state.recent_barcode_alerts))
        time.sleep(0.01)
