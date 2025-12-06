import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime
import time
import calendar
# internal imports
import calcs
from helper_functions import human_format, apply_filters, get_valid_date_range

airtel_css = """
    <style>
        .stVerticalBlock.st-emotion-cache-1gz5zxc.e196pkbe2 {
            border: 2px solid red;
            padding: 10px;
            border-radius: 8px;
        }
    </style>
"""
mtn_css = """
    <style>
        .stVerticalBlock.st-emotion-cache-1gz5zxc.e196pkbe2 {
            border: 2px solid #FDCC00;
            padding: 10px;
            border-radius: 8px;
        }
    </style>
"""
show_sidebar = """
    <style>
        .stSidebar .st-emotion-cache-1m5fwvu .e6f82ta0 {
            display: None;}
    </style>
"""
hide_sidebar = """
    <style>
        .stSidebar .st-emotion-cache-1m5fwvu .e6f82ta0 {
            display: none;}
    </style>
"""

remove_padding_css = """
    <style>
        .st-emotion-cache-zy6yx3 {
            padding: 2rem !important;
        }
        


    </style>
"""

# Apply the CSS
st.markdown(remove_padding_css, unsafe_allow_html=True)


zone = "South"
CUSTOMERS = ["MTN NG", "Airtel NG"]

# Block unauthenticated access
if not st.session_state.get("logged_in", False):
    st.markdown(hide_sidebar, unsafe_allow_html=True)
    st.error("🔒 Please log in to view this page.")
    st.session_state.login_messages = "Please login to view this site"
    st.switch_page("🏠 Homepage.py")
else:
    st.markdown(show_sidebar, unsafe_allow_html=True)

st.set_page_config(layout="wide", page_title="Site Information Dashboard")

# ----------------------------
# Load Data
# ----------------------------
df1 = st.session_state["df_init"]
pa_df1 = st.session_state["pa_init"]
db1 = st.session_state["db"]
db_full1 = st.session_state["db_full"]

df = df1.copy()
db = db1.copy()
pa_df = pa_df1.copy()
db_full = db_full1.copy()

pa_df = pd.merge(pa_df, db, on="IHS Site ID", how="left")

# Get the maximum date in the dataframe
max_date = df['Date'].max()
max_date_dt = pd.to_datetime(max_date)

# Extract year, week, and month from the maximum date
max_year = max_date_dt.year
max_week = max_date_dt.isocalendar().week
max_month = max_date_dt.month

# Get minimum week from minimum date
min_date = df['Date'].min()
min_date_dt = pd.to_datetime(min_date)
min_week = min_date_dt.isocalendar().week

# Filter DataFrame for the week containing the max date
df['Datetime'] = pd.to_datetime(df['Date'])
df['ISO_Year'] = df['Datetime'].dt.isocalendar().year
df['Week'] = df['Datetime'].dt.isocalendar().week

week_df = df[(df['ISO_Year'] == max_date_dt.isocalendar().year) & 
             (df['Week'] == max_week)]
max_wk_min_date = week_df['Date'].min()
max_wk_max_date = week_df['Date'].max()

def is_week_complete(df_fxn):
    """Check if the latest week has 7 days of data"""
    df_fxn = df_fxn.copy()
    df_fxn['Date'] = pd.to_datetime(df_fxn['Date'])
    
    # Get the latest date
    latest_date = df_fxn['Date'].max()
    latest_iso_year = latest_date.isocalendar().year
    latest_week = latest_date.isocalendar().week
    
    # Filter for the latest week
    latest_week_df = df_fxn[
        (df_fxn['Date'].dt.isocalendar().year == latest_iso_year) & 
        (df_fxn['Date'].dt.isocalendar().week == latest_week)
    ]
    
    # Count unique dates in the latest week
    unique_days = latest_week_df['Date'].nunique()
    
    return unique_days == 7

# ----------------------------
# Sidebar: Filters
# ----------------------------
st.sidebar.header("Filters")

# Zone Filter
df = df[df["Zone"] == zone].copy()
pa_df = pa_df[pa_df["Zone"] == zone].copy()

# Date range input
try:
    min_date, max_date = get_valid_date_range(pa_df, "Date")
except ValueError as e:
    st.error(str(e))
    st.stop()

date_range = st.sidebar.date_input(
    "Select date range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = min_date
    end_date = max_date

# Filter between start and end dates
# Convert date objects to datetime for comparison
start_datetime = pd.to_datetime(start_date)
end_datetime = pd.to_datetime(end_date)

pa_df = pa_df[(pa_df["Date"] >= start_datetime) & 
              (pa_df["Date"] <= end_datetime)].copy()
df = df[(df["Date"] >= start_datetime) & 
        (df["Date"] <= end_datetime)].copy()

# Store original dataframes AFTER date filtering but BEFORE site filtering
if 'df_original' not in st.session_state:
    st.session_state.df_original = df.copy()
if 'pa_df_original' not in st.session_state:
    st.session_state.pa_df_original = pa_df.copy()

# Update stored dataframes when date range changes
current_date_range = (start_date, end_date)
if 'stored_date_range' not in st.session_state:
    st.session_state.stored_date_range = current_date_range
    
if st.session_state.stored_date_range != current_date_range:
    st.session_state.df_original = df.copy()
    st.session_state.pa_df_original = pa_df.copy()
    st.session_state.stored_date_range = current_date_range
    st.session_state.ihs_site_id = "Select Site"
    st.session_state.tenant_site_id = "Select Site"

# Initialize session state for site selections
if 'ihs_site_id' not in st.session_state:
    if not df.empty:
        top_site = df["IHS Site ID"].value_counts().idxmax()
        st.session_state.ihs_site_id = top_site
    else:
        st.session_state.ihs_site_id = "Select Site"
    
if 'tenant_site_id' not in st.session_state:
    site_ids = df["IHS Site ID"].dropna().sort_values().unique().tolist()
    db_filtered = db_full[db_full["IHS Site ID"].isin(site_ids)]
    if st.session_state.ihs_site_id != "Select Site":
        top_tenant = db_filtered.loc[db_filtered["IHS Site ID"] == st.session_state.ihs_site_id, "tenant_and_id"]
        st.session_state.tenant_site_id = top_tenant.iloc[0] if not top_tenant.empty else "Select Site"
    else:
        st.session_state.tenant_site_id = "Select Site"

# Use original dataframes for creating the lists
df_work = st.session_state.df_original
pa_df_work = st.session_state.pa_df_original

# Prepare data
site_ids = df_work["IHS Site ID"].dropna().sort_values().unique().tolist()
db_filtered = db_full[db_full["IHS Site ID"].isin(site_ids)]

site_list = ["Select Site"] + site_ids
tenant_site_list = ["Select Site"] + db_filtered["tenant_and_id"].dropna().sort_values().unique().tolist()

# Callback functions
def on_ihs_change():
    site_id = st.session_state.ihs_selectbox
    df_temp = st.session_state.df_original
    site_ids_temp = df_temp["IHS Site ID"].dropna().sort_values().unique().tolist()
    db_filtered_temp = db_full[db_full["IHS Site ID"].isin(site_ids_temp)]
    
    if site_id != "Select Site":
        matching_tenants = db_filtered_temp.loc[db_filtered_temp["IHS Site ID"] == site_id, "tenant_and_id"].dropna()
        if not matching_tenants.empty:
            st.session_state.tenant_site_id = matching_tenants.iloc[0]
        else:
            st.session_state.tenant_site_id = "Select Site"
    else:
        st.session_state.tenant_site_id = "Select Site"
    st.session_state.ihs_site_id = site_id

def on_tenant_change():
    tenant_id = st.session_state.tenant_selectbox
    df_temp = st.session_state.df_original
    site_ids_temp = df_temp["IHS Site ID"].dropna().sort_values().unique().tolist()
    db_filtered_temp = db_full[db_full["IHS Site ID"].isin(site_ids_temp)]
    
    if tenant_id != "Select Site":
        matching_ihs = db_filtered_temp.loc[db_filtered_temp["tenant_and_id"] == tenant_id, "IHS Site ID"].dropna()
        if not matching_ihs.empty:
            st.session_state.ihs_site_id = matching_ihs.iloc[0]
        else:
            st.session_state.ihs_site_id = "Select Site"
    else:
        st.session_state.ihs_site_id = "Select Site"
    st.session_state.tenant_site_id = tenant_id

# Get current index values
ihs_index = site_list.index(st.session_state.ihs_site_id) if st.session_state.ihs_site_id in site_list else 0
tenant_index = tenant_site_list.index(st.session_state.tenant_site_id) if st.session_state.tenant_site_id in tenant_site_list else 0

# Create selectboxes with callbacks
site_id = st.sidebar.selectbox(
    "IHS Site ID", 
    site_list, 
    index=ihs_index,
    key='ihs_selectbox',
    on_change=on_ihs_change
)

tenant_site_id = st.sidebar.selectbox(
    "Tenant Site ID", 
    tenant_site_list, 
    index=tenant_index,
    key='tenant_selectbox',
    on_change=on_tenant_change
)

# Apply filters to dataframes
final_site_id = st.session_state.ihs_site_id

if final_site_id and final_site_id != "Select Site":
    if final_site_id in df_work["IHS Site ID"].values:
        df = df_work[df_work["IHS Site ID"] == final_site_id].copy()
        pa_df = pa_df_work[pa_df_work["IHS Site ID"] == final_site_id].copy()
        
        st.sidebar.success(f"IHS Site: {final_site_id}")
        st.sidebar.info(f"Tenant: {st.session_state.tenant_site_id}")
    else:
        st.sidebar.error(f"Site ID '{final_site_id}' not found in the selected date range.")
        df = df_work.iloc[0:0]
        pa_df = pa_df_work.iloc[0:0]
else:
    df = df_work
    pa_df = pa_df_work
    st.sidebar.info("Please select a site to filter data.")













# ----------------------------
# Simulated Data
# ----------------------------
# states = ['California', 'Texas', 'Florida', 'New York', 'Pennsylvania',
#           'Illinois', 'Ohio', 'Georgia', 'North Carolina', 'Michigan']
# populations = np.random.randint(10000000, 40000000, size=len(states))
# gains = np.random.randint(-100000, 100000, size=2)
# themes = {"blues": "Blues", "reds": "Reds", "greens": "Greens"}
























# ----------------------------
# Calculate Gains/Percentage Changes
# ----------------------------

# 1. OVERALL OUTAGE COUNT GAIN (compared to average of all sites)
# Get all sites' outage counts
all_sites_outage_counts = df_work.groupby("IHS Site ID")["Outage Count"].sum()
avg_outage_all_sites = all_sites_outage_counts.mean()
current_site_outage = sum(df["Outage Count"])

# Calculate percentage difference from average (lower is better, so negative is good)
if avg_outage_all_sites > 0:
    overall_outage_gain = ((current_site_outage - avg_outage_all_sites) / avg_outage_all_sites) * 100
else:
    overall_outage_gain = 0

# 2. WEEKLY OUTAGE COUNT GAIN (compared to previous week)
current_week_count = sum(df[df['Week'] == max_week]["Outage Count"])

# Handle week 1 - get last week of previous year
if max_week == 1:
    prev_year = max_year - 1
    prev_week_df = df[(df['Year'] == prev_year)]
    if not prev_week_df.empty:
        prev_week = prev_week_df['Week'].max()
        prev_week_count = sum(df[(df['Year'] == prev_year) & (df['Week'] == prev_week)]["Outage Count"])
    else:
        prev_week_count = 0
else:
    prev_week = max_week - 1
    prev_week_count = sum(df[(df['Year'] == max_year) & (df['Week'] == prev_week)]["Outage Count"])


# Calculate percentage change (lower is better, so negative is good)
if prev_week_count > 0:
    weekly_outage_gain = ((current_week_count - prev_week_count) / prev_week_count) * 100
else:
    weekly_outage_gain = 0 if current_week_count == 0 else 100

# 3. MONTHLY OUTAGE COUNT GAIN (compared to previous month)
current_month_count = sum(df[df['Month'] == calendar.month_name[max_month]]["Outage Count"])

# Handle January - get December of previous year
if max_month == 1:
    prev_year = max_year - 1
    prev_month = 12
    prev_month_count = sum(df[(df['Year'] == prev_year) & (df['Month'] == calendar.month_name[prev_month])]["Outage Count"])
else:
    prev_month = max_month - 1
    prev_month_count = sum(df[(df['Year'] == max_year) & (df['Month'] == calendar.month_name[prev_month])]["Outage Count"])

# Calculate percentage change (lower is better, so negative is good)
if prev_month_count > 0:
    monthly_outage_gain = ((current_month_count - prev_month_count) / prev_month_count) * 100
else:
    monthly_outage_gain = 0 if current_month_count == 0 else 100


# 4. MONTHLY PA GAIN (compared to previous month)
pa_df = pa_df.copy()  # Add this line
pa_df.loc[:, 'Datetime'] = pd.to_datetime(pa_df['Date'], errors='coerce')
pa_df.loc[:, 'Year'] = pa_df['Datetime'].dt.year
pa_df.loc[:, 'Month'] = pa_df['Datetime'].dt.month

latest_year = pa_df['Year'].max()
latest_month = pa_df[pa_df['Year'] == latest_year]['Month'].max()
latest_month_df = pa_df[(pa_df['Year'] == latest_year) & (pa_df['Month'] == latest_month)]
monthly_avg_pa = pd.to_numeric(latest_month_df['PA'], errors='coerce').mean()

# Handle January - get December of previous year
if latest_month == 1:
    prev_year_pa = latest_year - 1
    prev_month_pa = 12
    prev_month_df = pa_df[(pa_df['Year'] == prev_year_pa) & (pa_df['Month'] == prev_month_pa)]
else:
    prev_month_pa = latest_month - 1
    prev_month_df = pa_df[(pa_df['Year'] == latest_year) & (pa_df['Month'] == prev_month_pa)]

prev_monthly_avg_pa = pd.to_numeric(prev_month_df['PA'], errors='coerce').mean()

# Calculate percentage change (higher is better, so positive change is good)
if prev_monthly_avg_pa > 0 and not pd.isna(prev_monthly_avg_pa):
    monthly_pa_gain = ((monthly_avg_pa - prev_monthly_avg_pa) / prev_monthly_avg_pa) * 100
else:
    monthly_pa_gain = 0

# 5. WEEKLY PA GAIN (compared to previous week)
pa_df.loc[:, 'Week'] = pa_df['Datetime'].dt.isocalendar().week
pa_df.loc[:, 'ISO_Year'] = pa_df['Datetime'].dt.isocalendar().year

latest_iso_year = pa_df['ISO_Year'].max()
latest_week = pa_df[pa_df['ISO_Year'] == latest_iso_year]['Week'].max()
latest_week_df = pa_df[(pa_df['ISO_Year'] == latest_iso_year) & (pa_df['Week'] == latest_week)]
weekly_avg_pa = pd.to_numeric(latest_week_df['PA'], errors='coerce').mean()

# Handle week 1 - get last week of previous year
if latest_week == 1:
    prev_iso_year = latest_iso_year - 1
    prev_week_pa_df = pa_df[pa_df['ISO_Year'] == prev_iso_year]
    if not prev_week_pa_df.empty:
        prev_week_pa = prev_week_pa_df['Week'].max()
        prev_week_df_pa = pa_df[(pa_df['ISO_Year'] == prev_iso_year) & (pa_df['Week'] == prev_week_pa)]
    else:
        prev_week_df_pa = pd.DataFrame()
else:
    prev_week_pa = latest_week - 1
    prev_week_df_pa = pa_df[(pa_df['ISO_Year'] == latest_iso_year) & (pa_df['Week'] == prev_week_pa)]

prev_weekly_avg_pa = pd.to_numeric(prev_week_df_pa['PA'], errors='coerce').mean()

# Calculate percentage change (higher is better, so positive change is good)
if prev_weekly_avg_pa > 0 and not pd.isna(prev_weekly_avg_pa):
    weekly_pa_gain = ((weekly_avg_pa - prev_weekly_avg_pa) / prev_weekly_avg_pa) * 100
else:
    weekly_pa_gain = 0




# ----------------------------
# Layout Setup
# ----------------------------
matches = db_filtered.loc[db_filtered["IHS Site ID"] == final_site_id, "tenant_and_id"].dropna().tolist()
tenant_str = " - ".join(matches) if matches else "-"

st.subheader(f"{final_site_id} - Tenants ({tenant_str})")

try:
    rto_name = df.loc[df["IHS Site ID"] == final_site_id, "RTO Name"].iloc[0]
    st.write(f"RTO ({df.loc[df['IHS Site ID'] == final_site_id, 'RTO Name'].iloc[0]})  \
         \t FSE ({df.loc[df['IHS Site ID'] == final_site_id, 'EFS Name'].iloc[0]})")
    
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    
    # Metric Cards
    # Metric Cards
    with col1:
        with st.container(border=True):
            st.metric(
                label="Outage Count", 
                value=human_format(sum(df["Outage Count"])), 
                delta=f"{overall_outage_gain:.2f}%" if overall_outage_gain != 0 else "Average",
                delta_color="inverse"  # Red for positive (bad), green for negative (good)
            )
        
    with col2:
        with st.container(border=True):
            week_count = sum(df[df['Week'] == max_week]["Outage Count"])
            if is_week_complete(df) == False:
                st.metric(
                    label=f"⚠️ Week {max_week} Outage Count", 
                    value=human_format(week_count), 
                    delta=f"{weekly_outage_gain:.2f}%",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    label=f"Week {max_week} Outage Count", 
                    value=human_format(week_count), 
                    delta=f"{weekly_outage_gain:.2f}%",
                    delta_color="inverse"
                )

    with col3:
        with st.container(border=True):
            st.metric(
                label=f"{calendar.month_name[max_month]} Outage Count",
                value=human_format(current_month_count),
                delta=f"{monthly_outage_gain:.2f}%",
                delta_color="inverse"
            )

    with col4:
        with st.container(border=True):
            st.metric(
                label=f"{calendar.month_name[max_month]} PA", 
                value=f"{monthly_avg_pa:.2f}%" if not pd.isna(monthly_avg_pa) else "N/A", 
                delta=f"{monthly_pa_gain:.2f}%",
                delta_color="normal"  # Green for positive (good), red for negative (bad)
            )
                
    with col5:
        with st.container(border=True):
            st.metric(
                label=f"Week {latest_week} PA", 
                value=f"{weekly_avg_pa:.2f}%" if not pd.isna(weekly_avg_pa) else "N/A", 
                delta=f"{weekly_pa_gain:.1f}%",
                delta_color="normal"
            )
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        weekly_counts = df.groupby(['Year', 'Week']).size().reset_index(name='Outage Count')
        weekly_counts['Week_Label'] = (
            weekly_counts['Year'].astype(str) + '-W' + weekly_counts['Week'].astype(str).str.zfill(2)
        )
        weekly_counts = weekly_counts.sort_values(['Year', 'Week'])
        
        bars = alt.Chart(weekly_counts).mark_bar().encode(
            x=alt.X('Week_Label:O', title='Week'),
            y=alt.Y('Outage Count:Q'),
            tooltip=['Year', 'Week', 'Outage Count']
        )
        
        text = alt.Chart(weekly_counts).mark_text(
            align='center',
            baseline='middle',
            dy=10,
            color='black',
            fontSize=12,
        ).encode(
            x='Week_Label:O',
            y='Outage Count:Q',
            text=alt.Text('Outage Count:Q')
        )
        
        chart = (bars + text).properties(
            title=f"Weekly Outage for {final_site_id}",
            width=750,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
    
    with chart_col2:
        pa_df_chart = pa_df.copy()
        pa_df_chart.loc[:, 'Datetime'] = pd.to_datetime(pa_df_chart['Date'])
        pa_df_chart.loc[:, 'Year'] = pa_df_chart['Datetime'].dt.isocalendar().year
        pa_df_chart.loc[:, 'Week'] = pa_df_chart['Datetime'].dt.isocalendar().week
        pa_df_chart.loc[:, 'PA'] = pd.to_numeric(pa_df_chart['PA'], errors='coerce')
        
        weekly_pa = pa_df_chart.groupby(['Year', 'Week'])['PA'].mean().reset_index()
        weekly_pa['Week_Label'] = weekly_pa['Year'].astype(str) + '-W' + weekly_pa['Week'].astype(str).str.zfill(2)
        weekly_pa = weekly_pa.sort_values(['Year', 'Week'])
        
        min_pa = weekly_pa['PA'].min()
        top_y_label = 99.9
        padding = 0.1
        
        chart = alt.Chart(weekly_pa).mark_line(point=True).encode(
            x=alt.X('Week_Label:O', title='Week'),
            y=alt.Y('PA:Q', title='Average PA',
                    scale=alt.Scale(domain=[min_pa - padding, top_y_label + padding])),
            tooltip=['Year', 'Week', 'PA']
        ).properties(
            title="Average Weekly PA Across Years",
            width=750,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)

     # Convert date format from timestamp to dd/mm/yy
    # Convert date format from timestamp to dd/mm/yy
    df_display = df.copy()
    pa_df_display = pa_df.copy()
    df_display.loc[:, 'Date'] = pd.to_datetime(df_display['Date']).dt.strftime('%Y-%m-%d')
    pa_df_display.loc[:, 'Date'] = pd.to_datetime(pa_df_display['Date']).dt.strftime('%d-%B-%Y')

    st.dataframe(df_display.sort_values(by=["Date", "Duration"], ascending=[False, False]))
    st.dataframe(pa_df_display[pa_df_display["PA"] != 100])
    
    # Download buttons
    st.subheader("Download CSV Files")
    col1, col2 = st.columns(2)
    


    
    df_csv = df.to_csv(index=False)
    pa_df_csv = pa_df.to_csv(index=False)
    
    with col1:
        st.download_button(
            label="Download Outage DF",
            data=df_csv,
            file_name="outage_data.csv",
            mime="text/csv",
            icon="📥",
        )
    
    with col2:
        st.download_button(
            label="Download PA DF",
            data=pa_df_csv,
            file_name="pa_data.csv",
            mime="text/csv",
            icon="📥",
        )

except IndexError:
    st.warning(f"Site ID '{final_site_id}' not found in DataFrame.")
    pa_df = pa_df[pa_df["IHS Site ID"] == final_site_id]