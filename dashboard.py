import streamlit as st
import pandas as pd
import gspread
from dotenv import load_dotenv
import os
from oauth2client.service_account import ServiceAccountCredentials

# ===== Load Environment Variables =====
load_dotenv()
CREDS_PATH = os.getenv("CREDS_PATH")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# ===== Google Sheets Auth =====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
client = gspread.authorize(creds)

# ===== Load Data =====
sheet = client.open_by_key(SPREADSHEET_ID).sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Convert dates
df["date_start"] = pd.to_datetime(df["date_start"])
df["date_stop"] = pd.to_datetime(df["date_stop"])

# ===== Streamlit UI =====
st.set_page_config(page_title="Facebook Ads Dashboard", layout="wide")
st.title("📊 Facebook Ads Performance Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("📅 Filters")
    campaign_filter = st.multiselect(
        "Campaign Name", options=df["campaign_name"].unique(), default=list(df["campaign_name"].unique())
    )
    date_range = st.date_input(
        "Date Range", [df["date_start"].min(), df["date_stop"].max()]
    )

# Apply filters
filtered_df = df[
    (df["campaign_name"].isin(campaign_filter)) &
    (df["date_start"] >= pd.to_datetime(date_range[0])) &
    (df["date_stop"] <= pd.to_datetime(date_range[1]))
]

# ===== KPI Metrics =====
total_spend = filtered_df["spend"].sum()
total_clicks = filtered_df["clicks"].sum()
total_impressions = filtered_df["impressions"].sum()
avg_cpc = filtered_df["cpc"].mean()
avg_ctr = filtered_df["ctr"].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💸 Total Spend", f"${total_spend:,.2f}")
col2.metric("🖱️ Total Clicks", f"{total_clicks:,}")
col3.metric("👀 Impressions", f"{total_impressions:,}")
col4.metric("💰 Avg. CPC", f"${avg_cpc:.2f}")
col5.metric("📈 Avg. CTR", f"{avg_ctr:.2f}%")

# ===== Spend Chart =====
st.subheader("📉 Spend Over Time")

if filtered_df["date_start"].nunique() > 1:
    time_chart = (
        filtered_df.groupby(pd.Grouper(key="date_start", freq="D"))["spend"].sum().reset_index()
    )
    st.line_chart(time_chart.rename(columns={"date_start": "index"}).set_index("index"))
else:
    st.info("📅 Not enough date variation to show 'Spend Over Time' chart.")

# ===== Smart Insight Panel =====
st.subheader("🧠 Automated Insight Summary")

insight = ""

# Basic rule-based analysis
if avg_ctr < 1:
    insight += "⚠️ CTR is quite low — consider improving creatives or tightening targeting.\n\n"
elif avg_ctr > 3:
    insight += "✅ CTR is strong! Ads are engaging well with your audience.\n\n"

if avg_cpc > 1.0:
    insight += "💸 CPC is high — test more budget-friendly audiences or creatives.\n\n"
elif avg_cpc < 0.50:
    insight += "👍 CPC is low — campaigns are cost-efficient!\n\n"

if total_clicks == 0:
    insight += "🛑 No clicks recorded — are campaigns running?\n\n"

if total_spend < 10:
    insight += "📉 Low spend detected — there may not be enough data for strong conclusions.\n\n"

# Show insights or fallback
if insight.strip():
    st.info(insight.strip())
else:
    st.success("✅ Performance looks stable based on current data.")

# ===== Detailed Table =====
st.subheader("🧾 Ad Performance Table")
st.dataframe(filtered_df.sort_values("spend", ascending=False))

st.caption("Dashboard updates live from your Google Sheet every time you load this page.")
