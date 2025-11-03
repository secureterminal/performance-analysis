import streamlit as st
import random
import numpy as np
import pandas as pd

# ----- Sidebar Navigation -----
st.set_page_config(page_title="Performance Dashboard", page_icon="📊", layout="wide")



# ----- Top Navigation Bar -----
spacing, notif_col, help_col, profile_col = st.columns([8, 1, 1, 2])
with notif_col:
    st.markdown("🔔", unsafe_allow_html=True)
with help_col:
    st.markdown("❓", unsafe_allow_html=True)
with profile_col:
    st.markdown("👤 **Bethany Sparks**", unsafe_allow_html=True)

st.title("Dashboard Home")  # Main page title (if needed)

# ----- Metrics -----
total_traffic = random.randint(250000, 400000)
traffic_delta = f"{random.randint(1, 15)}% ↑"
new_users = random.randint(2000, 5000)
users_delta = f"{random.randint(-5, 5)}% "
performance = random.uniform(60, 100)
perf_delta = f"{random.randint(-5, 5)}% "
sales = random.randint(300, 1000)
sales_delta = f"{random.randint(0, 20)}% ↑"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Traffic", f"{total_traffic:,}", traffic_delta)
col2.metric("New Users", f"{new_users:,}", f"{users_delta}%")
col3.metric("Performance", f"{performance:.1f}%", f"{perf_delta}%")
col4.metric("Sales", f"{sales:,}", f"{sales_delta}%")

# ----- Health Care & Weather Cards -----
st.markdown("### Updates")
card_col1, card_col2 = st.columns(2)
with card_col1:
    st.subheader("🏥 Health Care")
    st.write("Healthcare stats or info goes here...")
with card_col2:
    st.subheader("☀️ Weather Updates")
    st.write("Latest weather details go here...")

# ----- Download Updates -----
st.subheader("Download Updates")
csv_data = "date,metric\n2025-10-01,100\n2025-11-01,110"
st.download_button(
    label="Download Latest Report",
    data=csv_data,
    file_name="updates.csv",
    mime="text/csv",
    icon="📥",
)

# ----- Charts -----
months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
percentage_values = np.random.randint(50, 100, size=12)
order_values = np.random.randint(200, 500, size=12)

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.subheader("Percentage")
    st.line_chart(percentage_values)
with chart_col2:
    st.subheader("Total Orders")
    orders_df = pd.DataFrame({"Month": months, "Orders": order_values})
    orders_df = orders_df.set_index("Month")
    st.bar_chart(orders_df)
