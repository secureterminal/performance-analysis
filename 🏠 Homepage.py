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
from helper_functions import human_format, apply_filters



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
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
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
    st.set_page_config(page_title="Performance Dashboard", page_icon="📊", layout="wide")
    st.title("📊 Performance Dashboard")

    # Block unauthenticated access
    if not st.session_state.get("logged_in", False):
        st.warning("🔒 Please log in to view this page.")
        st.stop()

    st.title("Dashboard Home")  # Main page title (if needed)

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
            df1, pa_df1, db1 = calcs.get_sheets(st.session_state.file)
            st.session_state["df_init"] = df1
            st.session_state["pa_init"] = pa_df1
            st.session_state["db"] = db1
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
        st.sidebar.header("Filters")

        # Ensure we have valid dates before creating the date input
        pa_df["Date"] = pa_df["Date"].cat.as_ordered()

        min_date = pa_df["Date"].min()
        max_date = pa_df["Date"].max()

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

        # ✅ Filter between start and end dates

        pa_df = pa_df[(pa_df["Date"] >= start_date) & (pa_df["Date"] <= end_date)]
        df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        # pa_df = pd.merge(pa_df, db, on="IHS Site ID", how="left")

        # Zone Filter
        df = df[df["Zone"] == zone]
        pa_df = pa_df[pa_df["Zone"] == zone]

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
        # Metric Cards (Gains/Losses)
        # ----------------------------
        gains = [5,2]
        with col1:
            with st.container(border=True):
                st.metric(label="Outage Count", value=human_format(len(df)), delta=f"{gains[0]:,}")
            

        # ----------------------------
        # Weekly
        # ----------------------------
        with col2:
            percent_change = 0
            with st.container(border=True):
                week_count = len(df[df['Week'] == max_week])
                # if max_week == 1:
                #     prev_week_count = 0
                #     percent_change = 100
                # else:
                #     prev_week_count = len(df[df['Week'] == (max_week-1)])
                #     percent_change = ((prev_week_count - week_count)/prev_week_count)*100
                if is_week_complete(df) == False:
                    st.metric(label=f"⚠️ Week {max_week} Outage Count", value=human_format(week_count), delta=f"{round(percent_change, 2)}%")
                else:
                    st.metric(label=f"Week {max_week} Outage Count", value=human_format(week_count), delta=f"{gains[1]:,}")


        # ----------------------------
        # Monthly
        # ----------------------------
        with col3:
            percent_change = 0
            with st.container(border=True):
                month_count = len(df[df['Month'] == calendar.month_name[max_month]])
                if max_month == 1:
                    prev_month_count = 0
                else:
                    prev_month_count = len(df[df['Month'] == calendar.month_name[(max_month - 1)]])

                # Handle division by zero
                # if prev_month_count > 0:
                #     percent_change = ((month_count - prev_month_count) / prev_month_count) * 100
                # else:
                #     percent_change = 0

                st.metric(
                    label=f"{calendar.month_name[max_month]} Outage Count",
                    value=human_format(month_count),
                    delta=f"{round(percent_change, 2)}%"
                )

        with col4:
            with st.container(border=True):
                pa_df['Datetime'] = pd.to_datetime(pa_df['Date'], errors='coerce')

                # Extract Year and Month
                pa_df['Year'] = pa_df['Datetime'].dt.year
                pa_df['Month'] = pa_df['Datetime'].dt.month

                # Get most recent year and month
                latest_year = pa_df['Year'].max()
                latest_month = pa_df[pa_df['Year'] == latest_year]['Month'].max()

                # Filter for that month
                latest_month_df = pa_df[(pa_df['Year'] == latest_year) & (pa_df['Month'] == latest_month)]

                # Compute average PA
                monthly_avg_pa = pd.to_numeric(latest_month_df['PA'], errors='coerce').mean().round(2)

                st.metric(label=f"{calendar.month_name[max_month]} PA", value=monthly_avg_pa, delta=f"{gains[0]:,}")
            

        with col5:
            with st.container(border=True):
                # Extract ISO Year and Week
                pa_df['Week'] = pa_df['Datetime'].dt.isocalendar().week
                pa_df['ISO_Year'] = pa_df['Datetime'].dt.isocalendar().year

                # Get most recent ISO year and week
                latest_iso_year = pa_df['ISO_Year'].max()
                latest_week = pa_df[pa_df['ISO_Year'] == latest_iso_year]['Week'].max()

                # Filter for that week
                latest_week_df = pa_df[(pa_df['ISO_Year'] == latest_iso_year) & (pa_df['Week'] == latest_week)]

                # Compute average PA
                weekly_avg_pa = pd.to_numeric(latest_week_df['PA'], errors='coerce').mean().round(2)

                st.metric(label=f"Week {latest_week} PA", value=weekly_avg_pa, delta=f"{gains[0]:,}")
            

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

        
        






        