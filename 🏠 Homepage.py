import streamlit as st
import random
import numpy as np
import pandas as pd
import json
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import datetime
import time
import calendar

import calcs
from helper_functions import human_format, apply_filters, get_valid_date_range


# if st.session_state.file_uploaded:
#     df1 = st.session_state["df_init"]
#     pa_df1 = st.session_state["pa_init"]
#     db1 = st.session_state["db"]
#     db_full1 = st.session_state["db_full"]
    
#     df = df1.copy()
#     db = db1.copy()
#     pa_df = pa_df1.copy()
    
#     # DEBUG: Check the data
#     st.write("### DEBUG INFO")
#     st.write("PA DataFrame shape:", pa_df.shape)
#     st.write("PA Date column dtype:", pa_df["Date"].dtype)
#     st.write("PA Date sample values:")
#     st.write(pa_df["Date"].head(20))
#     st.write("Number of NaT values:", pa_df["Date"].isna().sum())
#     st.write("Number of valid dates:", pa_df["Date"].notna().sum())
    
#     st.write("\nDF DataFrame shape:", df.shape)
#     st.write("DF Date column dtype:", df["Date"].dtype)
#     st.write("DF Date sample values:")
#     st.write(df["Date"].head(20))

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
            display: block;}
    </style>
"""

hide_sidebar = """
    <style>
        .stSidebar .st-emotion-cache-1m5fwvu .e6f82ta0 {
            display: none;}
    </style>
"""

zone = "South"
CUSTOMERS = ["MTN NG", "Airtel NG"]


# ---- File upload Logic ----
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False

if "file" not in st.session_state:
    st.session_state.file = False

# ---- Login Logic ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"

# Initialize session variable
if "login_messages" in st.session_state:
    st.warning(st.session_state.login_messages)
    st.session_state.login_messages = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown(hide_sidebar, unsafe_allow_html=True)
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.strip() == "admin" and password.strip() == "@cwLwNA945nNShp@cwLwNA945nNShp":
            st.session_state.logged_in = True
            st.success("Login successful! Loading dashboard...")
            st.rerun()
        else:
            st.error("Wrong credentials")

else:
    st.markdown(show_sidebar, unsafe_allow_html=True)
    st.set_page_config(page_title="Performance Dashboard", page_icon="📊", layout="wide")
    st.subheader("📊 Performance Dashboard")

    # Block unauthenticated access
    if not st.session_state.get("logged_in", False):
        st.warning("🔒 Please log in to view this page.")
        st.stop()

    # st.title("Dashboard Home")  # Main page title (if needed)

    if not st.session_state.file_uploaded:

        @st.cache_data
        def load_large_uploaded_file(file):
            file_extension = file.name.split(".")[-1].lower()
            if file_extension == "json":
                return json.load(file)
            elif file_extension == "xlsx":
                return pd.read_excel(file, engine="openpyxl")
            elif file_extension == "csv":
                return pd.read_csv(file)
            else:
                # get the file extension
                file_extension = uploaded_file.name.split(".")[-1]
                st.write(f"Unsupported file type: {file_extension}")
                st.stop()

        st.write("Upload a large csv for cache demo")

        uploaded_file = st.file_uploader(
            "Choose a large CSV file for caching",
            type=["csv", "xlsx", "json"],
            key="large",
        )
        st.session_state.file = uploaded_file

        if uploaded_file is not None:
            st.session_state.file = uploaded_file
            data = load_large_uploaded_file(uploaded_file)
            st.session_state.df_sheets = data
            st.write(st.session_state.df_sheets.head(10))

            st.info(
                "File uploaded and cached successfully! If Data is OK, kindly proceed to the Dashboard."
            )
            if st.button("Continue to Dashboard"):
                st.session_state.file_uploaded = True
                st.rerun()

    if st.session_state.file_uploaded:  # File has been uploaded
        # ----------------------------
        # Sidebar: Filters
        # ----------------------------
        # Load and store processed data in session_state
        if "df_init" not in st.session_state:
            df1, pa_df1, db1, db_full1 = calcs.get_sheets(st.session_state.file)
            st.session_state["df_init"] = df1
            st.session_state["pa_init"] = pa_df1
            st.session_state["db"] = db1
            st.session_state["db_full"] = db_full1
        else:
            df1 = st.session_state["df_init"]
            pa_df1 = st.session_state["pa_init"]
            db1 = st.session_state["db"]
        # def load_sheets():
        #     df1, pa_df1, db1 = calcs.get_sheets(st.session_state.file)
        #     return df1, pa_df1, db1
        # df1, pa_df1, db1 = load_sheets()

        df = df1.copy()
        db = db1.copy()
        pa_df = pa_df1.copy()

        pa_df = pd.merge(pa_df, db, on="IHS Site ID", how="left")



        max_year = df['Year'].max()
        latest_year_df = df[df['Year'] == max_year]

        max_week = latest_year_df['Week'].max()
        min_week = df["Week"].min()

        # Filter DataFrame for that week
        week_df = df[df['Week'] == max_week]

        # Get min and max dates
        max_wk_min_date = week_df['Date'].min()
        max_wk_max_date = week_df['Date'].max()

        max_month =  max_date = df["Date"].max().month


        def is_week_complete(df_fxn):
            # Ensure date column is datetime
            df_fxn['Date'] = pd.to_datetime(df_fxn['Date'])

            # Get all Mondays to define weeks
            df_fxn['Week Start'] = df_fxn['Date'] - pd.to_timedelta(df_fxn['Date'].dt.weekday, unit='d')

            # Count number of distinct dates in each week
            week_counts = df_fxn.groupby('Week Start')['Date'].nunique().reset_index(name='days_present')

            # Check if all weeks have 7 days
            return week_counts['days_present'].eq(7).all()


        # Sidebar: Date range input
        # Sidebar: Date range input
        st.sidebar.header("Filters")

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

        # Zone Filter
        df = df[df["Zone"] == zone].copy()
        pa_df = pa_df[pa_df["Zone"] == zone].copy()

        # Customer Filter
        customer = st.sidebar.selectbox("Customer", ["Select Customer"] + CUSTOMERS)

        if customer and customer != "Select Customer":
            df = df[df["Tenants On Site"].str.contains(customer, case=False, na=False)]
            pa_df = pa_df[pa_df["Tenants On Site"].str.contains(customer, case=False, na=False)]
            # pa_df = pa_df[pa_df["Tenants On Site"] == customer]

        if customer == "MTN NG":
            st.markdown(mtn_css, unsafe_allow_html=True)
        if customer == "Airtel NG":
            st.markdown(airtel_css, unsafe_allow_html=True)

        # Region Filter
        region = st.sidebar.selectbox("Region", ["Select Region"] + df["Region"].dropna().sort_values().unique().tolist())

        if region and region != "Select Region":
            df = df[df["Region"] == region]
            pa_df = pa_df[pa_df["Region"] == region]

        # State Filter
        state = st.sidebar.selectbox("State", ["Select State"] + df["State"].dropna().sort_values().unique().tolist())

        if state and state != "Select State":
            df = df[df["State"] == state]
            pa_df = pa_df[pa_df["State"] == state]

        # RTO Filter
        rto = st.sidebar.selectbox("RTO", ["Select RTO"] + df["RTO Name"].dropna().sort_values().unique().tolist())

        if rto and rto != "Select RTO":
            df = df[df["RTO Name"] == rto]
            pa_df = pa_df[pa_df["RTO Name"] == rto]

        # FSE Filter
        fse = st.sidebar.selectbox("FSE", ["Select FSE"] + df["EFS Name"].dropna().sort_values().unique().tolist())

        if fse and fse != "Select FSE":
            df = df[df["EFS Name"] == fse]
            pa_df = pa_df[pa_df["EFS Name"] == fse]


        # SBC Filter
        sbc = st.sidebar.selectbox("SBC", ["Select SBC"] + df["SBC"].dropna().sort_values().unique().tolist())

        if sbc and sbc != "Select SBC":
            df = df[df["SBC"] == sbc]
            pa_df = pa_df[pa_df["SBC"] == sbc]


        


        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

        # ----------------------------
        # Calculate Gains/Percentage Changes
        # ----------------------------

        # 1. OVERALL OUTAGE COUNT - No comparison needed for homepage, just show total
        total_outage_count = sum(df["Outage Count"])
        # Get all sites' outage counts
        all_sites_outage_counts = df.groupby("IHS Site ID")["Outage Count"].sum()
        avg_outage_all_sites = all_sites_outage_counts.mean()

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

        # Calculate percentage change (lower is better, so negative change is good)
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
        pa_df_calc = pa_df.copy()
        pa_df_calc['Datetime'] = pd.to_datetime(pa_df_calc['Date'], errors='coerce')
        pa_df_calc['Year'] = pa_df_calc['Datetime'].dt.year
        pa_df_calc['Month'] = pa_df_calc['Datetime'].dt.month

        latest_year = pa_df_calc['Year'].max()
        latest_month = pa_df_calc[pa_df_calc['Year'] == latest_year]['Month'].max()
        latest_month_df = pa_df_calc[(pa_df_calc['Year'] == latest_year) & (pa_df_calc['Month'] == latest_month)]
        monthly_avg_pa = pd.to_numeric(latest_month_df['PA'], errors='coerce').mean().round(2)

        # Handle January - get December of previous year
        if latest_month == 1:
            prev_year_pa = latest_year - 1
            prev_month_pa = 12
            prev_month_df = pa_df_calc[(pa_df_calc['Year'] == prev_year_pa) & (pa_df_calc['Month'] == prev_month_pa)]
        else:
            prev_month_pa = latest_month - 1
            prev_month_df = pa_df_calc[(pa_df_calc['Year'] == latest_year) & (pa_df_calc['Month'] == prev_month_pa)]

        prev_monthly_avg_pa = pd.to_numeric(prev_month_df['PA'], errors='coerce').mean()

        # Calculate percentage change (higher is better, so positive change is good)
        if prev_monthly_avg_pa > 0 and not pd.isna(prev_monthly_avg_pa):
            monthly_pa_gain = ((monthly_avg_pa - prev_monthly_avg_pa) / prev_monthly_avg_pa) * 100
        else:
            monthly_pa_gain = 0

        # 5. WEEKLY PA GAIN (compared to previous week)
        pa_df_calc['Week'] = pa_df_calc['Datetime'].dt.isocalendar().week
        pa_df_calc['ISO_Year'] = pa_df_calc['Datetime'].dt.isocalendar().year

        latest_iso_year = pa_df_calc['ISO_Year'].max()
        latest_week = pa_df_calc[pa_df_calc['ISO_Year'] == latest_iso_year]['Week'].max()
        latest_week_df = pa_df_calc[(pa_df_calc['ISO_Year'] == latest_iso_year) & (pa_df_calc['Week'] == latest_week)]
        weekly_avg_pa = pd.to_numeric(latest_week_df['PA'], errors='coerce').mean().round(2)

        # Handle week 1 - get last week of previous year
        if latest_week == 1:
            prev_iso_year = latest_iso_year - 1
            prev_week_pa_df = pa_df_calc[pa_df_calc['ISO_Year'] == prev_iso_year]
            if not prev_week_pa_df.empty:
                prev_week_pa = prev_week_pa_df['Week'].max()
                prev_week_df_pa = pa_df_calc[(pa_df_calc['ISO_Year'] == prev_iso_year) & (pa_df_calc['Week'] == prev_week_pa)]
            else:
                prev_week_df_pa = pd.DataFrame()
        else:
            prev_week_pa = latest_week - 1
            prev_week_df_pa = pa_df_calc[(pa_df_calc['ISO_Year'] == latest_iso_year) & (pa_df_calc['Week'] == prev_week_pa)]

        prev_weekly_avg_pa = pd.to_numeric(prev_week_df_pa['PA'], errors='coerce').mean()

        # Calculate percentage change (higher is better, so positive change is good)
        if prev_weekly_avg_pa > 0 and not pd.isna(prev_weekly_avg_pa):
            weekly_pa_gain = ((weekly_avg_pa - prev_weekly_avg_pa) / prev_weekly_avg_pa) * 100
        else:
            weekly_pa_gain = 0

        # ----------------------------
        # Metric Cards with Calculated Gains
        # ----------------------------
        with col1:
            with st.container(border=True):
                st.metric(
                    label="Outage Count", 
                    value=human_format(total_outage_count), 
                    delta=f"{avg_outage_all_sites:.2f}%",
                    delta_color="inverse" if avg_outage_all_sites > 2 else "normal"  # Red for positive (bad), green for negative (good)
                )
            

        # ----------------------------
        # Weekly
        # ----------------------------
        with col2:
            with st.container(border=True):
                week_count = sum(df[df['Week'] == max_week]["Outage Count"])
                if is_week_complete(df) == False:
                    st.metric(
                        label=f"⚠️ Week {max_week} Outage Count", 
                        value=human_format(week_count), 
                        delta=f"{weekly_outage_gain:.2f}%",
                        delta_color="inverse"  # Red for positive (bad), green for negative (good)
                    )
                else:
                    st.metric(
                        label=f"Week {max_week} Outage Count", 
                        value=human_format(week_count), 
                        delta=f"{weekly_outage_gain:.2f}%",
                        delta_color="inverse"
                    )


        # ----------------------------
        # Monthly
        # ----------------------------
        with col3:
            with st.container(border=True):
                st.metric(
                    label=f"{calendar.month_name[max_month]} Outage Count",
                    value=human_format(current_month_count),
                    delta=f"{monthly_outage_gain:.2f}%",
                    delta_color="inverse"  # Red for positive (bad), green for negative (good)
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
                    delta=f"{weekly_pa_gain:.2f}%",
                    delta_color="normal"  # Green for positive (good), red for negative (bad)
                )
            

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Step 1: Group by Year and Week to get weekly outage counts
            weekly_counts = df.groupby(['Year', 'Week']).size().reset_index(name='Outage Count')

            # Step 2: Create a combined label to show in chart, e.g. "2024-W52"
            weekly_counts['Week_Label'] = (
                weekly_counts['Year'].astype(str) + '-W' + weekly_counts['Week'].astype(str).str.zfill(2)
            )

            # Step 3: Sort by Year then Week
            weekly_counts = weekly_counts.sort_values(['Year', 'Week'])

            # Base bar chart
            bars = alt.Chart(weekly_counts).mark_bar().encode(
                x=alt.X('Week_Label:O', title='Week'),
                y=alt.Y('Outage Count:Q'),
                tooltip=['Year', 'Week', 'Outage Count']
            )

            # Text labels inside each bar
            text = alt.Chart(weekly_counts).mark_text(
                align='center',
                baseline='middle',
                dy=10,  # move inside the bar
                color='black',  # text color for contrast
                fontSize=12,
            ).encode(
                x='Week_Label:O',
                y='Outage Count:Q',
                text=alt.Text('Outage Count:Q')
            )

            # Combine both layers
            chart = (bars + text).properties(
                title="Weekly Outage Count Across Years",
                width=750,
                height=400
            )

            st.altair_chart(chart, use_container_width=True)



        with chart_col2:
            # st.subheader("Total Orders")
            # orders_df = pd.DataFrame({"Month": months, "Orders": order_values})
            # orders_df = orders_df.set_index("Month")
            # st.bar_chart(orders_df)

            # Average Weekly PA
            # Ensure 'Date' column is in datetime format
            pa_df['Datetime'] = pd.to_datetime(pa_df['Date'])

            # Step 1: Create 'Year' and 'Week' columns
            pa_df['Year'] = pa_df['Datetime'].dt.isocalendar().year
            pa_df['Week'] = pa_df['Datetime'].dt.isocalendar().week

            # Step 2: Group by Year and Week to calculate average PA
            pa_df['PA'] = pd.to_numeric(pa_df['PA'], errors='coerce')  # Convert to float, non-numeric → NaN

            weekly_pa = pa_df.groupby(['Year', 'Week'])['PA'].mean().reset_index()

            # Step 3: Create a combined label, e.g. "2025-W01"
            weekly_pa['Week_Label'] = weekly_pa['Year'].astype(str) + '-W' + weekly_pa['Week'].astype(str).str.zfill(2)

            # Step 4: Sort the data by Year then Week
            weekly_pa = weekly_pa.sort_values(['Year', 'Week'])

            # Calculate dynamic y-axis range
            min_pa = weekly_pa['PA'].min()
            top_y_label = 99.9
            padding = 0.1  # Adjust this to your preference

            # Step 5: Create Altair chart
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

            # Step 6: Show in Streamlit
            st.altair_chart(chart, use_container_width=True)





        












        

        # ----- Download Updates -----
        # ----- Download Updates -----
        st.subheader("Download CSV Files")
        col1, col2 = st.columns(2)

        # Convert DataFrames to CSV
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


        # # ----- Charts -----
        # months = [
        #     "Jan",
        #     "Feb",
        #     "Mar",
        #     "Apr",
        #     "May",
        #     "Jun",
        #     "Jul",
        #     "Aug",
        #     "Sep",
        #     "Oct",
        #     "Nov",
        #     "Dec",
        # ]
        # percentage_values = np.random.randint(50, 100, size=12)
        # order_values = np.random.randint(200, 500, size=12)

        # chart_col1, chart_col2 = st.columns(2)
        # with chart_col1:
        #     st.subheader("Percentage")
        #     st.line_chart(percentage_values)
        # with chart_col2:
        #     st.subheader("Total Orders")
        #     orders_df = pd.DataFrame({"Month": months, "Orders": order_values})
        #     orders_df = orders_df.set_index("Month")
        #     st.bar_chart(orders_df)

        

        # # From Site Info

        
        







