import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import re


# ===== AUTHENTICATION CHECK (ADD THIS) =====
if not st.session_state.get("logged_in", False):
    st.error("🔒 Please log in to access this page.")
    st.switch_page("Login.py")

# Hide login from sidebar
hide_login_css = """
    <style>
        [data-testid="stSidebarNav"] li:first-child {
            display: none;
        }
    </style>
"""
st.markdown(hide_login_css, unsafe_allow_html=True)

# Show user info at top with compact design
if st.session_state.get("user_info"):
    user = st.session_state.user_info
    full_name = user.get('full_name', user.get('username', 'User'))
    first_name = full_name.split()[0] if full_name else 'User'
    role = user.get('role', 'user').capitalize()
    
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 0.6rem 1rem; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 8px; 
                        # margin-bottom: 1.0rem;
                        margin-top: -25.5rem;
                        color: white;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">👤</span>
                    <div>
                        <div style="font-size: 1rem; font-weight: 600; margin: 0; line-height: 1.2;">{first_name}</div>
                        <div style="font-size: 0.75rem; opacity: 0.9; margin: 0; line-height: 1.2;">Role: {role}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
# ===== END AUTHENTICATION =====


st.set_page_config(page_title="Reports", page_icon="📊", layout="wide")



st.title("📊 Reports Management")


# Load session data
df1 = st.session_state["df_init"]
pa_df1 = st.session_state["pa_init"]
db1 = st.session_state["db"]
db_full1 = st.session_state["db_full"]


# Create three columns
col1, col2 = st.columns(2)

# ==========================================
# COLUMN 1: WEEKLY OUTAGE PROCESSOR
# ==========================================
with col1:
    st.subheader("📋 Weekly Outage")
    
    with st.container(border=True):
        st.write("**Upload Files**")
        
        # File uploaders
        outages_file = st.file_uploader(
            "Upload Weekly Outages File",
            type=["xlsx"],
            key="outages_upload",
            help="Upload the weekly outages Excel file"
        )
        
        # Week number input

        current_week = datetime.today().isocalendar()[1]
        previous_week = 52 if current_week == 1 else current_week - 1
        week_number = st.number_input(
            "Week Number",
            min_value=1,
            max_value=53,
            value=previous_week,
            help="Week number for the output file"
        )

        target_hours = st.number_input(
            "Target Hours",
            min_value=1,
            max_value=24,
            value=3,
            help="Target hours threshold for filtering"
        )
        
        # Process button
        if st.button("🔄 Process Outages", use_container_width=True):
            if outages_file is None:
                st.error("⚠️ Please upload the Outages file!")
            else:
                try:
                    with st.spinner("Processing outages..."):
                        # Load Excel files
                        outages_df = pd.read_excel(outages_file, engine="openpyxl")

                        # Change column name for IHS Site Name to IHS Site ID
                        if 'IHS Site Name' in outages_df.columns:
                            outages_df = outages_df.rename(columns={'IHS Site Name': 'IHS Site ID'})

                            # Exclude No Intervention
                            outages_df = outages_df[outages_df['RCA 3'] != "No Intervention"].copy()

                        # Prepare MTN and Airtel DataFrames from db_full
                        mtn_df = db_full1[db_full1["Tenant Name"] == "MTN NG"].copy()
                        airtel_df = db_full1[db_full1["Tenant Name"] == "Airtel NG"].copy()
                        
                        # Rename columns for MTN
                        mtn_df = mtn_df.rename(columns={
                            'Tenant Region': 'MTN Region',
                            'Tenant ID': 'MTN ID'
                        })
                        
                        # Rename columns for Airtel
                        airtel_df = airtel_df.rename(columns={
                            'Tenant Region': 'Airtel Region',
                            'Tenant ID': 'Airtel ID'
                        })
                        
                        # Step 4: Initialize customer columns
                        outages_df['MTN ID'] = ""
                        outages_df['MTN Region'] = ""
                        outages_df['Airtel ID'] = ""
                        outages_df['Airtel Region'] = ""
                        
                        # Step 5: Perform merges
                        outages_df = outages_df.merge(
                            mtn_df[['IHS Site ID', 'MTN ID', 'MTN Region']], 
                            on='IHS Site ID', 
                            how='left', 
                            suffixes=('', '_mtn')
                        )
                        
                        outages_df = outages_df.merge(
                            airtel_df[['IHS Site ID', 'Airtel ID', 'Airtel Region']], 
                            on='IHS Site ID', 
                            how='left', 
                            suffixes=('', '_airtel')
                        )
                        
                        # Handle merged columns
                        if 'MTN ID_mtn' in outages_df.columns:
                            outages_df['MTN ID'] = outages_df['MTN ID_mtn'].fillna(outages_df['MTN ID']).fillna("-")
                            outages_df = outages_df.drop(columns=['MTN ID_mtn'])
                        else:
                            outages_df['MTN ID'] = outages_df['MTN ID'].fillna("-")
                            
                        if 'MTN Region_mtn' in outages_df.columns:
                            outages_df['MTN Region'] = outages_df['MTN Region_mtn'].fillna(outages_df['MTN Region']).fillna("-")
                            outages_df = outages_df.drop(columns=['MTN Region_mtn'])
                        else:
                            outages_df['MTN Region'] = outages_df['MTN Region'].fillna("-")
                        
                        if 'Airtel ID_airtel' in outages_df.columns:
                            outages_df['Airtel ID'] = outages_df['Airtel ID_airtel'].fillna(outages_df['Airtel ID']).fillna("-")
                            outages_df = outages_df.drop(columns=['Airtel ID_airtel'])
                        else:
                            outages_df['Airtel ID'] = outages_df['Airtel ID'].fillna("-")
                            
                        if 'Airtel Region_airtel' in outages_df.columns:
                            outages_df['Airtel Region'] = outages_df['Airtel Region_airtel'].fillna(outages_df['Airtel Region']).fillna("-")
                            outages_df = outages_df.drop(columns=['Airtel Region_airtel'])
                        else:
                            outages_df['Airtel Region'] = outages_df['Airtel Region'].fillna("-")
                        
                        # Rename to AIRTEL
                        outages_df = outages_df.rename(columns={
                            'Airtel ID': 'AIRTEL ID',
                            'Airtel Region': 'AIRTEL Region'
                        })
                        
                        # Step 6: Remove invalid sites
                        if 'Site ID' in outages_df.columns:
                            outages_df = outages_df[outages_df['Site ID'] != "-"]
                        
                        # Step 7: Calculate time boundaries
                        max_year = outages_df['Outage Start Time'].dropna().dt.year.max()
                        start_of_week = datetime.fromisocalendar(max_year, week_number, 1)
                        end_date = datetime.fromisocalendar(max_year, week_number, 7) + timedelta(days=1)

                        st.write(f"First Day of week: {start_of_week}")
                        st.write(f"Last Day of week: {end_date}")
                        
                        # Step 8-12: Handle outage times
                        if 'Outage End Time' in outages_df.columns:
                            outages_df['Outage End Time'] = pd.to_datetime(outages_df['Outage End Time'], errors='coerce')
                            outages_df['Outage End Time'] = outages_df['Outage End Time'].fillna(end_date)
                        
                        if 'Outage Start Time' in outages_df.columns:
                            outages_df['Outage Start Time'] = pd.to_datetime(outages_df['Outage Start Time'], errors='coerce')
                            outages_df = outages_df[outages_df['Outage Start Time'] <= end_date]
                        
                        if 'Outage End Time' in outages_df.columns:
                            outages_df = outages_df[outages_df['Outage End Time'] >= start_of_week]
                        
                        if 'Outage Start Time' in outages_df.columns:
                            mask = (outages_df['Outage Start Time'] < start_of_week)
                            outages_df.loc[mask, 'Outage Start Time'] = start_of_week
                        
                        if 'Outage End Time' in outages_df.columns:
                            outages_df.loc[outages_df['Outage End Time'] > end_date, 'Outage End Time'] = end_date
                        
                        # Step 13: Calculate duration
                        if 'Outage Start Time' in outages_df.columns and 'Outage End Time' in outages_df.columns:
                            outages_df['Outage Duration'] = (
                                outages_df['Outage End Time'] - outages_df['Outage Start Time']
                            )
                        
                        # Step 14: Exclude vendors
                        if 'Maintenance Vendor' in outages_df.columns:
                            excluded_vendors = ["Introspect", "ACUTECH NGA", "Axon"]
                            outages_df = outages_df[~outages_df['Maintenance Vendor'].isin(excluded_vendors)]
                        
                        # Step 15: Sort by duration
                        if 'Outage Duration' in outages_df.columns:
                            outages_df = outages_df.sort_values(by='Outage Duration', ascending=False)
                        
                        # Step 16: Select columns
                        columns_to_select = [
                            'Number', 'Incident State', 'Incident Type', 'Incident Priority',
                            'Site ID', 'MTN ID', 'MTN Region', 'Region / Province',
                            'State/District', 'Impact', 'AIRTEL ID', 'AIRTEL Region',
                            'Short description', 'Created', 'Opened by', 'Alarm Start',
                            'Alarm End', 'Alarm Duration', 'Outage Start Time',
                            'Outage End Time', 'Outage Duration', 'Maintenance Vendor',
                            'Primary Cause', 'RCA 1', 'RCA 2', 'RCA 3',
                            'Affected Tenant / On Site', 'Affected Tenants',
                            'Affected Tenants Count', 'SBC Field Engineer',
                            'SBC Field Engineer 2', 'SBC Field Engineer 3',
                            'SBC OPS Head', 'SBC Regional Manager', 'SBC Supervisor',
                            'IHS Field Engineer', 'IHS RTO', 'IHS Head of Operation',
                            'Site Priority', 'Country', 'Notify', 'Cascaded Site Count',
                            'Resolution Comments', 'Resolution notes'
                        ]
                        
                        existing_columns = [col for col in columns_to_select if col in outages_df.columns]
                        outages_df = outages_df[existing_columns]
                        
                        # ===== RCA MAPPING AND SITE ANALYSIS =====
                        st.info("🔄 Processing RCA mapping...")
                        
                        # Define RCA mapping
                        rca_mapping = {
                            'Power Provided By 3RD Party': '3rd Party',
                            'Access Issue - Environmental Conditions': 'Access issue',
                            'Access - Time Restriction/Pre-Approval': 'Access issue',
                            'Access Issue - Regulatory Concerns': 'Access issue',
                            'DCDG - Actuator': 'Actuator was worked on',
                            'Rectifier Module Overloaded': 'Additional module added',
                            'ACDG - Air Intake': 'Airlock in fuel line',
                            'ATS-AMF Hanged': 'ATS contactor energized',
                            'DCDG - AVR': 'AVR worked on',
                            'ACDG - Injector Pump': 'Bad Injector Pump',
                            'ACDG - Fuel Injection Pump Calibration': 'Bad Injector Pump',
                            'Fuel Line Issue': 'Blocked fuel line',
                            'Water Separator Blockage': 'Blocked water separator',
                            'Faulty Circuit Breaker': 'Breaker was replaced',
                            'BTS Breaker Faulty': 'Breaker was replaced',
                            'BTS Breaker Tripped': 'Breaker was replaced',
                            'Rectifier Battery': 'BUB issue',
                            'Backup Batteries': 'BUB issue',
                            'DCDG - Charging Alternator': 'Charging alternator excited',
                            'DCGG - Charging Alternator': 'Charging alternator excited',
                            'ACDG - Charging Alternator Carbon Brush Faulty': 'Charging alternator excited',
                            'Access Issue - Security Guard Salary': 'CLO access issue',
                            'Access Issue - Community': 'Community access issue',
                            'Generator Battery Theft': 'Crank battery theft',
                            'Panel Distribution Board': 'Breaker was replaced',
                            'DC Cable Stolen': 'DC Cable Stolen',
                            'ACDG - Compression': 'DG Compression',
                            'DCDG - Compression': 'DG Compression',
                            'ACDG - Control Panel': 'DG control panel',
                            'ACDG - Crankshaft': 'DG crankshaft',
                            'DG Distribution Board': 'DG distribution board issue',
                            'ACDG - Emergency Stop Switch': 'DG emergency stop switch worked on',
                            'ACDG - Exhaust': 'DG exhaust fixed',
                            'ACDG - Generator Faulty': 'DG Fault',
                            'ACDG - Unexpected Shutdown': 'DG fault',
                            'DCDG - Fuse': 'DG fuse replaced',
                            'ACDG - Governor': 'DG Governor adjusted',
                            'ACDG - Over Speed': 'DG governor adjusted',
                            'ACDG - Under Frequency': 'DG governor adjusted',
                            'ACDG - Under Voltage': 'DG Governor adjusted',
                            'DCDG - Governor': 'DG governor adjusted',
                            'ACDG - Over Frequency': 'DG governor adjusted',
                            'ACDG - Over Voltage': 'DG governor adjusted',
                            'ACDG - Under Speed': 'DG governor adjusted',
                            'ACDG - High Engine Temp - Coolant Level Issue': 'DG high temperature',
                            'ACDG - Radiator': 'DG high temperature',
                            'ACDG - High Engine Temp - Clogged Radiator': 'DG high temperature',
                            'ACDG - High Engine Temp - Radiator Leakage': 'DG high temperature',
                            'Gen Temp High': 'DG high temperature',
                            'ACDG - Load Unbalanced': 'DG load balancing done',
                            'ACDG - Low Oil Pressure': 'DG low oil pressure',
                            'Site Down - Low Voltage': 'DG low voltage',
                            'ACDG - Oil Leakage': 'DG oil leakage',
                            'ACDG - Overload': 'DG Overload',
                            'ACDG - Push Rod': 'DG push rod',
                            'ACDG - Solenoid Coil': 'DG solenoid worked on',
                            'DG Theft': 'DG Theft',
                            'DCGG - Gen Voltage': 'DG voltage alarm cleared',
                            'Diesel Top-Up': 'Diesel outage',
                            'Diesel Outage': 'Diesel outage',
                            'Diesel Quality': 'Diesel quality',
                            'Diesel Theft': 'Diesel Theft',
                            'ACDG - Fan Belt': 'Fan belt swapped',
                            'DCGG - Fan Belt Issue': 'Fan belt swapped',
                            'Aircon Condenser Fan Motor Faulty': 'Faulty AC',
                            'Aircon Compressor High Temp': 'Faulty AC',
                            'Aircon Switch Faulty': 'Faulty AC',
                            'Armoured Cable': 'Faulty armoured cable',
                            'ATS-AMF Issue': 'Faulty ATS worked on',
                            'ATS Relay Faulty': 'Faulty ATS worked on',
                            'ACDG - AVR': 'Faulty AVR worked on',
                            'DCGG - Avr Output/Settings': 'Faulty AVR worked on',
                            'ACDG - Auxiliary Faulty': 'Faulty AVR worked on',
                            'ACDG - Charging Alternator': 'Charging alternator excited',
                            'ACDG - Interface Module Faulty': 'Faulty DG module worked on',
                            'ACDG - Relay Faulty': 'Relay was replaced',
                            'ACDG - Temperature Sensor Switch': 'Faulty DG thermostat replaced',
                            'ACDG - Emergency Stop': 'Faulty emergency stop switch',
                            'DCGG - Expansion Board Error': 'Faulty expansion board worked on',
                            'ACDG - Fuel Lifting Pump Faulty': 'Faulty fuel pump',
                            'DCDG - Fuel Pump': 'Faulty fuel pump',
                            'ACDG - Fuel Pump': 'Faulty fuel pump',
                            'ACDG - Priming Motor Faulty': 'Faulty hand primer worked on',
                            'ACDG - Kick Starter': 'Faulty kickstarter',
                            'ACDG - Lift Pump': 'Faulty Lift Pump',
                            'ACDG - Load Contactor': 'Faulty load contactor',
                            'ACDG - Oil Seal': 'Faulty oil seal',
                            'ACDG - Oil Pressure Sensor Faulty': 'Faulty oil sensor switch worked on',
                            'ACDG - Oil Sensor Switch': 'Faulty oil sensor switch worked on',
                            'Rectifier Cabinet': 'Faulty rectifier cabinet',
                            'Rectifier Module': 'Faulty rectifier module',
                            'ACDG - Rotor Head': 'Faulty rotor head',
                            'ACDG - Water Pump': 'Faulty water pump',
                            'DCDG - Water Pump': 'Faulty water pump',
                            'DCGG - Faulty/Burnt Breaker': 'Breaker was replaced',
                            'ACDG - Load Breaker': 'Breaker was replaced',
                            'DCDG - Load Breaker': 'Breaker was replaced',
                            'Rectifier - Circuit Breaker': 'Breaker was replaced',
                            'ACDG - Main Breaker Tripped': 'Breaker was replaced',
                            'Circuit Breaker Tripped': 'Breaker was replaced',
                            'AC Breaker Tripped': 'Breaker was replaced',
                            'AC Breaker Faulty': 'Breaker was replaced',
                            'ACDG - Fuel Filter': 'Fuel filter replaced',
                            'DCDG - Fuel Filter': 'Fuel filter replaced',
                            'DCGG - Avr Burnt Fuse/Avr Issue': 'Gen fuse worked on',
                            'DCGG - Control Module': 'GG control module worked on',
                            'DCGG - Gen Current': 'GG current adjusted',
                            'DCGG - Faulty Engine Harness': 'GG faulty harness cable',
                            'DCGG - Start Failure': 'GG start failure alarm',
                            'National Grid - Grid Incomplete Phase': 'Grid incomplete phase',
                            'National Grid - Low Current Supply': 'Grid low current',
                            'National Grid - Grid Outage Issue': 'Grid outage',
                            'DCGG - Gas Flow': 'High pressure regulator worked on',
                            'Hybrid Software': 'Hybrid failure',
                            'Hybrid Module': 'Hybrid failure',
                            'E-Site Comm Failure': 'Hybrid failure',
                            'Access Issue - Land Lord': 'Landlord access issue',
                            'DCGG - Load Cable': 'Load cable was worked on',
                            'DCDG - Logic Board': 'Logic board worked on',
                            'DCGG - Low Oil Pressure': 'Low oil pressure',
                            'DCDG - Low Oil Pressure': 'Low oil pressure',
                            'ACDG - Main Alternator': 'Main Alternator Issue',
                            'ACDG - Oil Pump': 'Oil pump replaced',
                            'Planned Activity - Passive': 'Passive planned activity',
                            'Installation Activity': 'Passive planned activity',
                            'Planned Activity - ACDG Inspection': 'Passive planned activity',
                            'POFC - Grid': 'POFC',
                            'POFC - Gen': 'POFC',
                            'Generator Servicing': 'PPM completed',
                            'ACDG - Radiator Leakage': 'DG high temperature',
                            'Rectifier - Controller Failure': 'Rectifier CSU failed',
                            'Rectifier - Phase Controller': 'Rectifier phase issue',
                            'Rectifier Distribution': 'Rectifier was worked on',
                            'ACDG - 12V Relay Faulty': 'Relay was replaced',
                            'No Intervention': 'SDO',
                            'Access Issue - Security': 'Security access issue',
                            'ACDG - Fip Solenoid Cable Faulty': 'Solenoid cable worked on',
                            'Intrusion - Vandalism/Sabotage': 'Theft',
                            'AC Cable Stolen': 'Theft',
                            'Rectifier Theft': 'Theft',
                            'ACDG - Top Gasket': 'Top gasket replaced',
                            'ACDG - Turbo Charger': 'Turbo charger issue',
                            'National Grid - Unstable Grid Supply Issue': 'Unstable grid',
                            'DCGG - Bus Voltage': 'Voltage fluctuations',
                            'Tank Sealing Issue - Water In The Fuel': 'Water ingress',
                            'ACDG - Generator Battery': 'Weak crank battery',
                            'DG Low Battery': 'Weak crank battery',
                            'DCGG - Crank Battery': 'Weak crank battery',
                            'DCDG - Generator Battery': 'Weak crank battery',
                            'DCGG - Crank Battery Weak/Dead': 'Weak crank battery',
                            'Gas Outage': 'Gas Outage',
                            'DCDG - Injector Pump': 'Bad Injector Pump',
                            'DCDG - Fan Belt': 'Fan belt swapped',
                            'DCDG - Panel Board': 'DG distribution board issue',
                            'DCGG - Faulty Expansion Board': 'Faulty expansion board worked on',
                            'DCGG - Control Panel': 'DG control panel',
                            'Relay': 'Relay was replaced',
                            'DCGG - Throttle Motor': 'GG throttle motor',
                            'DCDG - Radiator': 'DG high temperature',
                            'DCDG - Solenoid Coil': 'DG solenoid worked on',
                            'DCGG - CBC': 'Faulty CBC was replaced',
                            'DCGG - RPM - Gas Flow': 'High pressure regulator worked on',
                            'DCGG - High Rectifier Temp': 'DG high temperature',
                            'DCGG - Engine Temp - Faulty Water Pump': 'Faulty water pump',
                            'DCGG - High Engine Temp - Coolant Level Issue': 'DG high temperature',
                            'National Grid - Circuit Breaker': 'Grid breaker replaced',
                            'DCGG - High Engine Temp - Clogged Radiator': 'DG high temperature'
                        }
                        
                        # Map RCA 3
                        if 'RCA 3' in outages_df.columns:
                            outages_df['Preferred_RCA'] = outages_df['RCA 3'].map(rca_mapping)

                            def clean_spaces(text):
                                if pd.isna(text):
                                    return text
                                # Replace one or more whitespace characters (\s+) with a single space
                                return re.sub(r'\s+', ' ', str(text)).strip()

                            # Apply the cleaning function loop
                            outages_df['Preferred_RCA'] = outages_df['Preferred_RCA'].apply(clean_spaces)

                            # Handle unmapped
                            outages_df['Preferred_RCA'] = outages_df['Preferred_RCA'].fillna('Unmapped')
                            
                            # Handle unmapped
                            missing_rcas = outages_df[outages_df['Preferred_RCA'].isna() & outages_df['RCA 3'].notna()]['RCA 3'].unique()
                            if len(missing_rcas) > 0:
                                st.warning(f"⚠️ {len(missing_rcas)} unmapped RCA3 values. Setting to 'Unmapped'.")
                            outages_df['Preferred_RCA'] = outages_df['Preferred_RCA'].fillna('Unmapped')
                            
                            # Helper function
                            def format_timedelta_hours(td):
                                if pd.isna(td):
                                    return "00:00:00"
                                total_seconds = int(td.total_seconds())
                                hours = total_seconds // 3600
                                minutes = (total_seconds % 3600) // 60
                                seconds = total_seconds % 60
                                return f"{hours:02}:{minutes:02}:{seconds:02}"
                            
                            # Convert duration
                            outages_df['Outage Duration TD'] = pd.to_timedelta(outages_df['Outage Duration'], errors='coerce')
                            
                            # Site analysis
                            site_analysis = []
                            unique_sites = outages_df['Site ID'].unique()
                            
                            for site in unique_sites:
                                site_df = outages_df[outages_df['Site ID'] == site]
                                
                                total_count = len(site_df)
                                total_mttr = site_df['Outage Duration TD'].sum()
                                total_mttr_str = format_timedelta_hours(total_mttr)
                                
                                # ✅ Case-insensitive groupby that preserves original label
                                rca_stats = (
                                    site_df
                                    .groupby(site_df['Preferred_RCA'].str.lower())
                                    .agg(
                                        Preferred_RCA=('Preferred_RCA', 'first'),  # keep original casing
                                        count=('Preferred_RCA', 'count'),
                                        sum_mttr_seconds=('Outage Duration TD', lambda x: x.sum().total_seconds())
                                    )
                                    .reset_index(drop=True)
                                )
                                
                                rca_stats['impact'] = rca_stats['count'] * rca_stats['sum_mttr_seconds']
                                rca_stats = rca_stats.sort_values(by='impact', ascending=False)
                                
                                top_rcas = rca_stats['Preferred_RCA'].head(2).tolist()
                                distinct_rca_count = site_df['Preferred_RCA'].str.lower().nunique()
                                concatenated_rca = " | ".join(top_rcas) if top_rcas else "N/A"
                                
                                site_analysis.append({
                                    'Site ID': site,
                                    'Total count of outages for the site': total_count,
                                    'Total sum of MTTR for the site': total_mttr_str,
                                    'Distinct Preferred RCA Count': distinct_rca_count,
                                    'Concatenated Preferred RCA': concatenated_rca
                                })
                            
                            # Merge back
                            site_df_analysis = pd.DataFrame(site_analysis)
                            outages_df = outages_df.merge(site_df_analysis, on='Site ID', how='left')
                            outages_df = outages_df.drop(columns=['Outage Duration TD'], errors='ignore')
                            
                            st.success("✅ RCA mapping complete. Added 5 columns (Preferred_RCA + 4 analysis columns).")
                        else:
                            st.warning("⚠️ RCA 3 column not found. Skipping RCA analysis.")

                        
                        # Store in session state
                        st.session_state['processed_outages'] = outages_df
                        st.session_state['processed_week_number'] = week_number
                        st.session_state['target_hours'] = target_hours
                        st.session_state['trigger_regional_analysis'] = True
                        
                        st.success(f"✅ Processed {len(outages_df)} outages successfully!")
                        
                        # Display preview
                        st.write("**Preview (First 5 rows):**")
                        st.dataframe(outages_df.head(), use_container_width=True)
                        
                        # Display stats
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Total Outages", len(outages_df))
                        with col_b:
                            if 'Outage Duration' in outages_df.columns:
                                avg_duration = outages_df['Outage Duration'].mean()
                                hours = avg_duration.total_seconds() / 3600
                                st.metric("Avg Duration", f"{hours:.1f}h")
                            else:
                                st.metric("Avg Duration", "N/A")
                        
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Download button
        if 'processed_outages' in st.session_state:
            st.write("---")
            st.write("**Download Processed File**")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state['processed_outages'].to_excel(writer, index=False, sheet_name='Outages')
            output.seek(0)
            
            filename = f"Week {st.session_state['processed_week_number']} Processed.xlsx"
            
            st.download_button(
                label=f"📥 Download {filename}",
                data=output,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


# ==========================================
# COLUMN 2: PLACEHOLDER FOR REPORT 2
# ==========================================
with col2:
    st.subheader("📈 Regional Impact")
    
    with st.container(border=True):
        # Auto-run when Column 1 completes OR manually check
        should_run = st.session_state.get('trigger_regional_analysis', False) or 'processed_outages' in st.session_state
        
        # Check if processed outages exist
        if 'processed_outages' not in st.session_state:
            st.info("⏳ Please process outages in Column 1 first")
        elif should_run:
            try:
                # Clear the trigger
                if 'trigger_regional_analysis' in st.session_state:
                    st.session_state['trigger_regional_analysis'] = False
                
                with st.spinner("Analyzing regional impacts..."):
                    # Load processed data
                    df = st.session_state['processed_outages'].copy()
                    
                    # Filter for MTN regions
                    if 'MTN Region' in df.columns:
                        df = df[df['MTN Region'].isin(['ASB', 'IBD'])]
                        
                        if len(df) == 0:
                            st.warning("⚠️ No data found for ASB or IBD regions")
                        else:
                            # Initialize list to collect all feedback dataframes
                            feedback_dfs = []
                            
                            def process_region(region_df):
                                region_df = region_df.copy()
                                region_feedback_dfs = []
                                
                                # Calculate duration in hours
                                region_df['Outage Duration Hours'] = region_df['Outage Duration'].dt.total_seconds() / 3600
                                
                                # Access Issues
                                access_denial = region_df[
                                    (region_df['Primary Cause'] == 'Access Denial') &
                                    (region_df['Outage Duration Hours'] > target_hours)
                                ]
                                access_issues = ', '.join(access_denial['MTN ID'].dropna().astype(str).unique())
                                if len(access_denial) > 0:
                                    feedback_list_access = access_denial[['MTN ID', 'Site ID', 'MTN Region', 'Outage Duration', 'RCA 1', 'Resolution Comments']]
                                    region_feedback_dfs.append(feedback_list_access)
                                
                                # Theft and Vandalism
                                theft = region_df[
                                    (region_df['Primary Cause'] == 'Site Asset Theft') &
                                    (region_df['Outage Duration Hours'] > target_hours)
                                ]
                                theft_vandalism = ', '.join(theft['MTN ID'].dropna().astype(str).unique())
                                if len(theft) > 0:
                                    feedback_list_theft = theft[['MTN ID', 'Site ID', 'MTN Region', 'Outage Duration', 'RCA 1', 'Resolution Comments']]
                                    region_feedback_dfs.append(feedback_list_theft)
                                
                                # Major DG Faults (using RCA 2)
                                if 'RCA 2' in region_df.columns:
                                    dg_faults = region_df[
                                        region_df['RCA 2'].str.contains('DG', case=False, na=False)
                                    ].sort_values('Outage Duration Hours', ascending=False)
                                    major_dg = ', '.join(dg_faults['MTN ID'].dropna().astype(str).unique()[:5])
                                    if len(dg_faults) > 0:
                                        feedback_list_dg = dg_faults[['MTN ID', 'Site ID', 'MTN Region', 'Outage Duration', 'RCA 1', 'Resolution Comments']].head(5)
                                        region_feedback_dfs.append(feedback_list_dg)
                                else:
                                    major_dg = "N/A"
                                
                                # Diesel Cycle (15% threshold)
                                fuel_outage = region_df[
                                    region_df['Primary Cause'].str.contains('Fuel Outage', case=False, na=False)
                                ]
                                vendor_fuel_counts = fuel_outage['Maintenance Vendor'].value_counts()
                                vendor_total_counts = region_df['Maintenance Vendor'].value_counts()
                                diesel_vendors = [v for v in vendor_total_counts.index
                                                  if (vendor_fuel_counts.get(v, 0)/vendor_total_counts[v] * 100) > 15]
                                
                                return {
                                    'Access Issues': access_issues if access_issues else "None",
                                    'Theft and Vandalism': theft_vandalism if theft_vandalism else "None",
                                    'Major DG Faults': major_dg if major_dg else "None",
                                    'Diesel Cycle': ', '.join(diesel_vendors) if diesel_vendors else "None",
                                    'feedback_dfs': region_feedback_dfs
                                }
                            
                            # Process regions
                            asb_df = df[df['MTN Region'] == 'ASB'].copy()
                            ibd_df = df[df['MTN Region'] == 'IBD'].copy()
                            
                            if len(asb_df) > 0:
                                asb_result = process_region(asb_df)
                                feedback_dfs.extend(asb_result['feedback_dfs'])
                            else:
                                asb_result = {
                                    'Access Issues': 'No data',
                                    'Theft and Vandalism': 'No data',
                                    'Major DG Faults': 'No data',
                                    'Diesel Cycle': 'No data'
                                }
                            
                            if len(ibd_df) > 0:
                                ibd_result = process_region(ibd_df)
                                feedback_dfs.extend(ibd_result['feedback_dfs'])
                            else:
                                ibd_result = {
                                    'Access Issues': 'No data',
                                    'Theft and Vandalism': 'No data',
                                    'Major DG Faults': 'No data',
                                    'Diesel Cycle': 'No data'
                                }
                            
                            # Concatenate all feedback dataframes
                            conc_df = pd.concat(feedback_dfs, ignore_index=True) if feedback_dfs else pd.DataFrame()
                            
                            # Generate feedback text
                            feedback = feedback = f"""
**ASB Performance majorly impacted by:**<br>
• Access Issues: {asb_result['Access Issues']}<br>
• Theft and Vandalism: {asb_result['Theft and Vandalism']}<br>
• Major DG Faults: {asb_result['Major DG Faults']}<br>
• Diesel cycle: {asb_result['Diesel Cycle']}<br><br>

**IBD Performance majorly impacted by:**<br>
• Access Issues: {ibd_result['Access Issues']}<br>
• Theft and Vandalism: {ibd_result['Theft and Vandalism']}<br>
• Major DG Faults: {ibd_result['Major DG Faults']}<br>
• Diesel cycle: {ibd_result['Diesel Cycle']}
"""



                            
                            # Store results in session state
                            st.session_state['regional_analysis'] = conc_df
                            st.session_state['regional_feedback'] = feedback
                            
                            # Display results
                            st.success("✅ Analysis complete!")
                            st.markdown(feedback, unsafe_allow_html=True)
                            
                            # Display statistics
                            st.write("---")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("ASB Issues", len(asb_df))
                            with col_b:
                                st.metric("IBD Issues", len(ibd_df))
                            
                            # Show preview of issues
                            # if len(conc_df) > 0:
                            #     st.write("**Critical Issues Preview:**")
                            #     st.dataframe(conc_df.head(5), use_container_width=True)
                    else:
                        st.warning("⚠️ MTN Region column not found in processed data")
                        
            except Exception as e:
                st.error(f"❌ Error analyzing data: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        # Download button for issues
        if 'regional_analysis' in st.session_state and len(st.session_state['regional_analysis']) > 0:
            st.write("---")
            st.write("**Download Issues Report**")
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state['regional_analysis'].to_excel(writer, index=False, sheet_name='Issues')
            output.seek(0)
            
            # Generate filename
            week_num = st.session_state.get('processed_week_number', 'XX')
            filename = f"Week {week_num} Processed Issues.xlsx"
            
            st.download_button(
                label=f"📥 Download {filename}",
                data=output,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


# # Create three columns
# col1_1 = st.columns(1)
# # ==========================================
# # COLUMN 3: PLACEHOLDER FOR REPORT 1_1
# # ==========================================
# with col1_1:
st.subheader("🔧 Maintenance Vendor Analysis")

with st.container(border=True):
    # Check if processed outages exist
    if 'processed_outages' not in st.session_state:
        st.info("⏳ Please process outages in Column 1 first")
    else:
        try:
            with st.spinner("Analyzing vendor performance..."):
                # Load processed data
                df = st.session_state['processed_outages'].copy()
                
                # Filter for MTN regions
                if 'MTN Region' in df.columns and 'Maintenance Vendor' in df.columns:
                    df_mtn = df[df['MTN Region'].isin(['ASB', 'IBD'])]
                    
                    if len(df_mtn) == 0:
                        st.warning("⚠️ No data found for ASB or IBD regions")
                    else:
                        def create_vendor_rca_table(region_df, region_name):
                            """Create a pivot table showing vendors vs top 5 RCAs"""
                            
                            if len(region_df) == 0:
                                st.info(f"No data available for {region_name}")
                                return None
                            
                            # Get top 5 RCAs for this region
                            if 'RCA 3' in region_df.columns:
                                rca_df = region_df[region_df['RCA 3'] != "No Intervention"]
                                top_rcas = rca_df['RCA 3'].value_counts().head(5).index.tolist()
                                
                                # Create pivot table
                                vendor_rca_data = []
                                
                                vendors = rca_df['Maintenance Vendor'].dropna().unique()
                                
                                for vendor in vendors:
                                    vendor_df = rca_df[rca_df['Maintenance Vendor'] == vendor]
                                    row_data = {'Vendor': vendor}
                                    
                                    # Count occurrences of each top RCA for this vendor
                                    for rca in top_rcas:
                                        count = len(vendor_df[vendor_df['RCA 3'] == rca])
                                        row_data[rca] = count
                                    
                                    # Add total column
                                    row_data['Total'] = len(vendor_df)
                                    vendor_rca_data.append(row_data)
                                
                                # Create DataFrame
                                vendor_table = pd.DataFrame(vendor_rca_data)
                                
                                # Sort by Total descending
                                vendor_table = vendor_table.sort_values('Total', ascending=False)
                                
                                return vendor_table, top_rcas
                            else:
                                st.warning(f"RCA 1 column not found for {region_name}")
                                return None
                        
                        # Process ASB Region
                        st.write("### 📍 ASABA (ASB) Region")
                        asb_df = df_mtn[df_mtn['MTN Region'] == 'ASB'].copy()
                        
                        asb_result = create_vendor_rca_table(asb_df, "ASB")
                        
                        if asb_result:
                            asb_table, asb_rcas = asb_result
                            
                            # Display metrics
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total Vendors", len(asb_table))
                            with col_b:
                                st.metric("Total Outages", asb_table['Total'].sum())
                            with col_c:
                                if len(asb_table) > 0:
                                    st.metric("Worst Vendor", asb_table.iloc[0]['Vendor'][:15] + "...")
                            
                            # Display table
                            st.dataframe(
                                asb_table.style.background_gradient(
                                    subset=[col for col in asb_table.columns if col not in ['Vendor']],
                                    cmap='Reds'
                                ),
                                use_container_width=True,
                                height=300
                            )
                            
                            # Store in session state
                            st.session_state['asb_vendor_table'] = asb_table
                        
                        st.write("---")
                        
                        # Process IBD Region
                        st.write("### 📍 IBADAN (IBD) Region")
                        ibd_df = df_mtn[df_mtn['MTN Region'] == 'IBD'].copy()
                        
                        ibd_result = create_vendor_rca_table(ibd_df, "IBD")
                        
                        if ibd_result:
                            ibd_table, ibd_rcas = ibd_result
                            
                            # Display metrics
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total Vendors", len(ibd_table))
                            with col_b:
                                st.metric("Total Outages", ibd_table['Total'].sum())
                            with col_c:
                                if len(ibd_table) > 0:
                                    st.metric("Worst Vendor", ibd_table.iloc[0]['Vendor'][:15] + "...")
                            
                            # Display table
                            st.dataframe(
                                ibd_table.style.background_gradient(
                                    subset=[col for col in ibd_table.columns if col not in ['Vendor']],
                                    cmap='Reds'
                                ),
                                use_container_width=True,
                                height=300
                            )
                            
                            # Store in session state
                            st.session_state['ibd_vendor_table'] = ibd_table
                        
                        st.success("✅ Vendor analysis complete!")
                else:
                    st.warning("⚠️ Required columns (MTN Region, Maintenance Vendor) not found")
                    
        except Exception as e:
            st.error(f"❌ Error analyzing vendors: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # Download button for vendor analysis
    if 'asb_vendor_table' in st.session_state or 'ibd_vendor_table' in st.session_state:
        st.write("---")
        st.write("**Download Vendor Analysis**")
        
        # Create Excel file with both sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if 'asb_vendor_table' in st.session_state:
                st.session_state['asb_vendor_table'].to_excel(writer, index=False, sheet_name='ASB Vendors')
            if 'ibd_vendor_table' in st.session_state:
                st.session_state['ibd_vendor_table'].to_excel(writer, index=False, sheet_name='IBD Vendors')
        output.seek(0)
        
        # Generate filename
        week_num = st.session_state.get('processed_week_number', 'XX')
        filename = f"Week {week_num} Vendor Analysis.xlsx"
        
        st.download_button(
            label=f"📥 Download {filename}",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )