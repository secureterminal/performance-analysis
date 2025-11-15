# calcs.py
import pandas as pd
import datetime
import numpy as np
import streamlit as st

@st.cache_data
def get_sheets(file):
    """Reads and preprocesses all relevant Excel sheets."""
    sheets = pd.read_excel(
        file,
        sheet_name=["outages", "db", "pa", "rna", "tch"],
        engine="openpyxl"
    )

    # Extract sheets
    df_init = sheets["outages"]
    db_init = sheets["db"]
    pa_init = sheets["pa"]
    rna_init = sheets["rna"]
    tch_init = sheets["tch"]

    # Ensure all column names are strings
    df_init.columns = df_init.columns.astype(str)
    db_init.columns = db_init.columns.astype(str)
    pa_init.columns = pa_init.columns.astype(str)

    # --- Clean DB ---
    db_full = db_init.copy()

    db_1 = db_full.copy()[[
        "IHS Site ID", "Tenants On Site", "IHS Site Priority", "Zone", "Region",
        "State", "EFS Name", "RTO Name", "Head, Field Service", "SBC"
    ]]

    db = db_1.drop_duplicates(subset=["IHS Site ID"], keep="first").reset_index(drop=True)
    db_full["tenant_and_id"] = db_full["Tenant Name"].astype(str) + "_" + db_full["Tenant ID"].astype(str)

    # --- Clean Outages ---
    # Convert Date column to datetime
    df_init["Date"] = pd.to_datetime(df_init["Date"], errors="coerce")
    
    # Process Duration
    df_init["Duration"] = df_init["Duration"].apply(
        lambda x: datetime.timedelta(hours=x.hour, minutes=x.minute, seconds=x.second)
        if isinstance(x, datetime.time)
        else x
    )

    df_init["Duration_timedelta"] = pd.to_timedelta(df_init["Duration"], errors="coerce")
    df_init = df_init.drop(columns=["Tenants On Site"], errors="ignore")

    df_init = pd.merge(df_init, db, on="IHS Site ID", how="left")
    df_init = df_init[df_init["Year"] == datetime.date.today().year]

    # --- Clean PA ---
    pa_init = pa_init.rename(columns={"Site ID": "IHS Site ID"})
    
    # Melt the dataframe - date columns become row values
    pa_init = pa_init.melt(id_vars=["IHS Site ID"], var_name="Date", value_name="PA")
    
    # Convert the Date column (which contains former column headers) to datetime
    # Try different approaches based on the data type
    print("PA Date column type before conversion:")
    print(pa_init["Date"].dtype)
    if pd.api.types.is_datetime64_any_dtype(pa_init["Date"]):
        # Already datetime from Excel
        pa_init["Date"] = pd.to_datetime(pa_init["Date"])
    else:
        # It's a string or object, parse it
        # First try without format to let pandas infer
        pa_init["Date"] = pd.to_datetime(pa_init["Date"], errors="coerce")
        
        # If all failed, try with explicit format
        if pa_init["Date"].isna().all():
            pa_init["Date"] = pd.to_datetime(pa_init["Date"], format="%d/%m/%Y", errors="coerce")

    # Process PA values
    pa_init["PA"] = pa_init["PA"].replace("-", np.nan)
    pa_init["PA"] = pd.to_numeric(pa_init["PA"], errors="coerce").round(2)

    # Downcast for memory efficiency
    pa_init["IHS Site ID"] = pa_init["IHS Site ID"].astype("category")
    pa_init["PA"] = pa_init["PA"].astype("float32")
    # Keep Date as datetime64[ns], NOT category

    return df_init, pa_init, db, db_full
