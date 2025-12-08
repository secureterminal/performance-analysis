"""
Optimized LLM Prompt for Outage Analysis
Based on training data patterns
"""

def generate_analysis_prompt(ihs_site_id, site_outages_df, total_outages, duration_hours, 
                            rca_breakdown, resolution_comments, resolution_notes):
    """
    Generate optimized prompt for outage analysis that matches training data format
    """
    
    prompt = f"""You are analyzing site outages for {ihs_site_id}. Generate a professional outage summary following the exact style shown in the examples below.

SITE STATISTICS:
- Total Outages: {total_outages}
- Total Downtime: {duration_hours:.2f} hours
- Period: {site_outages_df['Outage Start Time'].min()} to {site_outages_df['Outage Start Time'].max()}

RCA BREAKDOWN (by frequency and duration):
{rca_breakdown.to_string(index=False)}

RESOLUTION COMMENTS:
{chr(10).join(resolution_comments[:30])}

RESOLUTION NOTES:
{chr(10).join(resolution_notes[:30])}

STYLE EXAMPLES (Learn from these):

Example 1:
Input: "DG high temperature alarm due low coolant level, coolant was added (No diesel outage after validation)"
Output: "DG high temperature, coolant added"

Example 2:
Input: "IHS FSE confirmed access issue due to community demands not met, DG was powered manually"
Output: "Community access issue resolved, DG powered"

Example 3:
Input: "Failed charging alternator was excited (No diesel outage after validation)"
Output: "Failed charging alternator was excited"

Example 4:
Input: "Access issue due to site located at high risk area with security concerns. RCA: Cut charging alternator cable was fixed"
Output: "High-risk area, cut charging alternator cable fixed"

Example 5:
Input: "Faulty injector pump on main DG; MDG was deployed and power was restored"
Output: "Faulty injector pump, MDG deployed"

Example 6:
Input: "DG loss compression 20KV was deployed (No diesel outage after validation)"
Output: "DG loss compression, 20kVA DG deployed"

Example 7:
Input: "Suspected passive issue, Awaiting RCA from FSE"
Output: "LLM should skip these kind of feedback that includes suspicion, we need to be 100% sure"

Example 8:
Input: "Faulty crankshaft, kick starter and hooked cylinder was worked on"
Output: "Faulty crankshaft, kick starter and hooked cylinder was worked on"

Example 9:
Input: "Site experienced fuel outage caused by faulty lift pump. Field team visited site and worked on the lift pump to restore normal operation."
Output: "Faulty lift pump, lift pump repaired"

CRITICAL RULES:
1. ISSUE IDENTIFICATION:
   - State the PRIMARY problem clearly (e.g., "DG lost compression", "Faulty alternator", "Community access denied")
   - Mention SECONDARY issues if multiple occurred (e.g., "High temperature | Weak BUB")
   - Prioritize issues by DURATION impact, not frequency

2. ACTION TAKEN:
   - State what was REPLACED/DEPLOYED: "DG deployed", "Alternator replaced", "BUB installed"
   - State what was REPAIRED/FIXED: "Injector fixed", "Cable repaired", "Leak sealed", "Fuel line flushed", "Solenoid replaced", "Water drained from tank"
   - State what was RESOLVED: "Access restored", "Power restored", "Community engaged"

3. BREVITY PATTERNS:
   - Remove: "No diesel outage after validation"
   - Remove: "IHS FSE confirmed"
   - Remove: "was worked on" → just state what was done
   - Remove: "due to" → just state the issue
   - Change: "was powered manually" → "DG powered"
   - Change: "was deployed to power the site" → "deployed"
   - Avoid phrases such as "Site experienced"

4. SKIP UNCERTAIN CASES:
   - If "suspected", "awaiting" → skip
   - If no clear resolution → respond: skip
   - Be 100% sure before summarizing

5. MULTIPLE ISSUES FORMAT:
   - Use " | " to separate: "DG compression loss | Alternator fault | BUB depleted"
   - Order by severity: High-impact first, then minor issues

BUCKET ASSIGNMENT RULES:

**Infra** (Asset-level replacement):
- DG deployed, replaced, installed
- Rectifier deployed, replaced
- BUB deployed, installed, replaced
- AC unit replaced, installed
- Inverter deployed
- DCDB replacement
Keywords: "deployed", "DG", "rectifier", "BUB", "battery", "AC", "inverter"

**NR** (Non-routine repairs/parts):
- Injector repaired, replaced, serviced
- Alternator fixed, replaced
- Solenoid replaced
- Cable repairs (cut, damaged)
- Shelter repairs (major)
- Module replaced
- Breaker replaced
- Contactor replaced
- Gasket replaced
- Any PART of an asset (not whole asset)
Keywords: "injector", "alternator", "solenoid", "cable", "module", "repaired", "fixed", "serviced"

**Diesel** (Fuel-related):
- Diesel outage (not "No diesel outage")
- Fuel line blocked
- Diesel quality issues
- Water in diesel
- Fuel pump issues
- Tank leakage
Keywords: "diesel", "fuel", "blocked line", "water ingress"

**Security** (Theft/Access):
- Theft, vandalism
- Equipment stolen
- Security concerns
- Bandits issues
Keywords: "theft", "stolen", "vandalized", "access denied"

**Access Issue**:
- Access denied by community
- Landlord issues blocking access
- Lease expired
- Rent unpaid
- Community demands (CSR, rent share)
Keywords: "access denied", "community blocked", "rent", "landlord"

**Legal** (Lease/Land):
- Land disputes
- Legal proceedings
Keywords: "lease","legal", "community demands"

**TX Issue/Active** (Customer equipment):
- Transmission equipment failure
- Customer active equipment
- BSC/RNC issues
- Backhaul issues
- No outage found (not IHS-related)
Keywords: "transmission", "TX", "active", "customer equipment", "not found"

OUTPUT FORMAT:
Return ONLY a valid JSON object with these exact keys:

{{
    "summary": "Brief issue + action taken (max 30 words)",
    "detailed_comments": "Detailed breakdown of what was done to close (max 60 words)",
    "bucket": "One of: Infra, NR, Diesel, Security, Legal, TX Issue, Active"
}}

EXAMPLE OUTPUTS:

Input: "DG high temp, coolant added | Failed alternator excited | DG was powered"
Output:
{{
    "summary": "DG high temperature due to low coolant. Coolant added, failed alternator excited, DG powered.",
    "detailed_comments": "Site experienced DG high temperature alarm caused by low coolant levels. Coolant was added to restore normal operating temperature. Additionally, a failed charging alternator was identified and excited. DG was manually powered to restore services.",
    "bucket": "NR"
}}

Input: "Access denied by community, DG powered manually, community engagement ongoing"
Output:
{{
    "summary": "Community access issue resolved temporarily. DG powered.",
    "detailed_comments": "Access to site was denied by community due to unmet demands. Field team engaged community leadership. DG was powered manually as temporary access granted. Formal community engagement process initiated to resolve underlying concerns and restore normal access.",
    "bucket": "Access"
}}

Input: "DG loss compression, 20kVA DG deployed"
Output:
{{
    "summary": "DG lost compression. 20kVA replacement DG deployed and site restored.",
    "detailed_comments": "Main DG lost compression. Site was powered using backup battery. A 20kVA replacement DG was deployed to site. Power fully restored and site under monitoring.",
    "bucket": "Infra"
}}

Input: "Faulty injector pump serviced, DG restored"
Output:
{{
    "summary": "Faulty injector pump. Injector serviced and DG restored.",
    "detailed_comments": "Diesel generator experienced repeated failures due to faulty injector pump. Technician dispatched to siteand serviced injector. Site under monitoring.",
    "bucket": "NR"
}}

NOW ANALYZE THE PROVIDED SITE DATA AND GENERATE YOUR RESPONSE:
"""
    
    return prompt


# ============================================
# ALTERNATIVE: Few-Shot Learning Approach
# ============================================

def generate_fewshot_prompt(ihs_site_id, site_outages_df, total_outages, duration_hours,
                           rca_breakdown, resolution_comments, resolution_notes):
    """
    Alternative approach using few-shot learning with real examples
    """
    
    # Extract top 3 RCAs
    top_rcas = rca_breakdown.head(3)
    rca_text = " | ".join([f"{row['RCA 3']}" for _, row in top_rcas.iterrows()])
    
    # Combine resolution info
    all_resolutions = list(resolution_comments[:5]) + list(resolution_notes[:5])
    resolution_text = " | ".join([r for r in all_resolutions if r and len(r) > 10])
    
    prompt = f"""Analyze site {ihs_site_id} outages and create professional summary.

DATA:
Outages: {total_outages} | Downtime: {duration_hours:.1f}hrs
Main Issues: {rca_text}
Actions: {resolution_text[:500]}

Learn from these REAL examples:

1. Raw: "DG high temperature alarm due low coolant level, coolant was added (No diesel outage after validation)"
   Summary: "DG high temperature, coolant added"
   Details: "Coolant was added to resolve DG high temperature"
   Bucket: NR

2. Raw: "Community demands not met, DG was powered manually"
   Summary: "Community access issue resolved, DG powered"  
   Details: "Access issue due to high risk area, DG powered manually"
   Bucket: Security

3. Raw: "Failed charging alternator was excited (No diesel outage after validation)"
   Summary: "Failed charging alternator was excited"
   Details: "Failed charging alternator was excited"
   Bucket: NR

4. Raw: "DG loss compression 20KV was deployed (No diesel outage after validation)"
   Summary: "DG loss compression, 20kVA DG deployed"
   Details: "DG lost compression, site restored on solar"
   Bucket: Infra

5. Raw: "Access issue due to site located at high risk area with security concerns. RCA: Cut charging alternator cable was fixed"
   Summary: "High-risk area, cut charging alternator cable fixed"
   Details: "Access issue due to high risk area, Cut charging alternator cable was fixed"
   Bucket: Security

6. Raw: "Faulty injector pump on main DG; MDG was deployed and power was restored"
   Summary: "Faulty injector pump, MDG deployed"
   Details: "Faulty injector pump, MDG deployed"
   Bucket: NR

7. Raw: "HFR PE confirmed Land lord access issue due to unpaid rent, DG was powered manually"
   Summary: "Landlord access issue due to unpaid rent resolved"
   Details: "Land lord access issue due to unpaid rent was resolved"
   Bucket: Legal

8. Raw: "POMC Site is powered from EDIABO. (No diesel outage after validation)"
   Summary: "Site powered from ED1ABO"
   Details: "POMC Site is powered from ED1ABO"
   Bucket: NR

RULES:
✓ Remove "(No diesel outage after validation)"
✓ Remove "IHS FSE confirmed"
✓ State issue + action taken
✓ Keep under 30 words (summary), 60 words (details)
✓ Use "|" to separate multiple issues
✓ Prioritize by duration impact

BUCKETS:
- Infra: DG/rectifier/BUB/AC deployment (whole asset)
- NR: Injector/alternator/cable/parts repair (parts)
- Diesel: Fuel issues, blocked line, water in diesel
- Security: Theft, access denial, vandalism
- Legal: Lease, rent, land disputes
- TX Issue: Customer equipment, not IHS fault

Return JSON:
{{"summary":"...","detailed_comments":"...","bucket":"..."}}"""
    
    return prompt


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    # Example usage
    sample_prompt = generate_analysis_prompt(
        ihs_site_id="IHS_OYO_0833A",
        site_outages_df=None,  # Pass your actual dataframe
        total_outages=5,
        duration_hours=12.5,
        rca_breakdown=None,  # Pass your actual breakdown
        resolution_comments=["DG high temp, coolant added", "Failed alternator excited"],
        resolution_notes=["DG powered manually", "Site restored"]
    )
    
    print(sample_prompt)