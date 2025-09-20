# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import qrcode
from io import BytesIO
from pyzbar.pyzbar import decode
from PIL import Image

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Pig Weight Tracker with QR",
    layout="wide"
)

st.title("🐖 Pig Weight Monitoring with QR Codes")

# -------------------------------
# Initialize or Load Data
# -------------------------------
if "pig_data" not in st.session_state:
    st.session_state.pig_data = pd.DataFrame(columns=["Pig_ID", "Date", "Weight"])

data = st.session_state.pig_data

# -------------------------------
# Sidebar: Add Pig / Weight Entry
# -------------------------------
st.sidebar.header("Add Weight Entry")

# Option 1: Enter Pig ID manually
manual_pig_id = st.sidebar.text_input("Pig ID (manual entry)")

# Option 2: Upload QR code image to select Pig
uploaded_file = st.sidebar.file_uploader("Upload QR code image", type=["png", "jpg", "jpeg"])

selected_pig_id = None

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    decoded_objs = decode(img)
    if decoded_objs:
        # Assume first QR code in image
        selected_pig_id = decoded_objs[0].data.decode("utf-8").replace("Pig_ID:", "")
        st.sidebar.success(f"Detected Pig ID: {selected_pig_id}")
    else:
        st.sidebar.error("No QR code detected. Please upload a valid QR image.")

# Use manual entry if no QR scan
if selected_pig_id is None and manual_pig_id.strip() != "":
    selected_pig_id = manual_pig_id.strip()

# Date and weight input
entry_date = st.sidebar.date_input("Date")
entry_weight = st.sidebar.number_input("Weight (kg)", min_value=0.0, max_value=500.0, step=0.1)

# Add entry
if st.sidebar.button("Add Entry") and selected_pig_id is not None:
    new_row = pd.DataFrame({
        "Pig_ID": [selected_pig_id],
        "Date": [entry_date],
        "Weight": [entry_weight]
    })
    st.session_state.pig_data = pd.concat([st.session_state.pig_data, new_row], ignore_index=True)
    st.sidebar.success(f"Entry added for Pig {selected_pig_id}.")

# -------------------------------
# QR Code Generation
# -------------------------------
st.header("📱 Pig QR Codes")
unique_pigs = data["Pig_ID"].unique()

for pig_id in unique_pigs:
    st.subheader(f"Pig ID: {pig_id}")
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(f"Pig_ID:{pig_id}")
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=150)

# -------------------------------
# Plot Weight Charts
# -------------------------------
st.header("📊 Pig Weight Charts")

for pig_id in unique_pigs:
    pig_df = data[data["Pig_ID"] == pig_id]
    if not pig_df.empty:
        fig = px.line(
            pig_df,
            x="Date",
            y="Weight",
            title=f"Weight of Pig {pig_id} Over Time",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True, key=f"weight_chart_{pig_id}")
