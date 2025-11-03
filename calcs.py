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

    # --- Clean Outages ---
    df_init["Date"] = pd.to_datetime(df_init["Date"], format="%d/%m/%Y", errors="coerce").dt.date
    df_init["Duration"] = df_init["Duration"].apply(
        lambda x: datetime.timedelta(hours=x.hour, minutes=x.minute, seconds=x.second)
        if isinstance(x, datetime.time)
        else x
    )
    df_init["Duration_timedelta"] = pd.to_timedelta(df_init["Duration"], errors="coerce")
    df_init = df_init.drop(columns=["Tenants On Site"], errors="ignore")

    db = db_init.copy()[[
        "IHS Site ID", "Tenants On Site", "IHS Site Priority", "Zone", "Region",
        "State", "EFS Name", "RTO Name", "Head, Field Service", "SBC"
    ]]
    df_init = pd.merge(df_init, db, on="IHS Site ID", how="left")
    df_init = df_init[df_init["Year"] == datetime.date.today().year]

    # --- Clean PA ---
    pa_init = pa_init.rename(columns={"Site ID": "IHS Site ID"})
    pa_init = pa_init.melt(id_vars=["IHS Site ID"], var_name="Date", value_name="PA")
    pa_init["Date"] = pd.to_datetime(pa_init["Date"], format="%d/%m/%Y", errors="coerce").dt.date
    pa_init["PA"] = pd.to_numeric(pa_init["PA"].replace("-", np.nan), errors="coerce").round(2)

    # Downcast for memory efficiency
    pa_init["IHS Site ID"] = pa_init["IHS Site ID"].astype("category")
    pa_init["Date"] = pa_init["Date"].astype("category")
    pa_init["PA"] = pa_init["PA"].astype("float32")

    return df_init, pa_init, db

































































































    # print(pa_df)
    # st.dataframe(pa_df)
# # === Load Data ===
# # ---- File upload Logic ----
# df_init, pa_init, db_init = "", "", ""

# if "file_uploaded" not in st.session_state:
#     st.session_state.file_uploaded = False

# if "uploaded_file_1" not in st.session_state:
#     st.session_state.uploaded_file_1 = False

# if st.session_state.file:
#     file = st.session_state.file
#     st.write(file)
#     df_init = pd.read_excel(file, sheet_name="outages", engine="openpyxl")
#     db_init = pd.read_excel(file, sheet_name="db", engine="openpyxl")
#     pa_init = pd.read_excel(file, sheet_name="pa", engine="openpyxl")
#     rna_init = pd.read_excel(file, sheet_name="rna", engine="openpyxl")
#     tch_init = pd.read_excel(file, sheet_name="tch", engine="openpyxl")
#     # else:
#     #     @st.cache_data
#     #     def load_data():
#     #         file_path = "assets/All Outages.csv"
#     #         file_path2 = "assets/DB.xlsx"
#     #         file_path3 = "assets/pa.xlsx"

#     #         df_init = pd.read_csv(file_path)
#     #         db_init = pd.read_excel(file_path2, sheet_name="Sheet1")
#     #         pa_init = pd.read_excel(file_path3, sheet_name="pa")
#     #         rna_init = pd.read_excel(file_path3, sheet_name="rna")
#     #         tch_init = pd.read_excel(file_path3, sheet_name="tch")
#     #         return df_init, db_init, pa_init

#     #     df_init,db_init, pa_init = load_data()


#     # Ensure correct datetime and duration types
#     df_init["Date"] = pd.to_datetime(df_init["Date"], format="%d/%m/%Y", errors="coerce").dt.date

#     df_init["Duration_timedelta"] = pd.to_timedelta(df_init["Duration"], errors="coerce")
#     df_init = df_init.drop(columns=["Tenants On Site"])


#     # select specific columns from DB
#     db = db_init.copy()
#     db = db[["IHS Site ID", "Tenants On Site", "IHS Site Priority", "Zone", "Region", "State", "EFS Name", "RTO Name",\
#             "Head, Field Service", "SBC"]]

#     # Merge df and db using column "IHS Site ID"
#     df_init = pd.merge(df_init, db, on="IHS Site ID", how="left")

#     df_init = df_init[df_init['Year'] == datetime.date.today().year]



#     # Rename "New ID" to "IHS Site ID"
#     pa_init = pa_init.rename(columns={"Site ID": "IHS Site ID"})
#     # st.write(pa_init.columns)

#     pa_init = pa_init.melt(
#         id_vars=["IHS Site ID"],       # Columns to keep fixed
#         var_name="Date",             # Name for the new column of variable names
#         value_name="PA"             # Name for the new column of values
#     )
#     pa_init["Date"] = pd.to_datetime(pa_init["Date"], format="%d/%m/%Y", errors="coerce").dt.date

#     pa_init['PA'] = pd.to_numeric(pa_init['PA'].replace('-', np.nan), errors='coerce', downcast='float')
#     pa_init['PA'] = pa_init['PA'].round(2)


#     pa_init["IHS Site ID"] = pa_init["IHS Site ID"].astype("category")
#     pa_init["Date"] = pa_init["Date"].astype("category")
#     pa_init["PA"] = pa_init["PA"].astype("category")

#     # Merge pa_init and db using column "IHS Site ID"
#     # pa_init = pd.merge(pa_init, db, on="IHS Site ID", how="left")

#     # Ensure correct datetime
#     pa_init["Date"] = pd.to_datetime(pa_init["Date"], format="%d/%m/%Y", errors="coerce").dt.date


#     # st.write(pa_init.shape)
#     # st.write(pa_init.memory_usage(deep=True).sum() / 1024**2)  # in MB)


#     # ===============================
#     # 1️⃣  SELECT DF
#     # ===============================

#     df = df_init.copy()
#     pa_df = pa_init.copy()


#     # print(pa_df)
#     # st.dataframe(pa_df)