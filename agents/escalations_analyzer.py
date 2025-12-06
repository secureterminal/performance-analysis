"""
Escalation Analyzer AI System
Multi-LLM fallback: Groq → Gemini → OpenAI
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import streamlit as st
from dotenv import load_dotenv

# AI Provider imports
from groq import Groq
import google.generativeai as genai
from openai import OpenAI

def get_secret(name: str):
    """Return Streamlit secret if available, else environment variable."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass  # st.secrets not available locally

    return os.getenv(name)

class EscalationAnalyzerAgent:
    """
    AI Agent for analyzing site outages and generating executive summaries
    Uses Groq → Gemini → OpenAI fallback chain
    """

    def __init__(self):
        """Initialize all AI clients with cloud-first secret handling"""
        
        # ----------------------------
        # Groq (Primary)
        # ----------------------------
        groq_key = get_secret("GROQ_API_KEY")
        self.groq_client = None

        if groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
            except Exception as e:
                print(f"Groq initialization failed: {e}")
                st.error(f"Groq initialization failed: {e}")

        # ----------------------------
        # Gemini (Secondary)
        # ----------------------------
        gemini_key = get_secret("GEMINI_API_KEY")
        self.gemini_client = None

        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"Gemini initialization failed: {e}")
                st.error(f"Gemini initialization failed: {e}")

        # ----------------------------
        # OpenAI (Tertiary)
        # ----------------------------
        openai_key = get_secret("OPENAI_API_KEY")
        self.openai_client = None

        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
            except Exception as e:
                print(f"OpenAI initialization failed: {e}")
                st.error(f"OpenAI initialization failed: {e}")

        # Track which provider is active
        self.current_provider = None

    
    def _call_llm(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500) -> Optional[str]:
        """
        Call LLM with automatic fallback
        Priority: Groq → Gemini → OpenAI
        """
        
        # Try Groq first
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert telecom infrastructure analyst. Provide concise, actionable summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                self.current_provider = "Groq"
                return response.choices[0].message.content
            except Exception as e:
                print(f"Groq failed: {e}. Falling back to Gemini...")
        
        # Try Gemini second
        if self.gemini_client:
            try:
                response = self.gemini_client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                self.current_provider = "Gemini"
                return response.text
            except Exception as e:
                print(f"Gemini failed: {e}. Falling back to OpenAI...")
        
        # Try OpenAI third
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert telecom infrastructure analyst. Provide concise, actionable summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                self.current_provider = "OpenAI"
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI failed: {e}")
                return None
        
        return None
    
    def calculate_major_rcas(self, outages_df: pd.DataFrame, top_n: int = 3) -> str:
        """
        Calculate top RCAs based on frequency AND duration
        Prioritize high-impact (long duration) over high-frequency
        """
        if outages_df.empty or "RCA 3" not in outages_df.columns or "Outage Duration" not in outages_df.columns:
            return "-"

        # Group by RCA 3
        rca_stats = outages_df.groupby("RCA 3").agg({
            "Outage Duration": ["sum", "count"]
        }).reset_index()

        rca_stats.columns = ["RCA", "Total_Duration", "Count"]

        # ---- Convert Total_Duration to hours as float ----
        if np.issubdtype(rca_stats["Total_Duration"].dtype, np.timedelta64):
            rca_stats["Total_Duration_hours"] = (
                rca_stats["Total_Duration"].dt.total_seconds() / 3600.0
            )
        else:
            # In case it's already numeric
            rca_stats["Total_Duration_hours"] = rca_stats["Total_Duration"].astype(float)

        max_duration = rca_stats["Total_Duration_hours"].max()
        if pd.isna(max_duration) or max_duration <= 0:
            max_duration = 1.0

        max_count = rca_stats["Count"].max()
        if pd.isna(max_count) or max_count <= 0:
            max_count = 1.0

        # Impact score: Duration weight (70%) + Frequency weight (30%)
        rca_stats["Duration_Score"] = rca_stats["Total_Duration_hours"] / max_duration
        rca_stats["Frequency_Score"] = rca_stats["Count"] / max_count
        rca_stats["Impact_Score"] = (
            rca_stats["Duration_Score"] * 0.7
            + rca_stats["Frequency_Score"] * 0.3
        )

        # Sort by impact score
        rca_stats = rca_stats.sort_values("Impact_Score", ascending=False)

        # Get top N
        top_rcas = rca_stats.head(top_n)

        # Format output
        rca_list = []
        for _, row in top_rcas.iterrows():
            rca = row["RCA"]
            count = int(row["Count"])
            duration_hours = row["Total_Duration_hours"]

            if count > 1:
                rca_text = f"Repeated {rca.lower()} issues"
            else:
                rca_text = rca

            rca_list.append(rca_text)

        return " | ".join(rca_list)
    
    def analyze_site_outages(self, site_outages_df: pd.DataFrame, ihs_site_id: str) -> Dict[str, Any]:
        """
        Analyze all outages for a single site and generate summary
        
        Returns:
            {
                "summary": "Brief 30-word summary",
                "detailed_comments": "60-word detailed comments",
                "bucket": "Infra/NR/Diesel/Security/Legal/TX Issue/Active",
                "major_rcas": "Top 3 RCAs",
                "provider_used": "Groq/Gemini/OpenAI"
            }
        """
        
        if site_outages_df.empty:
            return {
                "summary": "No outage data found for this site in the specified period",
                "detailed_comments": "No outage records available for analysis",
                "bucket": "TX Issue",
                "major_rcas": "-",
                "provider_used": "N/A"
            }
        
        # Calculate major RCAs
        major_rcas = self.calculate_major_rcas(site_outages_df)
        
        # Prepare data summary for AI
        total_outages = len(site_outages_df)
        total_duration = site_outages_df["Outage Duration"].sum()
        
        # Get duration in hours
        if hasattr(total_duration, "total_seconds"):
            duration_hours = total_duration.total_seconds() / 3600
        else:
            duration_hours = total_duration
        
        # Get RCA breakdown
        rca_breakdown = site_outages_df.groupby(["Primary Cause", "RCA 1", "RCA 2", "RCA 3"]).size().reset_index(name="Count")
        rca_breakdown = rca_breakdown.sort_values("Count", ascending=False).head(10)
        
        # Get resolution comments (unique, non-null)
        resolution_comments = site_outages_df["Resolution Comments"].dropna().unique()[:10]
        resolution_notes = site_outages_df["Resolution notes"].dropna().unique()[:10]
        
        # Build prompt
        prompt = f"""Analyze these outages for site {ihs_site_id}:

            STATISTICS:
            - Total Outages: {total_outages}
            - Total Downtime: {duration_hours:.2f} hours
            - Date Range: {site_outages_df['Outage Start Time'].min()} to {site_outages_df['Outage Start Time'].max()}

            TOP RCA BREAKDOWN:
            {rca_breakdown.to_string(index=False)}

            RESOLUTION COMMENTS:
            {chr(10).join(resolution_comments[:5])}

            RESOLUTION NOTES:
            {chr(10).join(resolution_notes[:5])}

            INSTRUCTIONS:
            1. Create a BRIEF 30-word summary focusing on MTTR and RCA counts
            2. Create a DETAILED 60-word summary of what was done to close issues
            3. Assign ONE bucket: Infra, NR, Diesel, Security, Legal, TX Issue, or Active

            BUCKET DEFINITIONS:
            - Infra: Asset replacements (DG, rectifier, batteries/BUB, shelters, AC units, inverters, etc.)
            - NR: Non-routine faults, part replacements (injector, solenoid, alternator, cables, etc.)
            - Diesel: Diesel outage, blocked fuel line, diesel quality, water ingress to diesel
            - Security: Theft, vandalism, access issues, security concerns
            - Legal: Land/lease issues, community demands, legal disputes
            - TX Issue/Active: Customer equipment, transmission issues (not IHS responsibility)

            STYLE RULES:
            - Be CONCISE - no verbose phrases like "No diesel outage after validation"
            - Use abridged language: "Community access resolved, DG powered" not "IHS FSE confirmed access issue due to community demands not met, DG was powered manually" or
                "Community access resolved, Injector serviced" not "IHS FSE confirmed access issue due to community demands not met, Injector was serviced and DG powered"
            - Separate multiple RCAs with " | " 
            - Focus on actionable issues and resolutions
            - Prioritize high-impact issues (long duration) over frequent minor ones

            Return ONLY a JSON object:
            {{
                "summary": "30-word brief summary here",
                "detailed_comments": "60-word detailed summary here",
                "bucket": "bucket_name_here"
            }}"""
        
        # Call LLM
        response = self._call_llm(prompt, temperature=0.3, max_tokens=400)
        
        if not response:
            return {
                "summary": f"{total_outages} outages, {duration_hours:.1f}hrs downtime. {major_rcas}",
                "detailed_comments": "AI analysis unavailable. Manual review required.",
                "bucket": "NR",
                "major_rcas": major_rcas,
                "provider_used": "Fallback"
            }
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
            
            result["major_rcas"] = major_rcas
            result["provider_used"] = self.current_provider
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "summary": f"{total_outages} outages, {duration_hours:.1f}hrs downtime. {major_rcas}",
                "detailed_comments": response[:300] if response else "Analysis error",
                "bucket": "NR",
                "major_rcas": major_rcas,
                "provider_used": self.current_provider
            }
    
    def batch_analyze_sites(self, sites_data: List[Tuple[str, pd.DataFrame]], 
                           progress_callback=None) -> List[Dict[str, Any]]:
        """
        Analyze multiple sites with progress tracking
        
        Args:
            sites_data: List of (ihs_site_id, outages_df) tuples
            progress_callback: Optional function(current, total, site_id) for progress updates
            
        Returns:
            List of analysis results
        """
        results = []
        total = len(sites_data)
        
        for idx, (site_id, outages_df) in enumerate(sites_data):
            if progress_callback:
                progress_callback(idx + 1, total, site_id)
            
            analysis = self.analyze_site_outages(outages_df, site_id)
            analysis["ihs_site_id"] = site_id
            results.append(analysis)
        
        return results


def validate_excel_file(df: pd.DataFrame) -> Tuple[bool, str, pd.DataFrame]:
    """
    Validate uploaded Excel file structure and clean data
    
    Returns:
        (is_valid, message, cleaned_df)
    """
    required_columns = {
        "Number": "Number",
        "Site ID": "IHS Site ID",
        "MTN ID": "MTN ID",
        "MTN Region": "MTN Region",
        "AIRTEL ID": "AIRTEL ID",
        "AIRTEL Region": "AIRTEL Region",
        "Outage Start Time": "Outage Start Time",
        "Outage End Time": "Outage End Time",
        "Outage Duration": "Outage Duration",
        "Maintenance Vendor": "Maintenance Vendor",
        "Primary Cause": "Primary Cause",
        "RCA 1": "RCA 1",
        "RCA 2": "RCA 2",
        "RCA 3": "RCA 3",
        "IHS Field Engineer": "IHS Field Engineer",
        "IHS RTO": "IHS RTO",
        "IHS Head of Operation": "IHS Head of Operation",
        "Resolution Comments": "Resolution Comments",
        "Resolution notes": "Resolution notes"
    }
    
    # Check if all required columns exist
    missing_cols = [col for col in required_columns.keys() if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}", df
    
    # Rename Site ID to IHS Site ID
    df = df.rename(columns={"Site ID": "IHS Site ID"})
    
    # Remove rows with null critical fields
    critical_fields = ["Number", "IHS Site ID", "Outage Start Time", "Primary Cause"]
    initial_count = len(df)
    df = df.dropna(subset=critical_fields)
    removed_count = initial_count - len(df)
    
    if removed_count > 0:
        print(f"Removed {removed_count} rows with null critical fields")
    
    # Convert datetime columns
    df["Outage Start Time"] = pd.to_datetime(df["Outage Start Time"], errors="coerce")
    df["Outage End Time"] = pd.to_datetime(df["Outage End Time"], errors="coerce")
    
    # Fill null Outage End Time with max value
    max_end_time = df["Outage End Time"].max()
    df["Outage End Time"] = df["Outage End Time"].fillna(max_end_time)
    
    # Recalculate Outage Duration (End - Start)
    df["Outage Duration"] = df["Outage End Time"] - df["Outage Start Time"]
    
    # Remove negative durations (data error)
    df = df[df["Outage Duration"] >= timedelta(0)]
    
    # Sort by duration (largest first)
    df = df.sort_values("Outage Duration", ascending=False)
    
    # Handle duplicates - keep larger MTTR
    duplicate_log = []
    duplicates = df[df.duplicated(subset=["Number"], keep=False)]
    
    if not duplicates.empty:
        for number in duplicates["Number"].unique():
            dup_rows = df[df["Number"] == number].sort_values("Outage Duration", ascending=False)
            kept = dup_rows.iloc[0]
            removed = dup_rows.iloc[1:]
            
            for _, row in removed.iterrows():
                duplicate_log.append({
                    "Number": number,
                    "IHS Site ID": row["IHS Site ID"],
                    "Removed_MTTR": row["Outage Duration"],
                    "Kept_MTTR": kept["Outage Duration"],
                    "Reason": "Kept higher MTTR record"
                })
        
        # Keep only first occurrence (already sorted by duration)
        df = df.drop_duplicates(subset=["Number"], keep="first")
    
    # Reset index
    df = df.reset_index(drop=True)
    
    message = f"File validated successfully. {len(df)} records loaded."
    if duplicate_log:
        message += f" Removed {len(duplicate_log)} duplicates (kept higher MTTR versions)."
    
    return True, message, df


if __name__ == "__main__":
    # Test the agent
    agent = EscalationAnalyzerAgent()
    
    # Sample test data
    test_df = pd.DataFrame({
        "Outage Duration": [timedelta(hours=2), timedelta(minutes=30), timedelta(hours=1)],
        "Primary Cause": ["Power", "Power", "Access"],
        "RCA 1": ["DG Fault", "DG Fault", "Community"],
        "RCA 2": ["Compression Loss", "Alternator", "Unpaid Rent"],
        "RCA 3": ["Compression Loss", "Charging Alternator", "Access Denied"],
        "Resolution Comments": ["DG replaced", "Alternator fixed", "Community engaged"],
        "Resolution notes": ["Site restored", "Monitoring", "Access granted"],
        "Outage Start Time": [datetime.now() - timedelta(days=5)] * 3,
        "Outage End Time": [datetime.now() - timedelta(days=5)] * 3
    })
    
    result = agent.analyze_site_outages(test_df, "IHS_OYO_0833A")
    print(json.dumps(result, indent=2, default=str))