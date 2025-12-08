"""
pages/Escalation_Analyzer.py - Customer Escalation Analysis System
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import io
from agents.escalations_analyzer import EscalationAnalyzerAgent, validate_excel_file

# Import backend (assuming it's in the same directory or Python path)
# from escalation_analyzer_backend import EscalationAnalyzerAgent, validate_excel_file

st.set_page_config(page_title="Escalation Analyzer", page_icon="📊", layout="wide")


agent = EscalationAnalyzerAgent()

# Check authentication
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Please log in to view this page.")
    st.stop()

# Check if main data is loaded
if not st.session_state.get("file_uploaded", False):
    st.warning("⚠️ Please upload the main data file on the Homepage first.")
    st.stop()

# Load session data
df1 = st.session_state["df_init"]
pa_df1 = st.session_state["pa_init"]
db1 = st.session_state["db"]
db_full1 = st.session_state["db_full"]

# Initialize session state for this page
if "escalation_file_uploaded" not in st.session_state:
    st.session_state.escalation_file_uploaded = False
if "escalation_df" not in st.session_state:
    st.session_state.escalation_df = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "duplicate_log" not in st.session_state:
    st.session_state.duplicate_log = []

# Page header
st.title("📊 Escalation Analyzer")
st.markdown("""
Upload customer escalation file and get AI-powered analysis of site outages with executive summaries.
""")

# Step 1: File Upload
st.subheader("📁 Step 1: Upload Escalation File")

uploaded_file = st.file_uploader(
    "Upload Excel file containing escalation outage data",
    type=["xlsx", "xls"],
    help="File should contain columns: Number, Site ID, Outage Start Time, Primary Cause, RCA 1-3, etc."
)
# st.session_state.escalation_file_uploaded = False

if uploaded_file is not None and not st.session_state.escalation_file_uploaded:
    with st.spinner("🔍 Validating and processing file..."):
        try:
            # Read Excel file
            df_upload = pd.read_excel(uploaded_file, engine="openpyxl")

            is_valid, message, cleaned_df = validate_excel_file(df_upload)
            

            # Store in session state
            st.session_state.escalation_df = cleaned_df
            st.session_state.duplicate_log = message
            st.session_state.escalation_file_uploaded = True
            
            # Success message
            st.success(f"✅ File validated! {len(cleaned_df)} records loaded.")
            
            if message:
                st.info(message)
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.stop()

# Show duplicate log if exists
if st.session_state.duplicate_log:
    with st.expander("📋 View Duplicate Removal Log"):
        # st.dataframe(pd.DataFrame(st.session_state.duplicate_log), use_container_width=True)
        st.info(st.session_state.duplicate_log)

# Step 2: User Inputs (only show if file is uploaded)
if st.session_state.escalation_file_uploaded:
    st.markdown("---")
    st.subheader("🎯 Step 2: Define Escalation Scope")
    
    escalation_df = st.session_state.escalation_df
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Customer selection
        tenant_names = db_full1["Tenant Name"].dropna().unique().tolist()
        
        # Priority customers first
        priority_customers = ["MTN NG", "Airtel NG", "Spectranet"]
        other_customers = sorted([c for c in tenant_names if c not in priority_customers])
        customer_options = priority_customers + other_customers
        
        selected_customer = st.selectbox(
            "Select Customer",
            options=customer_options,
            help="Choose the customer for this escalation analysis"
        )
        
        # Date range
        min_date = escalation_df["Outage Start Time"].min().date()
        max_date = escalation_df["Outage Start Time"].max().date()
        
        date_range = st.date_input(
            "Escalation Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            help="Select the date range for this escalation"
        )
    
    with col2:
        # Site IDs input
        site_ids_input = st.text_area(
            "Enter Site IDs (one per line)",
            height=150,
            placeholder="IHS_OYO_0833A\nT3515\nOS0655",
            help="Paste site IDs, one per line. Can be either Tenant IDs or IHS Site IDs"
        )
        
        # ID type selection
        id_type = st.selectbox(
            "Site ID Type",
            options=["IHS Site ID", "Tenant ID"],
            help="Specify whether the IDs above are IHS Site IDs or Tenant IDs"
        )
    
    # Process button
    if st.button("🔍 Preview & Confirm", type="primary", use_container_width=True):
        if not site_ids_input.strip():
            st.error("❌ Please enter at least one site ID")
        else:
            # Parse site IDs
            site_ids = [sid.strip() for sid in site_ids_input.split("\n") if sid.strip()]
            
            # Resolve IDs
            resolved_sites = []
            not_found = []
            
            for site_id in site_ids:
                if id_type == "IHS Site ID":
                    # Lookup in db_full
                    match = db_full1[db_full1["IHS Site ID"] == site_id]
                    if not match.empty:
                        row = match.iloc[0]
                        resolved_sites.append({
                            "IHS Site ID": row["IHS Site ID"],
                            "Tenant ID": row.get("Tenant ID", "-"),
                            "Tenant Name": row.get("Tenant Name", "-"),
                            "Region": row.get("Region", "-"),
                            "State": row.get("State", "-")
                        })
                    else:
                        not_found.append(site_id)
                else:  # Tenant ID
                    # Filter by customer first, then lookup
                    customer_sites = db_full1[db_full1["Tenant Name"] == selected_customer]
                    match = customer_sites[customer_sites["Tenant ID"].astype(str) == site_id]
                    if not match.empty:
                        row = match.iloc[0]
                        resolved_sites.append({
                            "IHS Site ID": row["IHS Site ID"],
                            "Tenant ID": row.get("Tenant ID", "-"),
                            "Tenant Name": row.get("Tenant Name", "-"),
                            "Region": row.get("Region", "-"),
                            "State": row.get("State", "-")
                        })
                    else:
                        not_found.append(site_id)
            
            # Store in session state
            st.session_state.resolved_sites = resolved_sites
            st.session_state.not_found_sites = not_found
            st.session_state.date_range = date_range
            st.session_state.selected_customer = selected_customer
            st.session_state.show_confirmation = True
            
            st.rerun()

# Step 3: Confirmation Dialog
if st.session_state.get("show_confirmation", False):
    
    @st.dialog("🔍 Confirm Escalation Details", width="large")
    def show_confirmation_dialog():
        resolved_sites = st.session_state.resolved_sites
        not_found = st.session_state.not_found_sites
        date_range = st.session_state.date_range
        customer = st.session_state.selected_customer
        
        st.markdown(f"### 📋 Escalation Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Customer", customer)
        with col2:
            st.metric("Sites Found", len(resolved_sites))
        with col3:
            if isinstance(date_range, tuple) and len(date_range) == 2:
                date_str = f"{date_range[0]} to {date_range[1]}"
            else:
                date_str = str(date_range)
            st.metric("Date Range", date_str)
        
        if not_found:
            st.warning(f"⚠️ {len(not_found)} site(s) not found in database: {', '.join(not_found[:5])}")
        
        st.markdown("### 🏢 Resolved Sites")
        st.dataframe(pd.DataFrame(resolved_sites), use_container_width=True, height=300)
        
        st.markdown("### 📊 Sample Data Preview")
        escalation_df = st.session_state.escalation_df
        
        # Filter by date range
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = escalation_df[
                (escalation_df["Outage Start Time"].dt.date >= start_date) &
                (escalation_df["Outage Start Time"].dt.date <= end_date)
            ]
        else:
            filtered_df = escalation_df
        
        st.dataframe(filtered_df.head(10), use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Proceed with Analysis", type="primary", use_container_width=True):
                st.session_state.show_confirmation = False
                st.session_state.start_analysis = True
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_confirmation = False
                st.rerun()
    
    show_confirmation_dialog()

# Step 4: Run Analysis
if st.session_state.get("start_analysis", False):
    st.markdown("---")
    st.subheader("🤖 AI Analysis in Progress")
    
    resolved_sites = st.session_state.resolved_sites
    escalation_df = st.session_state.escalation_df
    date_range = st.session_state.date_range
    customer = st.session_state.selected_customer
    
    # Filter escalation data by date range
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        escalation_df_filtered = escalation_df[
            (escalation_df["Outage Start Time"].dt.date >= start_date) &
            (escalation_df["Outage Start Time"].dt.date <= end_date)
        ]
    else:
        escalation_df_filtered = escalation_df
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    # Placeholder for AI agent
    # In production: agent = EscalationAnalyzerAgent()
    
    total_sites = len(resolved_sites)
    
    for idx, site_info in enumerate(resolved_sites):
        ihs_site_id = site_info["IHS Site ID"]
        
        # Update progress
        progress = (idx + 1) / total_sites
        progress_bar.progress(progress)
        status_text.text(f"Analyzing site {idx + 1}/{total_sites}: {ihs_site_id}")
        
        # Filter outages for this site
        site_outages = escalation_df_filtered[escalation_df_filtered["IHS Site ID"] == ihs_site_id]
        
        if site_outages.empty:
            # No outages found
            result = {
                "IHS Site ID": ihs_site_id,
                "Tenant Name": site_info["Tenant Name"],
                "Tenant ID": site_info["Tenant ID"],
                "HUB Priority": "-",
                "Tenant Priority": "-",
                "IHS Priority": "-",
                "First Outage Date": "-",
                "Last Outage Date": "-",
                "MTTR Sum": "-",
                "Count of Outages": 0,
                "Major RCA": "-",
                "Bucket": "TX Issue",
                "What was done to close": "No outage data found",
                "Extra Comments": "No outage records in specified period",
                "provider_used": "N/A"
            }
        else:
            # Get site details from db_full
            db_match = db_full1[
                (db_full1["IHS Site ID"] == ihs_site_id) &
                (db_full1["Tenant Name"] == customer)
            ]
            
            if not db_match.empty:
                site_row = db_match.iloc[0]
                hub_priority = site_row.get("Tenant Operational Priority", "-")
                tenant_priority = site_row.get("Tenant Contractual Priority", "-")
                ihs_priority = site_row.get("IHS Site Priority", "-")
            else:
                hub_priority = "-"
                tenant_priority = "-"
                ihs_priority = "-"
            
            # Calculate metrics
            first_outage = site_outages["Outage Start Time"].min()
            # print(first_outage)
            last_outage = site_outages["Outage Start Time"].max()
            mttr_sum = site_outages["Outage Duration"].sum()
            outage_count = len(site_outages)
            
            # Format MTTR
            if hasattr(mttr_sum, "total_seconds"):
                mttr_hours = mttr_sum.total_seconds() / 3600
                mttr_display = f"{mttr_hours:.2f} hrs"
            else:
                mttr_display = str(mttr_sum)
            
            # Placeholder for AI analysis
            # In production: analysis = agent.analyze_site_outages(site_outages, ihs_site_id)
            
            # Demo/fallback analysis
            rca_counts = site_outages["RCA 3"].value_counts()
            top_rcas = " | ".join(rca_counts.head(3).index.tolist())
            
            res = agent.analyze_site_outages(site_outages, ihs_site_id)
            # print(res)
            result = {
                "IHS Site ID": ihs_site_id,
                "Tenant Name": site_info["Tenant Name"],
                "Tenant ID": site_info["Tenant ID"],
                "HUB Priority": hub_priority,
                "Tenant Priority": tenant_priority,
                "IHS Priority": ihs_priority,
                "First Outage Date": first_outage.strftime("%Y-%m-%d"),
                "Last Outage Date": last_outage.strftime("%Y-%m-%d"),
                "MTTR Sum": mttr_display,
                "Count of Outages": outage_count,
                "Major RCA": top_rcas,
                "Bucket": "NR",  # AI would determine this
                "What was done to close": f"{outage_count} outages resolved, {mttr_display} total downtime",
                "Extra Comments": f"{res['detailed_comments'] if 'detailed_comments' in res else 'N/A'}",
                "provider_used": res.get("provider_used", "N/A")
            }
        
        results.append(result)
    
    # Complete
    progress_bar.progress(1.0)
    status_text.text("✅ Analysis complete!")
    
    # Store results
    st.session_state.analysis_results = pd.DataFrame(results)
    st.session_state.start_analysis = False
    
    st.success(f"🎉 Successfully analyzed {len(results)} sites!")
    st.rerun()

# Step 5: Display Results
if st.session_state.analysis_results is not None:
    st.markdown("---")
    st.subheader("📊 Executive Summary Dashboard")
    
    results_df = st.session_state.analysis_results
    
    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Sites", len(results_df))
    
    with col2:
        total_outages = results_df["Count of Outages"].sum()
        st.metric("Total Outages", total_outages)
    
    with col3:
        # Calculate average MTTR (need to parse from string)
        avg_mttr = "N/A"  # Would calculate from actual data
        st.metric("Avg MTTR/Site", avg_mttr)
    
    with col4:
        # Most common bucket
        most_common_bucket = results_df["Bucket"].mode()
        if len(most_common_bucket) > 0:
            st.metric("Top Bucket", most_common_bucket[0])
        else:
            st.metric("Top Bucket", "N/A")
    
    with col5:
        # Sites with issues
        sites_with_issues = len(results_df[results_df["Count of Outages"] > 0])
        st.metric("Sites w/ Issues", sites_with_issues)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Bucket distribution
        bucket_counts = results_df["Bucket"].value_counts().reset_index()
        bucket_counts.columns = ["Bucket", "Count"]
        
        fig_bucket = px.pie(
            bucket_counts,
            values="Count",
            names="Bucket",
            title="Issue Distribution by Bucket",
            hole=0.4
        )
        st.plotly_chart(fig_bucket, use_container_width=True)
    
    with col2:
        # Top sites by outage count
        top_sites = results_df.nlargest(10, "Count of Outages")[["IHS Site ID", "Count of Outages"]]
        
        fig_sites = px.bar(
            top_sites,
            x="Count of Outages",
            y="IHS Site ID",
            orientation="h",
            title="Top 10 Sites by Outage Count",
            color="Count of Outages",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_sites, use_container_width=True)
    
    # Full results table
    st.markdown("---")
    st.subheader("📋 Detailed Analysis Results")
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_bucket = st.multiselect("Filter by Bucket", results_df["Bucket"].unique())
    with col2:
        filter_priority = st.multiselect("Filter by IHS Priority", results_df["IHS Priority"].unique())
    with col3:
        min_outages = st.number_input("Min Outages", min_value=0, value=0)
    
    # Apply filters
    filtered_results = results_df.copy()
    if filter_bucket:
        filtered_results = filtered_results[filtered_results["Bucket"].isin(filter_bucket)]
    if filter_priority:
        filtered_results = filtered_results[filtered_results["IHS Priority"].isin(filter_priority)]
    if min_outages > 0:
        filtered_results = filtered_results[filtered_results["Count of Outages"] >= min_outages]
    
    st.dataframe(filtered_results, use_container_width=True, height=500)
    
    # Download button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Convert to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_results.to_excel(writer, index=False, sheet_name='Analysis Results')
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Analysis Report (Excel)",
            data=excel_data,
            file_name=f"escalation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )