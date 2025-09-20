import sqlite3
import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client

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
        print(f"✅ Email sent for piglet {piglet_info['barcode']}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

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
        print(f"✅ SMS sent for piglet {piglet_info['barcode']} (SID {message.sid})")
    except Exception as e:
        print(f"❌ SMS failed: {e}")

# -----------------------------
# Dashboard App
# -----------------------------
init_alerts_table()
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2("🐖 Piglets Monitoring Dashboard", className="text-center my-3"),

    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id="table-selector",
            options=[
                {"label": "Male Piglets", "value": "MalePiglets"},
                {"label": "Female Piglets", "value": "FemalePiglets"}
            ],
            value="MalePiglets",
            clearable=False
        ), md=4),

        dbc.Col(dcc.Dropdown(
            id="location-filter",
            placeholder="Filter by Location",
            multi=True
        ), md=4),

        dbc.Col(dcc.Dropdown(
            id="health-filter",
            placeholder="Filter by Health Status",
            multi=True
        ), md=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="breed-chart"), md=4),
        dbc.Col(dcc.Graph(id="weight-chart"), md=4),
        dbc.Col(dcc.Graph(id="health-chart"), md=4),
    ]),

    html.H4("📋 Piglet Records", className="mt-4"),
    dash_table.DataTable(
        id="records-table",
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                "if": {"filter_query": "{health_status} = 'Sick'"},
                "backgroundColor": "#f8d7da",
                "color": "black",
                "fontWeight": "bold"
            },
            {
                "if": {"filter_query": "{health_status} = 'Healthy'"},
                "backgroundColor": "#d4edda",
                "color": "black"
            }
        ]
    )
], fluid=True)

# -----------------------------
# Callbacks
# -----------------------------
@app.callback(
    [Output("location-filter", "options"),
     Output("health-filter", "options")],
    [Input("table-selector", "value")]
)
def update_filters(table_name):
    df = get_data(table_name)
    loc_options = [{"label": loc, "value": loc} for loc in sorted(df["location"].dropna().unique())]
    health_options = [{"label": h, "value": h} for h in sorted(df["health_status"].dropna().unique())]
    return loc_options, health_options

@app.callback(
    [Output("breed-chart", "figure"),
     Output("weight-chart", "figure"),
     Output("health-chart", "figure"),
     Output("records-table", "data"),
     Output("records-table", "columns")],
    [Input("table-selector", "value"),
     Input("location-filter", "value"),
     Input("health-filter", "value")]
)
def update_dashboard(table_name, locations, health_statuses):
    df = get_data(table_name)

    # Apply filters
    if locations:
        df = df[df["location"].isin(locations)]
    if health_statuses:
        df = df[df["health_status"].isin(health_statuses)]

    if df.empty:
        return {}, {}, {}, [], []

    # -----------------
    # ALERTS
    # -----------------
    sick_piglets = df[df["health_status"] == "Sick"].to_dict("records")
    for piglet in sick_piglets:
        if not already_alerted(piglet["barcode"]):
            send_email_alert(piglet)
            send_sms_alert(piglet)
            mark_alerted(piglet["barcode"], table_name)

    # Charts
    breed_chart = px.histogram(df, x="breed", title="Breed Distribution")
    weight_chart = px.histogram(df, x="weight", nbins=10, title="Weight Distribution (kg)")
    health_chart = px.pie(df, names="health_status", title="Health Status Breakdown")

    # Table
    data = df.to_dict("records")
    columns = [{"name": i, "id": i} for i in df.columns]

    return breed_chart, weight_chart, health_chart, data, columns

# -----------------------------
# Run App
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8055)
