import pandas as pd
import re
import math
from typing import Any


# 🔹 Add this where yo
# u define your tabs (append "Account Overview" to your existing list)
# Example:
# tabs = st.tabs(["Risk Analysis", "Liquidity", "Profitability", "Account Overview"])
# If you already have `tabs = st.tabs([...])`, just include "Account Overview" at the end and keep the variable name the same.

# Capture the last tab as the Account Overview tab
# *_, account_tab = st.tabs([*getattr(st.session_state, "TAB_LABELS", ["Risk Analysis", "Liquidity", "Profitability"]), "Account Overview"])

def main(Iteam_List_df: pd.DataFrame, Payment_History_df: pd.DataFrame)-> pd.DataFrame:
    import pandas as pd
    import streamlit as st

    # Heading (keep as in Excel)
    st.header("ACCOUNT OVERVIEW")

    # ---- Table structure (headings/subheadings exactly as in the Excel layout) ----
    # Row labels (left-most column) in the same order as the Excel:
    row_labels = [
        "OSC01",
        "Aerotek",
        "OCS03",
        "Aviation",
        "Aston Carter",
        "SJA01",
        "Actalent",
        "CE",
        "Scientific",
        "Services",
        "Actalent Canada",
        "Services_EASCA",          # Services - EASCA
        "Aerotek Canada",
        "Aston Carter Canada",
        "MLA/IEL",
        "Teksystems",
        "Tek Global",
        "Totals",            # totals row at the end
    ]

    num_rows_lables = [
        "OSC01",
        "OCS03",
        "Aviation",
        "SJA01",
        "CE",
        "Scientific",
        "Services",
        "Actalent Canada",
        "Services_EASCA",          # Services - EASCA
        "Aerotek Canada",
        "Aston Carter Canada",
        "MLA/IEL",
        "Teksystems",
        "Tek Global",
    ]

    # Column headers as shown in the Excel (ignore numeric values, keep header text)
    col_headers = ["Current", "1-30", "31-60", "61-90", "91-180", "181+",  "Total"]

    # Create an empty dataframe with the same shape; values will be supplied from your existing DataFrames
    account_overview_df = pd.DataFrame(
        data=[[""] * len(col_headers) for _ in row_labels],  # placeholders only
        index=row_labels,
        columns = col_headers
    )
    # def value, decimals=0):
    #     """
    #     Format a numeric value with commas (e.g. 31983000 -> '31,983,000').

    #     Args:
    #         value: int, float, or numeric string
    #         decimals: number of decimal places to display (default 0)

    #     Returns:
    #         str: formatted number with commas (e.g. '31,983,000' or '31,983,000.25')
    #     """
    #     try:
    #         if pd.isna(value):
    #             return "-"
    #         value = float(value)
    #         return f"{value:,.{decimals}f}"
    #     except (ValueError, TypeError):
    #         return str(value)
        
    # def  value) -> str:
    #     """Format financial values"""
    #     if pd.isna(value) or value is None:
    #         return "-"
    #     # Convert to thousands
    #     value = value / 1000
    #     if value < 0:
    #         return f"$({abs(value):,.0f})"
    #     else:
    #         return f"${value:,.0f}"



    # 👉 If you already compute values elsewhere, just assign them into `account_overview_df`
    # Example (pseudo):
    # account_overview_df.loc[:, col_headers] = your_values_df.loc[row_labels, col_headers].values
    # Assigning values to OSC01.
    account_overview_df.loc["OSC01", "Current"] = Iteam_List_df.query('Unit == "OCS01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["OSC01", "1-30"] = Iteam_List_df.query('Unit == "OCS01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["OSC01", "31-60"] = Iteam_List_df.query('Unit == "OCS01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["OSC01", "61-90"] = Iteam_List_df.query('Unit == "OCS01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["OSC01", "91-180"] =Iteam_List_df.query('Unit == "OCS01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["OSC01", "181+"] = Iteam_List_df.query('Unit == "OCS01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["OSC01", "Total"] = account_overview_df.loc["OSC01", col_headers[:-1]].sum().round(2)

    # Assigning values to OSC03.
    account_overview_df.loc["OCS03", "Current"] = Iteam_List_df.query('Unit == "OCS03" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["OCS03", "1-30"] = Iteam_List_df.query('Unit == "OCS03" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["OCS03", "31-60"] = Iteam_List_df.query('Unit == "OCS03" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["OCS03", "61-90"] = Iteam_List_df.query('Unit == "OCS03" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["OCS03", "91-180"] = Iteam_List_df.query('Unit == "OCS03" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["OCS03", "181+"] = Iteam_List_df.query('Unit == "OCS03" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["OCS03", "Total"] = account_overview_df.loc["OCS03", col_headers[:-1]].sum().round(2)

    # Assigning values to Avaiation.)
    account_overview_df.loc["Aviation", "Current"] = Iteam_List_df.query('Unit == "OAV01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aviation", "1-30"] = Iteam_List_df.query('Unit == "OAV01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aviation", "31-60"] = Iteam_List_df.query('Unit == "OAV01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aviation", "61-90"] = Iteam_List_df.query('Unit == "OAV01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aviation", "91-180"] = Iteam_List_df.query('Unit == "OAV01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aviation", "181+"] = Iteam_List_df.query('Unit == "OAV01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aviation", "Total"] = account_overview_df.loc["Aviation", col_headers[:-1]].sum().round(2)

    # Assigning values to SJA01.
    account_overview_df.loc["SJA01", "Current"] = Iteam_List_df.query('Unit == "SJA01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["SJA01", "1-30"] = Iteam_List_df.query('Unit == "SJA01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["SJA01", "31-60"] = Iteam_List_df.query('Unit == "SJA01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["SJA01", "61-90"] = Iteam_List_df.query('Unit == "SJA01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["SJA01", "91-180"] = Iteam_List_df.query('Unit == "SJA01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["SJA01", "181+"] = Iteam_List_df.query('Unit == "SJA01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["SJA01", "Total"] = account_overview_df.loc["SJA01", col_headers[:-1]].sum().round(2)

    # Assigning values to CE."{:,.0f}".format(
    account_overview_df.loc["CE", "Current"] = Iteam_List_df.query('Unit == "OCS02" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["CE", "1-30"] = Iteam_List_df.query('Unit == "OCS02" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["CE", "31-60"] = Iteam_List_df.query('Unit == "OCS02" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["CE", "61-90"] = Iteam_List_df.query('Unit == "OCS02" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["CE", "91-180"] = Iteam_List_df.query('Unit == "OCS02" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["CE", "181+"] = Iteam_List_df.query('Unit == "OCS02" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["CE", "Total"] = account_overview_df.loc["CE", col_headers[:-1]].sum().round(2)

    # Assigning values to Scientific.
    account_overview_df.loc["Scientific", "Current"] = Iteam_List_df.query('Unit == "ASC01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Scientific", "1-30"] = Iteam_List_df.query('Unit == "ASC01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Scientific", "31-60"] = Iteam_List_df.query('Unit == "ASC01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Scientific", "61-90"] = Iteam_List_df.query('Unit == "ASC01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Scientific", "91-180"] = Iteam_List_df.query('Unit == "ASC01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Scientific", "181+"] = Iteam_List_df.query('Unit == "ASC01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Scientific", "Total"] = account_overview_df.loc["Scientific", col_headers[:-1]].sum().round(2)

    # Assigning values to Services.
    account_overview_df.loc["Services", "Current"] = Iteam_List_df.query('Unit == "INP01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services", "1-30"] = Iteam_List_df.query('Unit == "INP01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services", "31-60"] = Iteam_List_df.query('Unit == "INP01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services", "61-90"] = Iteam_List_df.query('Unit == "INP01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services", "91-180"] = Iteam_List_df.query('Unit == "INP01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services", "181+"] = Iteam_List_df.query('Unit == "INP01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services", "Total"] = account_overview_df.loc["Services", col_headers[:-1]].sum().round(2)

    # Assigning values to Actalent Canada.
    account_overview_df.loc["Actalent Canada", "Current"] = Iteam_List_df.query('Unit == "CACOR" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Actalent Canada", "1-30"] = Iteam_List_df.query('Unit == "CACOR" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Actalent Canada", "31-60"] = Iteam_List_df.query('Unit == "CACOR" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Actalent Canada", "61-90"] = Iteam_List_df.query('Unit == "CACOR" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Actalent Canada", "91-180"] = Iteam_List_df.query('Unit == "CACOR" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Actalent Canada", "181+"] = Iteam_List_df.query('Unit == "CACOR" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Actalent Canada", "Total"] = account_overview_df.loc["Actalent Canada", col_headers[:-1]].sum().round(2)

    # Assigning values to Services_EASCA.
    account_overview_df.loc["Services_EASCA", "Current"] = Iteam_List_df.query('Unit == "EASCA" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services_EASCA", "1-30"] = Iteam_List_df.query('Unit == "EASCA" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services_EASCA", "31-60"] = Iteam_List_df.query('Unit == "EASCA" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services_EASCA", "61-90"] = Iteam_List_df.query('Unit == "EASCA" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services_EASCA", "91-180"] = Iteam_List_df.query('Unit == "EASCA" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services_EASCA", "181+"] = Iteam_List_df.query('Unit == "EASCA" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Services_EASCA", "Total"] = account_overview_df.loc["Services_EASCA", col_headers[:-1]].sum().round(2)

    # Assigning values to Aerotek Canada.
    account_overview_df.loc["Aerotek Canada", "Current"] = Iteam_List_df.query('Unit == "CAIND" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aerotek Canada", "1-30"] = Iteam_List_df.query('Unit == "CAIND" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aerotek Canada", "31-60"] = Iteam_List_df.query('Unit == "CAIND" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aerotek Canada", "61-90"] = Iteam_List_df.query('Unit == "CAIND" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aerotek Canada", "91-180"] = Iteam_List_df.query('Unit == "CAIND" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aerotek Canada", "181+"] = Iteam_List_df.query('Unit == "CAIND" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aerotek Canada", "Total"] = account_overview_df.loc["Aerotek Canada", col_headers[:-1]].sum().round(2)

    # Assigning values to Aston Carter Canada.
    account_overview_df.loc["Aston Carter Canada", "Current"] = Iteam_List_df.query('Unit == "CAAC1" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aston Carter Canada", "1-30"] = Iteam_List_df.query('Unit == "CAAC1" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aston Carter Canada", "31-60"] = Iteam_List_df.query('Unit == "CAAC1" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aston Carter Canada", "61-90"] = Iteam_List_df.query('Unit == "CAAC1" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aston Carter Canada", "91-180"] = Iteam_List_df.query('Unit == "CAAC1" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aston Carter Canada", "181+"] = Iteam_List_df.query('Unit == "CAAC1" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Aston Carter Canada", "Total"] = account_overview_df.loc["Aston Carter Canada", col_headers[:-1]].sum().round(2)

    # Assigning values to MLA/IEL.
    account_overview_df.loc["MLA/IEL", "Current"] = Iteam_List_df.query('Unit == "IELO1" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["MLA/IEL", "1-30"] = Iteam_List_df.query('Unit == "IELO1" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["MLA/IEL", "31-60"] = Iteam_List_df.query('Unit == "IELO1" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["MLA/IEL", "61-90"] = Iteam_List_df.query('Unit == "IELO1" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["MLA/IEL", "91-180"] = Iteam_List_df.query('Unit == "IELO1" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["MLA/IEL", "181+"] = Iteam_List_df.query('Unit == "IELO1" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["MLA/IEL", "Total"] = account_overview_df.loc["MLA/IEL", col_headers[:-1]].sum().round(2)

    # Assigning values to Teksystems.
    account_overview_df.loc["Teksystems", "Current"] = Iteam_List_df.query('Unit == "TEK01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Teksystems", "1-30"] = Iteam_List_df.query('Unit == "TEK01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Teksystems", "31-60"] = Iteam_List_df.query('Unit == "TEK01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Teksystems", "61-90"] = Iteam_List_df.query('Unit == "TEK01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Teksystems", "91-180"] = Iteam_List_df.query('Unit == "TEK01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Teksystems", "181+"] = Iteam_List_df.query('Unit == "TEK01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Teksystems", "Total"] = account_overview_df.loc["Teksystems", col_headers[:-1]].sum().round(2)

    # assigning values to Tek Global.
    account_overview_df.loc["Tek Global", "Current"] = Iteam_List_df.query('Unit == "TKC01" and `Days Late` <= 0')['Item Balance'].sum().round(2)
    account_overview_df.loc["Tek Global", "1-30"] = Iteam_List_df.query('Unit == "TKC01" and `Days Late` > 0 and `Days Late` <= 30')['Item Balance'].sum().round(2)
    account_overview_df.loc["Tek Global", "31-60"] = Iteam_List_df.query('Unit == "TKC01" and `Days Late` > 30 and `Days Late` <= 60')['Item Balance'].sum().round(2)
    account_overview_df.loc["Tek Global", "61-90"] = Iteam_List_df.query('Unit == "TKC01" and `Days Late` > 60 and `Days Late` <= 90')['Item Balance'].sum().round(2)
    account_overview_df.loc["Tek Global", "91-180"] = Iteam_List_df.query('Unit == "TKC01" and `Days Late` > 90 and `Days Late` <= 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Tek Global", "181+"] = Iteam_List_df.query('Unit == "TKC01" and `Days Late` > 180')['Item Balance'].sum().round(2)
    account_overview_df.loc["Tek Global", "Total"] = account_overview_df.loc["Tek Global", col_headers[:-1]].sum().round(2)

    # Assigning values to Totals.
    account_overview_df.loc["Totals", "Current"] = account_overview_df.loc[num_rows_lables, "Current"].sum().round(2)
    account_overview_df.loc["Totals", "1-30"] = account_overview_df.loc[num_rows_lables, "1-30"].sum().round(2)
    account_overview_df.loc["Totals", "31-60"] = account_overview_df.loc[num_rows_lables, "31-60"].sum().round(2)
    account_overview_df.loc["Totals", "61-90"] = account_overview_df.loc[num_rows_lables, "61-90"].sum().round(2)
    account_overview_df.loc["Totals", "91-180"] = account_overview_df.loc[num_rows_lables, "91-180"].sum().round(2)
    account_overview_df.loc["Totals", "181+"] = account_overview_df.loc[num_rows_lables, "181+"].sum().round(2)
    account_overview_df.loc["Totals", "Total"] = account_overview_df.loc[num_rows_lables, "Total"].sum().round(2)

    # Only format numeric values, leave strings as they are
    account_overview_df = account_overview_df.applymap(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)



    
    # ---------- invoice paid-----------
    # L3M_invoices_paid = Payment_History_df[pd.to_datetime(Payment_History_df['Payment Date']) >= (pd.to_datetime('08-09-2024') - pd.DateOffset(months=3))]['Invoice Number'].nunique()
    payment_history = pd.DataFrame(columns=["Payment Date"])

    payment_history["Payment Date"] = pd.to_datetime(Payment_History_df['Payment Date'], errors='coerce')

    # F5 is your reference date (as a pandas Timestamp or parseable string)
    # example: f5 = pd.Timestamp('2025-09-01')
    cutoff_90 = pd.to_datetime('08-09-2024') - pd.Timedelta(days=91)

    L3M_invoices_paid = (payment_history['Payment Date'] >= cutoff_90).sum()

    #LTM Invoice paid
    cutoff_365 = pd.to_datetime('08-09-2024') - pd.Timedelta(days=365)
    LTM_invoice_paid  = (payment_history['Payment Date'] >= cutoff_365).sum()

    Invoice_paid_2006 = Payment_History_df['Amt Applied to Customer'].count()

    # ----------------$paid amount-----------
    # Ensure Payment Date is in datetime format
    Payment_History_df['Payment Date'] = pd.to_datetime(Payment_History_df['Payment Date'], errors="coerce")

    # Define cutoff date (last 91 days from today)
    cutoff_paid_90 = pd.to_datetime('08-09-2024') - pd.Timedelta(days=91)

    # Filter and sum
    L3M_Paid_90 = Payment_History_df.loc[Payment_History_df["Payment Date"] >= cutoff_paid_90, "Amt Applied to Customer"].sum()

    cutoff_paid_365 = pd.to_datetime('08-09-2024') - pd.Timedelta(days=365)

    # Filter and sum
    LTM_Paid_365 = Payment_History_df.loc[Payment_History_df["Payment Date"] >= cutoff_paid_365, "Amt Applied to Customer"].sum()

    # Amount_paid_2006
    Amount_paid_2006 = Payment_History_df["Amt Applied to Customer"].sum()

    # -----------Average DPD----------------

    L3L_averageDPD__90 = Payment_History_df.loc[Payment_History_df["Payment Date"] >= cutoff_paid_90, "Days Past Due"].mean()
    LTM_averageDPD_365 = Payment_History_df.loc[Payment_History_df["Payment Date"] >= cutoff_paid_365, "Days Past Due"].mean()
    Average_DPD_2006 = Payment_History_df["Days Past Due"].mean()


    # Total credits
    total_credits = Iteam_List_df.query('`Item Balance` < 0')['Item Balance'].sum()


    # ---------------LAst Payment and Amount----------------
    
    df = Payment_History_df.copy()

    # 1) Parse dates safely
    df['Payment Date'] = pd.to_datetime(df['Payment Date'], errors='coerce')  # add dayfirst=True if needed

    # 2) Parse amounts safely (handles '$', commas, etc. if present)
    df['Amt Applied to Customer'] = pd.to_numeric(
        df['Amt Applied to Customer'], errors='coerce'
    )

    # 3) Find the last payment date (skip NaT)
    last_ts = df['Payment Date'].max()

    if pd.isna(last_ts):
        Last_Payment = pd.NaT
        Last_Payment_Date_Amount = 0.0
    else:
        # If you care about exact timestamp:
        # mask = df['Payment Date'].eq(last_ts)

        # If you care about the calendar day (ignores time-of-day):
        mask = df['Payment Date'].dt.normalize().eq(last_ts.normalize())

        Last_Payment = last_ts
        Last_Payment_Date_Amount = df.loc[mask, 'Amt Applied to Customer'].sum()


    # Net terms
    Net_terms = Payment_History_df['Terms'].iloc[0]
    

    # Render the table (structure-only; numbers come from your dataframes)
    st.dataframe(
        account_overview_df,
        use_container_width=True,
        hide_index=False
    )

    # ---- Optional: small summary panel placeholders exactly as labels in the Excel footer ----
    # (Keep labels; you will populate values from your own dataframes)
    with st.container():
        # st.subheader("Account Summary")

        # Header row
        h1, h2, h3, h4, h5 = st.columns([1.2, 1, 1, 1.2, 1.6])
        h1.markdown(" ")  # empty leading cell
        h2.markdown("**L3M**")
        h3.markdown("**LTM**")
        h4.markdown("**Since 2/17/2006**")
        with h5:
            st.markdown("**Last Payment Date:**")
            st.markdown("05-08-2024")

        # Row: Invoices Paid
        c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1.2, 1.6])
        c1.markdown("**Invoices Paid**")
        c2.markdown(L3M_invoices_paid)
        c3.markdown(LTM_invoice_paid)
        c4.markdown(Invoice_paid_2006)
        c5.markdown("**Amount:** " f"${Last_Payment_Date_Amount}")

        # Row: $ Paid
        c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1.2, 1.6])
        c1.markdown("**$ Paid**")
        c2.markdown(L3M_Paid_90)
        c3.markdown(LTM_Paid_365)
        c4.markdown(Amount_paid_2006)
        c5.markdown("**Net Terms:**  " f"{Net_terms}")

        # Row: Average DPD
        c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1.2, 1.6])
        c1.markdown("**Average DPD**")
        c2.markdown(L3L_averageDPD__90)
        c3.markdown(LTM_averageDPD_365)
        c4.markdown(Average_DPD_2006)
        c5.markdown("**Total Credits:** " f"${total_credits}")
    return account_overview_df
 
    
