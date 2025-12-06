import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from datetime import datetime
import numpy as np

# -------------------------------------------------
# Page config (MUST be first)
# -------------------------------------------------
st.set_page_config(
    page_title="Sites Dashboard – Multi-Zone",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'Multi-Zone Telecom Sites Dashboard • @NozieMezie'
    }
)

# -------------------------------------------------
# CSS
# -------------------------------------------------
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

# -------------------------------------------------
# Authentication Check
# -------------------------------------------------
if not st.session_state.get("logged_in", False):
    st.markdown(hide_sidebar, unsafe_allow_html=True)
    st.error("🔒 Please log in to view this page.")
    st.session_state.login_messages = "Please login to view this site"
    st.switch_page("🏠 Homepage.py")
else:
    st.markdown(show_sidebar, unsafe_allow_html=True)

# -------------------------------------------------
# Data Check
# -------------------------------------------------
if "db_full" not in st.session_state:
    st.error("⚠️ Data not loaded. Please upload a file on the homepage first.")
    st.info("👉 Redirecting to homepage...")
    st.switch_page("🏠 Homepage.py")

# -------------------------------------------------
# Title
# -------------------------------------------------
st.title("Sites Operational Dashboard")
st.markdown("**Multi-Zone View** | Real-time site status & geospatial insights")

# -------------------------------------------------
# Cached Data Processing Function
# -------------------------------------------------
@st.cache_data
def process_db_data(db_full_data):
    """Process and clean database - cached for performance"""
    db_full = db_full_data.copy()
    
    # Check required columns
    required_cols = [
        "Zone", "IHS Site ID", "Tenant ID", "Tenant Name", "Site Address",
        "Site Operational Status", "Region", "State", "EFS Name",
        "RTO Name", "SBC", "Latitude", "Longitude", "Project"
    ]
    missing = [c for c in required_cols if c not in db_full.columns]
    if missing:
        return None, missing
    
    # Clean data
    db_full = db_full[db_full["Project"].str.strip() != "GICL"].copy()
    db_full["Latitude"] = pd.to_numeric(db_full["Latitude"], errors="coerce")
    db_full["Longitude"] = pd.to_numeric(db_full["Longitude"], errors="coerce")
    
    for col in ["IHS Site ID", "Tenant ID", "Tenant Name", "Zone", "Region", "State"]:
        if col in db_full.columns:
            db_full[col] = db_full[col].astype(str).str.strip()
    
    db_full = db_full[~db_full["IHS Site ID"].isin(["", "nan", "None", "<NA>"])]
    
    return db_full, None

# Process data with caching
db_full, missing_cols = process_db_data(st.session_state["db_full"])

if db_full is None:
    st.error(f"Missing columns: {', '.join(missing_cols)}")
    st.stop()

if db_full.empty:
    st.error("No valid data after cleaning.")
    st.stop()

# -------------------------------------------------
# Sidebar Filters
# -------------------------------------------------
st.sidebar.header("Filters")

# Zone filter - default South
all_zones = sorted(db_full["Zone"].unique())
sel_zone = st.sidebar.multiselect(
    "Zone", 
    options=all_zones, 
    default=["South"] if "South" in all_zones else all_zones[:1],
    key="zone_filter"
)

def multiselect_filter(label, col, key, default_all=True):
    opts = sorted(db_full[col].dropna().unique())
    return st.sidebar.multiselect(
        label, 
        options=opts, 
        default=opts if default_all else [],
        key=key
    )

sel_tenant = multiselect_filter("Tenant Name", "Tenant Name", "tenant_filter")
sel_region = multiselect_filter("Region", "Region", "region_filter")
sel_state = st.sidebar.multiselect(
    "State", 
    options=sorted(db_full["State"].unique()),
    key="state_filter"
)
sel_status = multiselect_filter("Site Operational Status", "Site Operational Status", "status_filter")
sel_efs = multiselect_filter("EFS Name", "EFS Name", "efs_filter")
sel_rto = multiselect_filter("RTO Name", "RTO Name", "rto_filter")
sel_sbc = multiselect_filter("SBC", "SBC", "sbc_filter")

# -------------------------------------------------
# Apply Filters (Cached)
# -------------------------------------------------
@st.cache_data
def apply_filters(df, zone, tenant, region, state, status, efs, rto, sbc):
    """Apply all filters - cached for performance"""
    filtered = df.copy()
    
    filter_dict = {
        "Zone": zone,
        "Tenant Name": tenant,
        "Region": region,
        "State": state,
        "Site Operational Status": status,
        "EFS Name": efs,
        "RTO Name": rto,
        "SBC": sbc,
    }
    
    for col, vals in filter_dict.items():
        if vals:
            filtered = filtered[filtered[col].isin(vals)]
    
    return filtered

filtered = apply_filters(
    db_full, 
    tuple(sel_zone), 
    tuple(sel_tenant), 
    tuple(sel_region), 
    tuple(sel_state),
    tuple(sel_status), 
    tuple(sel_efs), 
    tuple(sel_rto), 
    tuple(sel_sbc)
)

if filtered.empty:
    st.warning("No sites match the current filters.")
    st.stop()

# -------------------------------------------------
# KPI Calculations (Cached)
# -------------------------------------------------
@st.cache_data
def calculate_kpis(df):
    """Calculate KPIs - cached for performance"""
    unique_sites = df.drop_duplicates("IHS Site ID")
    total_sites = len(unique_sites)
    
    mtn_sites = len(df[df["Tenant Name"] == "MTN NG"])
    airtel_sites = len(df[df["Tenant Name"] == "Airtel NG"])
    operational_sites = len(unique_sites[unique_sites["Site Operational Status"] == "On Air"])
    
    return total_sites, mtn_sites, airtel_sites, operational_sites

total_sites, mtn_sites, airtel_sites, operational_sites = calculate_kpis(filtered)

# -------------------------------------------------
# KPI Cards
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Total Sites", f"{total_sites:,}")
with c2: st.metric("MTN Sites", f"{mtn_sites:,}", delta=f"{mtn_sites/total_sites*100:.1f}%" if total_sites else "0%")
with c3: st.metric("Airtel Sites", f"{airtel_sites:,}", delta=f"{airtel_sites/total_sites*100:.1f}%" if total_sites else "0%")
with c4: st.metric("On Air Sites", f"{operational_sites:,}", delta=f"{operational_sites/total_sites*100:.1f}%" if total_sites else "0%")

# -------------------------------------------------
# Tabs
# -------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Site Analytics", "Geospatial View", "Zone Comparison"])

# ---------- ANALYTICS TAB ----------
with tab1:
    unique_sites = filtered.drop_duplicates("IHS Site ID")
    
    colA, colB = st.columns([2, 1])
    with colA:
        st.subheader("Site Status (Unique Sites)")
        status_counts = unique_sites["Site Operational Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            status_counts, 
            values="Count", 
            names="Status", 
            hole=0.3,
            color_discrete_map={"On Air": "#10a300", "Down": "#ff3b30"}
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="status_pie")

    with colB:
        st.subheader("Tenant Breakdown")
        tenant_counts = filtered["Tenant Name"].value_counts().reset_index()
        tenant_counts.columns = ["Tenant", "Records"]
        fig_bar = px.bar(tenant_counts, x="Tenant", y="Records", text="Records")
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True, key="tenant_bar")

    st.subheader("Detailed Tenant Records")
    disp_cols = ["IHS Site ID", "Tenant ID", "Tenant Name", "Site Address", "Site Operational Status",
                    "State", "Region", "EFS Name", "RTO Name", "SBC", "Latitude", "Longitude"]
    st.dataframe(filtered[disp_cols].sort_values("IHS Site ID"), use_container_width=True, height=500)

    # Download buttons
    st.markdown("---")
    st.subheader("Download Filtered Tenant Data")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        mtn_data = filtered[filtered["Tenant Name"] == "MTN NG"]
        if not mtn_data.empty:
            csv_mtn = mtn_data.to_csv(index=False)
            st.download_button(
                label="📥 Download MTN Sites (CSV)",
                data=csv_mtn,
                file_name=f"MTN_Sites_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_mtn"
            )
    
    with col_d2:
        airtel_data = filtered[filtered["Tenant Name"] == "Airtel NG"]
        if not airtel_data.empty:
            csv_airtel = airtel_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Airtel Sites (CSV)",
                data=csv_airtel,
                file_name=f"Airtel_Sites_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_airtel"
            )

# ---------- MAP TAB ----------
with tab2:
    st.subheader("Site Locations Map")
    
    # Deduplicate for map
    map_data = (
        filtered.dropna(subset=["Latitude", "Longitude"])
        .sort_values("IHS Site ID")
        .drop_duplicates("IHS Site ID")
        .copy()
    )
    
    if map_data.empty:
        st.warning("No valid coordinates available for mapping.")
    else:
        # Search box
        search_term = st.text_input(
            "Search Site (IHS ID, Address, Tenant)",
            placeholder="e.g. IHS12345, Lagos, MTN",
            key="map_search_input"
        ).strip().lower()
        
        # Add a button to trigger map update
        col_search, col_button = st.columns([3, 1])
        with col_button:
            search_button = st.button("🔍 Search", key="search_map_btn")
        
        # Use session state to control map updates
        if "last_search_term" not in st.session_state:
            st.session_state.last_search_term = ""
        
        # Only update if search button clicked or first load
        if search_button or "map_generated" not in st.session_state:
            st.session_state.last_search_term = search_term
            st.session_state.map_generated = True
        
        # Use the stored search term
        active_search = st.session_state.last_search_term
        
        # Filter based on search
        if active_search:
            mask = (
                map_data["IHS Site ID"].str.lower().str.contains(active_search, na=False) |
                map_data["Site Address"].str.lower().str.contains(active_search, na=False) |
                map_data["Tenant Name"].str.lower().str.contains(active_search, na=False)
            )
            display_data = map_data[mask].copy()
            if display_data.empty:
                st.info(f"No sites found for **'{active_search}'**")
                display_data = map_data  
            st.caption(f"Showing **{len(display_data)}** site(s) {f'matching **{active_search}**' if active_search else ''}")
        else:
            # Limit initial display for performance
            display_data = map_data
            st.caption(f"Use search to find specific sites.")
        
        # Create map - only if needed
        @st.cache_data
        def create_folium_map(df, center_lat, center_lon, zoom):
            """Create folium map - cached"""
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles="CartoDB positron"
            )
            return m
        
        # Center map
        center_lat = display_data["Latitude"].mean()
        center_lon = display_data["Longitude"].mean()
        zoom_level = 10 if active_search else 8
        
        # Create base map (cached)
        m = create_folium_map(display_data, center_lat, center_lon, zoom_level)
        
        # Add marker cluster
        marker_cluster = MarkerCluster().add_to(m)
        
        status_color = {
            "On Air": "green",
            "Down": "red",
            "Partial": "orange",
            "Under Maintenance": "gray"
        }
        
        # Add markers
        for _, row in display_data.iterrows():
            site_tenants = filtered[
                filtered["IHS Site ID"] == row["IHS Site ID"]
            ]["Tenant Name"].unique()
            tenants_list = ", ".join(site_tenants)
            
            popup_html = f"""
            <div style="font-size: 12px; width: 220px;">
                <b>{row['IHS Site ID']}</b><br>
                <b>Tenants:</b> {tenants_list}<br>
                <b>Address:</b> {str(row['Site Address'])[:50]}...<br>
                <b>Status:</b> <strong>{row['Site Operational Status']}</strong><br>
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
                    target="_blank" style="color:#1a73e8;">Get Directions</a>
            </div>
            """
            
            color = status_color.get(row["Site Operational Status"], "blue")
            
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{row['IHS Site ID']} | {tenants_list}"
            ).add_to(marker_cluster)
        
        # CRITICAL: Use returned_objects=[] to prevent rerun
        st_folium(
            m, 
            width=None,
            height=600,
            returned_objects=[],  # This prevents the map from triggering reruns
            key="site_map_display"
        )
        
        # Show table below map for better UX
        st.subheader("Sites on Map")
        display_cols = ["IHS Site ID", "Tenant Name", "Site Address", "Site Operational Status", "State"]
        st.dataframe(
            display_data[display_cols],
            use_container_width=True,
            height=300
        )
# ---------- ZONE COMPARISON TAB ----------
with tab3:
    st.subheader("Zone Comparison Dashboard")
    
    zone_summary = (
        db_full.drop_duplicates("IHS Site ID")
        .groupby("Zone")
        .agg(
            Total_Sites=("IHS Site ID", "count"),
            On_Air_Sites=("Site Operational Status", lambda x: (x == "On Air").sum()),
            MTN_Sites=("Tenant Name", lambda x: (x == "MTN NG").sum()),
            Airtel_Sites=("Tenant Name", lambda x: (x == "Airtel NG").sum())
        )
        .reset_index()
    )
    zone_summary["Operational %"] = (zone_summary["On_Air_Sites"] / zone_summary["Total_Sites"] * 100).round(1)
    st.dataframe(zone_summary, use_container_width=True)
    
    colz1, colz2 = st.columns(2)
    with colz1:
        fig_zone = px.bar(zone_summary, x="Zone", y="Total_Sites", title="Total Sites by Zone")
        st.plotly_chart(fig_zone, use_container_width=True, key="zone_bar")
    with colz2:
        fig_op = px.bar(zone_summary, x="Zone", y="Operational %", title="Operational % by Zone", color="Operational %")
        st.plotly_chart(fig_op, use_container_width=True, key="op_bar")

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
st.caption(f"Data refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')} • Built with Streamlit • @NozieMezie")