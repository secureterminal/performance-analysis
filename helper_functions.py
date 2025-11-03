import pandas as pd

def apply_filters(df, filters: dict):
    """
    Applies multiple filters to a DataFrame.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame.
        filters (dict): Dictionary where keys are column names and values are:
                        - list/tuple for multi-select or range filters
                        - string for text contains
                        - single value for exact match
                        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    filtered_df = df.copy()

    for col, val in filters.items():
        if val is None or val == "" or val == []:
            continue
        if col == "Date" and isinstance(val, tuple) and len(val) == 2:
            filtered_df = filtered_df[(filtered_df["Date"] >= val[0]) & (filtered_df["Date"] <= val[1])]
        # Range filter (e.g. slider): (min, max)
        elif isinstance(val, (tuple, list)) and len(val) == 2 and all(isinstance(v, (int, float)) for v in val):
            filtered_df = filtered_df[filtered_df[col].between(val[0], val[1])]

        # List filter (e.g. multiselect)
        elif isinstance(val, (list, tuple)):
            filtered_df = filtered_df[filtered_df[col].isin(val)]

        # Text filter
        elif isinstance(val, str):
            filtered_df = filtered_df[filtered_df[col].str.contains(val, case=False, na=False)]

        # Exact match
        else:
            filtered_df = filtered_df[filtered_df[col] == val]

    return filtered_df




def human_format(num):
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:.2f}T"
    elif abs_num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:.0f}"
