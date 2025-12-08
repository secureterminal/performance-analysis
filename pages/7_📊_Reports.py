import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Reports", page_icon="📊", layout="wide")

# Block unauthenticated access
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Please log in to view this page.")
    st.stop()

st.title("📊 Reports Management")


# Load session data
df1 = st.session_state["df_init"]
pa_df1 = st.session_state["pa_init"]
db1 = st.session_state["db"]
db_full1 = st.session_state["db_full"]


# Create three columns
col1, col2, col3 = st.columns(3)

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
        week_number = st.number_input(
            "Week Number",
            min_value=1,
            max_value=53,
            value=datetime.today().isocalendar()[1] - 1,
            help="Week number for the output file"
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
                        
                        # Step 4: Initialize customer columns (will be overwritten by merge)
                        outages_df['MTN ID'] = ""
                        outages_df['MTN Region'] = ""
                        outages_df['Airtel ID'] = ""
                        outages_df['Airtel Region'] = ""
                        
                        # Step 5: Perform merges
                        # First merge with MTN data
                        outages_df = outages_df.merge(
                            mtn_df[['IHS Site ID', 'MTN ID', 'MTN Region']], 
                            on='IHS Site ID', 
                            how='left', 
                            suffixes=('', '_mtn')
                        )
                        
                        # Second merge with Airtel data
                        outages_df = outages_df.merge(
                            airtel_df[['IHS Site ID', 'Airtel ID', 'Airtel Region']], 
                            on='IHS Site ID', 
                            how='left', 
                            suffixes=('', '_airtel')
                        )
                        
                        # Handle the merged columns - consolidate duplicates
                        # For MTN columns
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
                        
                        # For Airtel columns
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
                        
                        # Now rename Airtel columns to AIRTEL for consistency with output
                        outages_df = outages_df.rename(columns={
                            'Airtel ID': 'AIRTEL ID',
                            'Airtel Region': 'AIRTEL Region'
                        })
                        
                        # Step 6: Remove invalid sites
                        if 'Site ID' in outages_df.columns:
                            outages_df = outages_df[outages_df['Site ID'] != "-"]
                        
                        # Step 7: Calculate time boundaries

                        max_year = outages_df['Outage Start Time'].dropna().dt.year.max()

                        # First day of selected week (Monday)
                        start_of_week = datetime.fromisocalendar(max_year, week_number, 1)

                        # Last day of selected week (Sunday)
                        end_date = datetime.fromisocalendar(max_year, week_number, 7) + timedelta(days=1)

                        st.write(start_of_week)
                        st.write(end_date)

                        # today = datetime.today()
                        # start_of_current_week = today - timedelta(days=today.weekday())
                        # start_of_current_week = start_of_current_week.replace(hour=0, minute=0, second=0, microsecond=0)
                        # start_of_week = start_of_current_week - timedelta(weeks=1)
                        # end_date = start_of_current_week
                        
                        # Step 8: Handle ongoing outages
                        if 'Outage End Time' in outages_df.columns:
                            outages_df['Outage End Time'] = pd.to_datetime(outages_df['Outage End Time'], errors='coerce')
                            outages_df['Outage End Time'] = outages_df['Outage End Time'].fillna(end_date)
                        
                        # Step 9: Remove future outages
                        if 'Outage Start Time' in outages_df.columns:
                            outages_df['Outage Start Time'] = pd.to_datetime(outages_df['Outage Start Time'], errors='coerce')
                            outages_df = outages_df[outages_df['Outage Start Time'] <= end_date]
                        
                        # Step 10: Remove old outages
                        if 'Outage End Time' in outages_df.columns:
                            outages_df = outages_df[outages_df['Outage End Time'] >= start_of_week]
                        
                        # Step 11: Trim start times
                        if 'Outage Start Time' in outages_df.columns:
                            mask = (outages_df['Outage Start Time'] < start_of_week)
                            outages_df.loc[mask, 'Outage Start Time'] = start_of_week
                        
                        # Step 12: Trim end times
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
                        
                        # Step 16: Select columns (only those that exist)
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
                        
                        # Filter to only include columns that exist in the dataframe
                        existing_columns = [col for col in columns_to_select if col in outages_df.columns]
                        outages_df = outages_df[existing_columns]
                        
                        # Store in session state
                        st.session_state['processed_outages'] = outages_df
                        st.session_state['processed_week_number'] = week_number
                        
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
                    # Show the full traceback for debugging
                    import traceback
                    st.code(traceback.format_exc())
        
        # Download button
        if 'processed_outages' in st.session_state:
            st.write("---")
            st.write("**Download Processed File**")
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state['processed_outages'].to_excel(writer, index=False, sheet_name='Outages')
            output.seek(0)
            
            # Generate filename
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
    st.subheader("📈 Regional Impact Analysis")
    
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
                                    (region_df['Outage Duration Hours'] > 3)
                                ]
                                access_issues = ', '.join(access_denial['MTN ID'].dropna().astype(str).unique())
                                if len(access_denial) > 0:
                                    feedback_list_access = access_denial[['MTN ID', 'Site ID', 'MTN Region', 'RCA 1', 'Resolution Comments', 'Outage Duration']]
                                    region_feedback_dfs.append(feedback_list_access)
                                
                                # Theft and Vandalism
                                theft = region_df[
                                    (region_df['Primary Cause'] == 'Site Asset Theft') &
                                    (region_df['Outage Duration Hours'] > 3)
                                ]
                                theft_vandalism = ', '.join(theft['MTN ID'].dropna().astype(str).unique())
                                if len(theft) > 0:
                                    feedback_list_theft = theft[['MTN ID', 'Site ID', 'MTN Region', 'RCA 1', 'Resolution Comments', 'Outage Duration']]
                                    region_feedback_dfs.append(feedback_list_theft)
                                
                                # Major DG Faults (using RCA 2)
                                if 'RCA 2' in region_df.columns:
                                    dg_faults = region_df[
                                        region_df['RCA 2'].str.contains('DG', case=False, na=False)
                                    ].sort_values('Outage Duration Hours', ascending=False)
                                    major_dg = ', '.join(dg_faults['MTN ID'].dropna().astype(str).unique()[:5])
                                    if len(dg_faults) > 0:
                                        feedback_list_dg = dg_faults[['MTN ID', 'Site ID', 'MTN Region', 'RCA 1', 'Resolution Comments', 'Outage Duration']].head(5)
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
                            if len(conc_df) > 0:
                                st.write("**Critical Issues Preview:**")
                                st.dataframe(conc_df.head(5), use_container_width=True)
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


# ==========================================
# COLUMN 3: PLACEHOLDER FOR REPORT 3
# ==========================================
with col3:
    st.subheader("📊 Report 3")
    
    with st.container(border=True):
        st.info("🚧 Report module coming soon...")
        st.write("This section will contain the third reporting functionality.")
        
        # Placeholder content
        st.write("**Features:**")
        st.write("- Feature 1")
        st.write("- Feature 2")
        st.write("- Feature 3")