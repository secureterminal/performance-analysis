"""
Optimized Performance Dashboard Homepage
- Cached computations
- Vectorized operations
- Lazy loading
- Minimal recomputation
"""

import streamlit as st
import pandas as pd
import altair as alt
import calendar
from datetime import timedelta

import calcs
from helper_functions import human_format, get_valid_date_range

# ============================================
# PAGE CONFIG - MUST BE FIRST
# ============================================
st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# OPTIMIZED CSS - Minified
# ============================================
COMMON_CSS = """
<style>
[data-testid="stSidebar"]{display:block!important}
.stMetric{font-size:0.9rem}
.stMetric label{font-weight:600}
</style>
"""

MTN_BORDER = """<style>.stVerticalBlock.st-emotion-cache-1gz5zxc.e196pkbe2{border:2px solid #FDCC00;padding:10px;border-radius:8px}</style>"""
AIRTEL_BORDER = """<style>.stVerticalBlock.st-emotion-cache-1gz5zxc.e196pkbe2{border:2px solid red;padding:10px;border-radius:8px}</style>"""

st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ============================================
# CONSTANTS
# ============================================
ZONE = "South"
CUSTOMERS = ["MTN NG", "Airtel NG"]
PASSWORD_HASH = "@cwLwNA945nNShp@cwLwNA945nNShp"

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
def init_session_state():
    """Initialize all session state variables once"""
    defaults = {
        "logged_in": True,  # Set to False for production
        "file_uploaded": False,
        "file": None,
        "page": "home",
        "df_init": None,
        "pa_init": None,
        "db": None,
        "db_full": None,
        "filters_applied": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================
# LOGIN HANDLER
# ============================================
if not st.session_state.logged_in:
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", type="primary")
        
        if submit:
            if username == "admin" and password == PASSWORD_HASH:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    st.stop()

# ============================================
# CACHED DATA LOADER
# ============================================
@st.cache_data(show_spinner=False)
def load_uploaded_file(file_bytes, file_name):
    """Cache file loading by content hash"""
    import io
    file_obj = io.BytesIO(file_bytes)
    # file_obj.name = file_name
    
    ext = file_name.split(".")[-1].lower()
    if ext == "xlsx":
        return pd.read_excel(file_obj, engine="openpyxl")
    elif ext == "csv":
        return pd.read_csv(file_obj)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

@st.cache_data(show_spinner=False)
def process_sheets(file_bytes, file_name):
    """Cache expensive sheet processing"""
    import tempfile
    import os

    # Write bytes to a real temporary file
    suffix = os.path.splitext(file_name)[1]  # .xlsx or .csv
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    try:
        return calcs.get_sheets(tmp_path)
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass

# ============================================
# FILE UPLOAD SECTION
# ============================================
if not st.session_state.file_uploaded:
    st.subheader("📁 Upload Data File")
    
    uploaded_file = st.file_uploader(
        "Choose your data file",
        type=["csv", "xlsx"],
        key="file_uploader"
    )
    
    if uploaded_file:
        # Store file bytes for caching
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        
        with st.spinner("⏳ Processing data..."):
            # Load with caching
            data = load_uploaded_file(file_bytes, file_name)
            st.session_state.df_sheets = data
        
        st.success("✅ File loaded successfully!")
        
        # Show preview
        with st.expander("📊 Data Preview", expanded=False):
            st.dataframe(data.head(10), use_container_width=True)
        
        if st.button("Continue to Dashboard", type="primary", use_container_width=True):
            st.session_state.file_uploaded = True
            st.session_state.file_bytes = file_bytes
            st.session_state.file_name = file_name
            st.rerun()
    
    st.stop()

# ============================================
# LOAD & CACHE PROCESSED DATA
# ============================================
if st.session_state.df_init is None:
    with st.spinner("🔄 Initializing dashboard..."):
        df1, pa_df1, db1, db_full1 = process_sheets(
            st.session_state.file_bytes,
            st.session_state.file_name
        )
        st.session_state.df_init = df1
        st.session_state.pa_init = pa_df1
        st.session_state.db = db1
        st.session_state.db_full = db_full1

# Get cached data
df_base = st.session_state.df_init
pa_base = st.session_state.pa_init
db = st.session_state.db

# ============================================
# OPTIMIZED FILTERING FUNCTIONS
# ============================================
@st.cache_data(show_spinner=False)
def apply_date_filter(df, start_date, end_date):
    """Vectorized date filtering"""
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    mask = (df["Date"] >= start_dt) & (df["Date"] <= end_dt)
    return df[mask].copy()

@st.cache_data(show_spinner=False)
def apply_string_filter(df, column, value):
    """Optimized string filtering"""
    if not value or value.startswith("Select"):
        return df
    return df[df[column].str.contains(value, case=False, na=False)].copy()

@st.cache_data(show_spinner=False)
def merge_pa_with_db(pa_df, db):
    """Cache the merge operation"""
    return pd.merge(pa_df, db, on="IHS Site ID", how="left")

# ============================================
# SIDEBAR FILTERS
# ============================================
st.sidebar.header("🔍 Filters")

# Merge PA with DB once
pa_merged = merge_pa_with_db(pa_base, db)

# Date filter
try:
    min_date, max_date = get_valid_date_range(pa_merged, "Date")
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date
        
except ValueError as e:
    st.error(str(e))
    st.stop()

# Apply date filter to both dataframes
df = apply_date_filter(df_base, start_date, end_date)
pa_df = apply_date_filter(pa_merged, start_date, end_date)

# Zone filter (vectorized)
df = df[df["Zone"] == ZONE].copy()
pa_df = pa_df[pa_df["Zone"] == ZONE].copy()

# Customer filter
customer = st.sidebar.selectbox("Customer", ["Select Customer"] + CUSTOMERS)

if customer != "Select Customer":
    df = apply_string_filter(df, "Tenants On Site", customer)
    pa_df = apply_string_filter(pa_df, "Tenants On Site", customer)
    
    # Apply branding
    if customer == "MTN NG":
        st.markdown(MTN_BORDER, unsafe_allow_html=True)
    elif customer == "Airtel NG":
        st.markdown(AIRTEL_BORDER, unsafe_allow_html=True)

# Get unique values AFTER customer filter (faster)
regions = df["Region"].dropna().unique().tolist()
states = df["State"].dropna().unique().tolist()
rtos = df["RTO Name"].dropna().unique().tolist()
fses = df["EFS Name"].dropna().unique().tolist()
sbcs = df["SBC"].dropna().unique().tolist()

# Additional filters
region = st.sidebar.selectbox("Region", ["Select Region"] + sorted(regions))
if region != "Select Region":
    df = df[df["Region"] == region]
    pa_df = pa_df[pa_df["Region"] == region]

state = st.sidebar.selectbox("State", ["Select State"] + sorted(states))
if state != "Select State":
    df = df[df["State"] == state]
    pa_df = pa_df[pa_df["State"] == state]

rto = st.sidebar.selectbox("RTO", ["Select RTO"] + sorted(rtos))
if rto != "Select RTO":
    df = df[df["RTO Name"] == rto]
    pa_df = pa_df[pa_df["RTO Name"] == rto]

fse = st.sidebar.selectbox("FSE", ["Select FSE"] + sorted(fses))
if fse != "Select FSE":
    df = df[df["EFS Name"] == fse]
    pa_df = pa_df[pa_df["EFS Name"] == fse]

sbc = st.sidebar.selectbox("SBC", ["Select SBC"] + sorted(sbcs))
if sbc != "Select SBC":
    df = df[df["SBC"] == sbc]
    pa_df = pa_df[pa_df["SBC"] == sbc]

# ============================================
# OPTIMIZED METRIC CALCULATIONS
# ============================================
@st.cache_data(show_spinner=False)
def calculate_metrics(df, pa_df):
    """Batch calculate all metrics at once"""
    metrics = {}
    
    # Current period metrics
    max_year = df['Year'].max()
    max_month = df["Date"].max().month
    latest_year_df = df[df['Year'] == max_year]
    max_week = latest_year_df['Week'].max()
    
    # Outage counts
    metrics['total_outages'] = df["Outage Count"].sum()
    metrics['avg_per_site'] = df.groupby("IHS Site ID")["Outage Count"].sum().mean()
    metrics['current_week'] = df[df['Week'] == max_week]["Outage Count"].sum()
    metrics['current_month'] = df[df['Month'] == calendar.month_name[max_month]]["Outage Count"].sum()
    
    # Previous period comparisons
    if max_week == 1:
        prev_year = max_year - 1
        prev_week_df = df[df['Year'] == prev_year]
        if not prev_week_df.empty:
            prev_week = prev_week_df['Week'].max()
            metrics['prev_week'] = df[(df['Year'] == prev_year) & (df['Week'] == prev_week)]["Outage Count"].sum()
        else:
            metrics['prev_week'] = 0
    else:
        metrics['prev_week'] = df[(df['Year'] == max_year) & (df['Week'] == max_week - 1)]["Outage Count"].sum()
    
    if max_month == 1:
        metrics['prev_month'] = df[(df['Year'] == max_year - 1) & (df['Month'] == calendar.month_name[12])]["Outage Count"].sum()
    else:
        metrics['prev_month'] = df[(df['Year'] == max_year) & (df['Month'] == calendar.month_name[max_month - 1])]["Outage Count"].sum()
    
    # PA calculations
    pa_calc = pa_df.copy()
    pa_calc['Datetime'] = pd.to_datetime(pa_calc['Date'], errors='coerce')
    pa_calc['Year'] = pa_calc['Datetime'].dt.year
    pa_calc['Month'] = pa_calc['Datetime'].dt.month
    pa_calc['Week'] = pa_calc['Datetime'].dt.isocalendar().week
    pa_calc['ISO_Year'] = pa_calc['Datetime'].dt.isocalendar().year
    pa_calc['PA'] = pd.to_numeric(pa_calc['PA'], errors='coerce')
    
    latest_year = pa_calc['Year'].max()
    latest_month = pa_calc[pa_calc['Year'] == latest_year]['Month'].max()
    latest_iso_year = pa_calc['ISO_Year'].max()
    latest_week = pa_calc[pa_calc['ISO_Year'] == latest_iso_year]['Week'].max()
    
    metrics['monthly_pa'] = pa_calc[(pa_calc['Year'] == latest_year) & (pa_calc['Month'] == latest_month)]['PA'].mean()
    metrics['weekly_pa'] = pa_calc[(pa_calc['ISO_Year'] == latest_iso_year) & (pa_calc['Week'] == latest_week)]['PA'].mean()
    
    # Previous PA
    if latest_month == 1:
        metrics['prev_monthly_pa'] = pa_calc[(pa_calc['Year'] == latest_year - 1) & (pa_calc['Month'] == 12)]['PA'].mean()
    else:
        metrics['prev_monthly_pa'] = pa_calc[(pa_calc['Year'] == latest_year) & (pa_calc['Month'] == latest_month - 1)]['PA'].mean()
    
    if latest_week == 1:
        prev_week_pa_df = pa_calc[pa_calc['ISO_Year'] == latest_iso_year - 1]
        if not prev_week_pa_df.empty:
            prev_week_pa = prev_week_pa_df['Week'].max()
            metrics['prev_weekly_pa'] = pa_calc[(pa_calc['ISO_Year'] == latest_iso_year - 1) & (pa_calc['Week'] == prev_week_pa)]['PA'].mean()
        else:
            metrics['prev_weekly_pa'] = 0
    else:
        metrics['prev_weekly_pa'] = pa_calc[(pa_calc['ISO_Year'] == latest_iso_year) & (pa_calc['Week'] == latest_week - 1)]['PA'].mean()
    
    metrics['max_week'] = max_week
    metrics['latest_week'] = latest_week
    metrics['max_month'] = max_month
    
    return metrics

# Calculate all metrics at once
metrics = calculate_metrics(df, pa_df)

# Calculate percentage changes
def calc_change(current, previous):
    if previous > 0:
        return ((current - previous) / previous) * 100
    return 0 if current == 0 else 100

weekly_change = calc_change(metrics['current_week'], metrics['prev_week'])
monthly_change = calc_change(metrics['current_month'], metrics['prev_month'])
monthly_pa_change = calc_change(metrics['monthly_pa'], metrics['prev_monthly_pa']) if not pd.isna(metrics['prev_monthly_pa']) else 0
weekly_pa_change = calc_change(metrics['weekly_pa'], metrics['prev_weekly_pa']) if not pd.isna(metrics['prev_weekly_pa']) else 0

# ============================================
# DASHBOARD HEADER
# ============================================
st.title("📊 Performance Dashboard")

# ============================================
# METRICS DISPLAY
# ============================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Outages",
        human_format(int(metrics['total_outages'])),
        f"{metrics['avg_per_site']:.1f} avg/site",
        delta_color="inverse"
    )

with col2:
    st.metric(
        f"Week {metrics['max_week']}",
        human_format(int(metrics['current_week'])),
        f"{weekly_change:+.1f}%",
        delta_color="inverse"
    )

with col3:
    st.metric(
        calendar.month_name[metrics['max_month']],
        human_format(int(metrics['current_month'])),
        f"{monthly_change:+.1f}%",
        delta_color="inverse"
    )

with col4:
    pa_val = metrics['monthly_pa']
    st.metric(
        f"{calendar.month_name[metrics['max_month']]} PA",
        f"{pa_val:.2f}%" if not pd.isna(pa_val) else "N/A",
        f"{monthly_pa_change:+.1f}%",
        delta_color="normal"
    )

with col5:
    pa_val = metrics['weekly_pa']
    st.metric(
        f"Week {metrics['latest_week']} PA",
        f"{pa_val:.2f}%" if not pd.isna(pa_val) else "N/A",
        f"{weekly_pa_change:+.1f}%",
        delta_color="normal"
    )

# ============================================
# OPTIMIZED CHARTS
# ============================================
@st.cache_data(show_spinner=False)
def create_weekly_outage_chart(df):
    """Create weekly outage chart with caching"""
    weekly = df.groupby(['Year', 'Week']).size().reset_index(name='Count')
    weekly['Label'] = weekly['Year'].astype(str) + '-W' + weekly['Week'].astype(str).str.zfill(2)
    weekly = weekly.sort_values(['Year', 'Week'])
    
    chart = alt.Chart(weekly).mark_bar().encode(
        x=alt.X('Label:O', title='Week', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Count:Q', title='Outage Count'),
        tooltip=['Year:N', 'Week:N', 'Count:Q']
    ).properties(
        title="Weekly Outage Trend",
        height=300
    )
    
    return chart

@st.cache_data(show_spinner=False)
def create_weekly_pa_chart(pa_df):
    """Create weekly PA chart with caching"""
    pa_calc = pa_df.copy()
    pa_calc['Datetime'] = pd.to_datetime(pa_calc['Date'])
    pa_calc['Year'] = pa_calc['Datetime'].dt.isocalendar().year
    pa_calc['Week'] = pa_calc['Datetime'].dt.isocalendar().week
    pa_calc['PA'] = pd.to_numeric(pa_calc['PA'], errors='coerce')
    
    weekly = pa_calc.groupby(['Year', 'Week'])['PA'].mean().reset_index()
    weekly['Label'] = weekly['Year'].astype(str) + '-W' + weekly['Week'].astype(str).str.zfill(2)
    weekly = weekly.sort_values(['Year', 'Week'])
    
    chart = alt.Chart(weekly).mark_line(point=True).encode(
        x=alt.X('Label:O', title='Week', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('PA:Q', title='PA %', scale=alt.Scale(domain=[weekly['PA'].min() - 0.5, 100])),
        tooltip=['Year:N', 'Week:N', alt.Tooltip('PA:Q', format='.2f')]
    ).properties(
        title="Weekly PA Trend",
        height=300
    )
    
    return chart

st.subheader("📈 Trends")

col1, col2 = st.columns(2)

with col1:
    chart = create_weekly_outage_chart(df)
    st.altair_chart(chart, use_container_width=True)

with col2:
    chart = create_weekly_pa_chart(pa_df)
    st.altair_chart(chart, use_container_width=True)

# ============================================
# DOWNLOAD SECTION
# ============================================
st.divider()

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.download_button(
        "📥 Download Outage Data",
        df.to_csv(index=False).encode('utf-8'),
        "outage_data.csv",
        "text/csv",
        use_container_width=True
    )

with col2:
    st.download_button(
        "📥 Download PA Data",
        pa_df.to_csv(index=False).encode('utf-8'),
        "pa_data.csv",
        "text/csv",
        use_container_width=True
    )