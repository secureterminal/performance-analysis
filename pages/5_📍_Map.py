import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from datetime import datetime

# Block unauthenticated access
if not st.session_state.get("logged_in", False):
    st.error("🔒 Please log in to view this page.")
    # st.page_link("app.py", label="Login", icon="🔐")
    st.session_state.login_messages = "Please login to view this site"
    st.switch_page("🏠 Homepage.py")

# # Page content here
# st.title("📍 Map / Location Page")
# st.write("Welcome to the map and location dashboard.")


# -------------------------------------------------
# Page config
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
# Title
# -------------------------------------------------
st.title("Sites Operational Dashboard")
st.markdown("**Multi-Zone View** | Real-time site status & geospatial insights")

# -------------------------------------------------
# File upload
# -------------------------------------------------


db_full1 = st.session_state["db_full"]

db_full = db_full1.copy()


if db_full is not None:
    # -------------------------------------------------
    # Required columns check
    # -------------------------------------------------
    required_cols = [
        "Zone", "IHS Site ID", "Tenant ID", "Tenant Name", "Site Address",
        "Site Operational Status", "Region", "State", "EFS Name",
        "RTO Name", "SBC", "Latitude", "Longitude", "Project"
    ]
    missing = [c for c in required_cols if c not in db_full.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        st.stop()

    # -------------------------------------------------
    # Clean & prepare data
    # -------------------------------------------------
    db_full = db_full[db_full["Project"].str.strip() != "GICL"].copy()

    db_full["Latitude"] = pd.to_numeric(db_full["Latitude"], errors="coerce")
    db_full["Longitude"] = pd.to_numeric(db_full["Longitude"], errors="coerce")

    for col in ["IHS Site ID", "Tenant ID", "Tenant Name", "Zone", "Region", "State"]:
        db_full[col] = db_full[col].astype(str).str.strip()

    db_full = db_full[~db_full["IHS Site ID"].isin(["", "nan", "None", "<NA>"])]

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
        "Zone", options=all_zones, default=["South"] if "South" in all_zones else all_zones[:1]
    )

    def multiselect(label, col, default_all=True):
        opts = sorted(db_full[col].dropna().unique())
        return st.sidebar.multiselect(label, options=opts, default=opts if default_all else [])

    sel_tenant = multiselect("Tenant Name", "Tenant Name")
    sel_region = multiselect("Region", "Region")
    sel_state = st.sidebar.multiselect("State", options=sorted(db_full["State"].unique()))
    sel_status = multiselect("Site Operational Status", "Site Operational Status")
    sel_efs = multiselect("EFS Name", "EFS Name")
    sel_rto = multiselect("RTO Name", "RTO Name")
    sel_sbc = multiselect("SBC", "SBC")

    # Apply filters
    filtered = db_full.copy()
    for col, vals in {
        "Zone": sel_zone,
        "Tenant Name": sel_tenant,
        "Region": sel_region,
        "State": sel_state,
        "Site Operational Status": sel_status,
        "EFS Name": sel_efs,
        "RTO Name": sel_rto,
        "SBC": sel_sbc,
    }.items():
        if vals:
            filtered = filtered[filtered[col].isin(vals)]

    if filtered.empty:
        st.warning("No sites match the current filters.")
        st.stop()

    # -------------------------------------------------
    # KPI Calculations
    # -------------------------------------------------
    unique_sites = filtered.drop_duplicates("IHS Site ID")
    total_sites = len(unique_sites)

    mtn_rows = filtered[filtered["Tenant Name"] == "MTN NG"]
    airtel_rows = filtered[filtered["Tenant Name"] == "Airtel NG"]
    mtn_sites = len(mtn_rows)
    airtel_sites = len(airtel_rows)

    operational_sites = len(unique_sites[unique_sites["Site Operational Status"] == "On Air"])

    # -------------------------------------------------
    # KPI Cards
    # -------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Sites", f"{total_sites:,}")
    with c2: st.metric("MTN Sites", f"{mtn_sites:,}", delta=f"{mtn_sites/total_sites*100:.1f}%" if total_sites else "0%")
    with c3: st.metric("Airtel Sites", f"{airtel_sites:,}", delta=f"{airtel_sites/total_sites*100:.1f}%" if total_sites else "0%")
    with c4: st.metric("Operational", f"{operational_sites:,}", delta=f"{operational_sites/total_sites*100:.1f}%" if total_sites else "0%")

    # -------------------------------------------------
    # Tabs
    # -------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["Site Analytics", "Geospatial View", "Zone Comparison"])

    # ---------- ANALYTICS TAB ----------
    with tab1:
        colA, colB = st.columns([2, 1])
        with colA:
            st.subheader("Site Status (Unique Sites)")
            status_db_full = unique_sites["Site Operational Status"].value_counts().reset_index()
            status_db_full.columns = ["Status", "Count"]
            fig_pie = px.pie(status_db_full, values="Count", names="Status", hole=0.3,
                                color_discrete_map={"On Air": "#10a300", "Down": "#ff3b30"})
            st.plotly_chart(fig_pie, use_container_width=True)

        with colB:
            st.subheader("Tenant Breakdown")
            tenant_db_full = filtered["Tenant Name"].value_counts().reset_index()
            tenant_db_full.columns = ["Tenant", "Records"]
            fig_bar = px.bar(tenant_db_full, x="Tenant", y="Records", text="Records")
            fig_bar.update_traces(textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Detailed Tenant Records")
        disp_cols = ["IHS Site ID", "Tenant ID", "Tenant Name", "Site Address", "Site Operational Status",
                        "State", "Region", "EFS Name", "RTO Name", "SBC", "Latitude", "Longitude"]
        st.dataframe(filtered[disp_cols].sort_values("IHS Site ID"), use_container_width=True, height=500)

        # -------------------------------------------------
        # DOWNLOAD BUTTONS (MTN / AIRTEL)
        # -------------------------------------------------
        st.markdown("---")
        st.subheader("Download Filtered Tenant Data")

        export_cols = [
            "IHS Site ID", "Site Address", "Tenant Region", "Tenant ID", "Tenant Operational Status",
            "IHS Site Priority", "Zone", "Region", "State", "EFS Name", "EFS Email", "EFS Phone",
            "RTO Name", "RTO Email", "RTO Phone", "Head, Field Service", "Head, Field Service Email",
            "Head, Field Service Phone", "Customer Experience Manager", "Customer Experience Manager Email",
            "Customer Experience Manager Phone", "SBC", "Latitude", "Longitude", "Site Operational Status"
        ]

        # Ensure export columns exist
        for col in export_cols:
            if col not in filtered.columns:
                filtered[col] = "N/A"

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            if st.button("Download MTN Sites", type="primary"):
                mtn_data = filtered[filtered["Tenant Name"] == "MTN NG"][export_cols]
                month = datetime.now().strftime("%b")
                excel_file = mtn_data.to_excel(index=False, engine='openpyxl')
                st.download_button(
                    label="MTN DB Nov.xlsx",
                    data=excel_file,
                    file_name=f"MTN DB {month}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with col_d2:
            if st.button("Download Airtel Sites", type="primary"):
                airtel_data = filtered[filtered["Tenant Name"] == "Airtel NG"][export_cols]
                month = datetime.now().strftime("%b")
                excel_file = airtel_data.to_excel(index=False, engine='openpyxl')
                st.download_button(
                    label="Airtel DB Nov.xlsx",
                    data=excel_file,
                    file_name=f"Airtel DB {month}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # ---------- MAP TAB (WITH SEARCH) ----------
    with tab2:
        st.subheader("Site Locations Map")

        # Deduplicate for map: one marker per IHS Site ID
        map_db_full = (
            filtered.dropna(subset=["Latitude", "Longitude"])
            .sort_values("IHS Site ID")
            .drop_duplicates("IHS Site ID")
            .copy()
        )

        if map_db_full.empty:
            st.warning("No valid coordinates available for mapping.")
        else:
            # === SEARCH BOX ===
            search_term = st.text_input(
                "Search Site (IHS ID, Address, Tenant)",
                placeholder="e.g. IHS12345, Lagos, MTN",
                key="map_search"
            ).strip().lower()

            # Filter map data based on search
            if search_term:
                mask = (
                    map_db_full["IHS Site ID"].str.lower().str.contains(search_term, na=False) |
                    map_db_full["Site Address"].str.lower().str.contains(search_term, na=False)
                )
                # Include tenant search across full filtered data
                tenant_sites = filtered[
                    filtered["Tenant Name"].str.lower().str.contains(search_term, na=False)
                ]["IHS Site ID"].unique()
                mask |= map_db_full["IHS Site ID"].isin(tenant_sites)
                display_db_full = map_db_full[mask].copy()
                if display_db_full.empty:
                    st.info(f"No sites found for **'{search_term}'**")
                    display_db_full = map_db_full.copy()  # fallback
            else:
                display_db_full = map_db_full.copy()

            # Center map
            center_lat = display_db_full["Latitude"].mean()
            center_lon = display_db_full["Longitude"].mean()

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=10 if search_term else 8,
                tiles="CartoDB positron"
            )
            marker_cluster = MarkerCluster().add_to(m)

            status_color = {
                "On Air": "green",
                "Down": "red",
                "Partial": "orange",
                "Under Maintenance": "gray"
            }

            for _, row in display_db_full.iterrows():
                # Get all tenants on this site
                site_tenants = filtered[
                    filtered["IHS Site ID"] == row["IHS Site ID"]
                ]["Tenant Name"].unique()
                tenants_list = ", ".join(site_tenants)

                popup_html = f"""
                <div style="font-size: 12px; width: 220px;">
                    <b>{row['IHS Site ID']}</b><br>
                    <b>Tenants:</b> {tenants_list}<br>
                    <b>Address:</b> {row['Site Address'][:50]}...<br>
                    <b>Status:</b> <strong>{row['Site Operational Status']}</strong><br>
                    <a href="https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
                        target="_blank" style="color:#1a73e8;">Get Directions</a>
                </div>
                """

                # Highlight searched sites
                color = status_color.get(row["Site Operational Status"], "blue")
                radius = 10 if search_term and (
                    search_term in row["IHS Site ID"].lower() or
                    search_term in row["Site Address"].lower() or
                    any(search_term in t.lower() for t in site_tenants)
                ) else 6

                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9 if radius > 6 else 0.7,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{row['IHS Site ID']} | {tenants_list}"
                ).add_to(marker_cluster)

            # Add search result count
            if search_term:
                st.caption(f"Showing **{len(display_db_full)}** site(s) matching **'{search_term}'**")

            st_folium(m, use_container_width=True, height=600)

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
            st.plotly_chart(fig_zone, use_container_width=True)
        with colz2:
            fig_op = px.bar(zone_summary, x="Zone", y="Operational %", title="Operational % by Zone", color="Operational %")
            st.plotly_chart(fig_op, use_container_width=True)

    # -------------------------------------------------
    # Footer
    # -------------------------------------------------
    st.markdown("---")
    st.caption(f"Data refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')} • Built with Streamlit • @NozieMezie")

else:
    st.info("Please upload **Tenant-Site.xlsb** to begin.")
    st.markdown("### Required Columns\n`IHS Site ID`, `Tenant Name`, `Zone`, `Latitude`, `Longitude`, `Project`, etc.")
