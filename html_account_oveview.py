import pandas as pd
import logging
from Account_Overview import main as account_overview_main


def account_overview_to_html(item_list_df:pd.DataFrame, payment_history_df:pd.DataFrame)->str:
    account_overview_html = ""
    if item_list_df is not None and payment_history_df is not None:

        try:
            # Create a StringIO buffer to capture the Streamlit output
            from contextlib import redirect_stdout
            import sys
            
            # Create a custom capture for the Account Overview output
            # Since Account_Overview.main() uses st.dataframe and st.markdown,
            # we need to extract the dataframe directly
            
            # Get the account_overview_df from the function
            # We'll need to modify the approach to get the actual DataFrame
            
            # Import the row_labels and col_headers from Account_Overview
            row_labels = [
                "OSC01", "Aerotek", "OCS03", "Aviation", "Aston Carter", 
                "SJA01", "Actalent", "CE", "Scientific", "Services",
                "Actalent Canada", "Services_EASCA", "Aerotek Canada",
                "Aston Carter Canada", "MLA/IEL", "Teksystems", "Tek Global", "Totals"
            ]
            col_headers = ["Current", "1-30", "31-60", "61-90", "91-180", "181+", "Total"]
            
            # Create empty dataframe structure
            account_overview_df = account_overview_main(item_list_df, payment_history_df)
            
            # Populate the dataframe using the same logic from Account_Overview.py
            # (This is a simplified version - you'd need to copy all the calculation logic)
            # For now, we'll call the main function and try to extract the data
            
            # Since Account_Overview.main() doesn't return the DataFrame,
            # we need to recreate the calculations here for the HTML report
            
            # Generate the HTML table
            account_overview_table = account_overview_df.to_html(
                index=True, 
                escape=False, 
                na_rep="",
                classes="table",
                table_id="account-overview-table"
            )
            
            # Calculate summary metrics (from Account_Overview.py)
            payment_history = pd.DataFrame(columns=["Payment Date"])
            payment_history["Payment Date"] = pd.to_datetime(payment_history_df['Payment Date'], errors='coerce')
            
            cutoff_90 = pd.to_datetime('08-09-2024') - pd.Timedelta(days=91)
            cutoff_365 = pd.to_datetime('08-09-2024') - pd.Timedelta(days=365)
            
            L3M_invoices_paid = (payment_history['Payment Date'] >= cutoff_90).sum()
            LTM_invoice_paid = (payment_history['Payment Date'] >= cutoff_365).sum()
            Invoice_paid_2006 = payment_history_df['Amt Applied to Customer'].count()
            
            payment_history_df['Payment Date'] = pd.to_datetime(payment_history_df['Payment Date'], errors="coerce")
            L3M_Paid_90 = payment_history_df.loc[payment_history_df["Payment Date"] >= cutoff_90, "Amt Applied to Customer"].sum().round(0)
            LTM_Paid_365 = payment_history_df.loc[payment_history_df["Payment Date"] >= cutoff_365, "Amt Applied to Customer"].sum().round(0)
            Amount_paid_2006 = payment_history_df["Amt Applied to Customer"].sum().round(0)
            
            L3L_averageDPD__90 = payment_history_df.loc[payment_history_df["Payment Date"] >= cutoff_90, "Days Past Due"].mean().round(0)
            LTM_averageDPD_365 = payment_history_df.loc[payment_history_df["Payment Date"] >= cutoff_365, "Days Past Due"].mean().round(0)
            Average_DPD_2006 = payment_history_df["Days Past Due"].mean().round(0)
            
            total_credits = item_list_df.query('`Item Balance` < 0')['Item Balance'].sum()
            
            # Get last payment info
            df = payment_history_df.copy()
            df['Payment Date'] = pd.to_datetime(df['Payment Date'], errors='coerce')
            df['Amt Applied to Customer'] = pd.to_numeric(df['Amt Applied to Customer'], errors='coerce')
            last_ts = df['Payment Date'].max()
            
            if pd.isna(last_ts):
                Last_Payment = "N/A"
                Last_Payment_Date_Amount = 0.0
            else:
                mask = df['Payment Date'].dt.normalize().eq(last_ts.normalize())
                Last_Payment = last_ts.strftime('%m-%d-%Y')
                Last_Payment_Date_Amount = df.loc[mask, 'Amt Applied to Customer'].sum().round(0)
            
            Net_terms = payment_history_df['Terms'].iloc[0] if not payment_history_df.empty else "N/A"
            
            # Build the HTML for Account Overview section
            account_overview_html = f"""
            <h3>Account Overview</h3>
            {account_overview_table}
            
            <h4>Account Summary</h4>
            <table class="table" style="width: 100%; margin-top: 20px;">
                <thead>
                    <tr>
                        <th></th>
                        <th>L3M</th>
                        <th>LTM</th>
                        <th>Since 2/17/2006</th>
                        <th>Additional Info</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Invoices Paid</strong></td>
                        <td>{L3M_invoices_paid}</td>
                        <td>{LTM_invoice_paid}</td>
                        <td>{Invoice_paid_2006}</td>
                        <td><strong>Last Payment Date:</strong> {Last_Payment}</td>
                    </tr>
                    <tr>
                        <td><strong>$ Paid</strong></td>
                        <td>${L3M_Paid_90}</td>
                        <td>${LTM_Paid_365}</td>
                        <td>${Amount_paid_2006}</td>
                        <td><strong>Amount:</strong> ${Last_Payment_Date_Amount}</td>
                    </tr>
                    <tr>
                        <td><strong>Average DPD</strong></td>
                        <td>{L3L_averageDPD__90}</td>
                        <td>{LTM_averageDPD_365}</td>
                        <td>{Average_DPD_2006}</td>
                        <td><strong>Net Terms:</strong> {Net_terms}</td>
                    </tr>
                    <tr>
                        <td colspan="4"></td>
                        <td><strong>Total Credits:</strong> ${total_credits}</td>
                    </tr>
                </tbody>
            </table>
            """
        
            
        except Exception as e:
            # logger.warning(f"Could not generate Account Overview for report: {e}")
            account_overview_html = "<h3>Account Overview</h3><p>Account Overview data not available</p>"
        return account_overview_html
    else:
        account_overview_html = "<h3>Account Overview</h3><p>Item List and Payment History files not uploaded</p>"
