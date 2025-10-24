import requests
import pandas as pd
import json
import numpy as np

class Financial_api:
    
    def __init__(self, ticker):
        self.ticker = ticker
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/117.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nasdaq.com/",
            "Origin": "https://www.nasdaq.com"
        }
    
    def _ordered_header_values(self, headers_dict):
        """
        Convert headers dict like {'value1': 'Period Ending:', 'value2': '12/31/2024', ...}
        into an ordered list of header values sorted by the numeric suffix.
        """
        if not isinstance(headers_dict, dict):
            return []
        try:
            items = sorted(headers_dict.items(), key=lambda x: int(x[0].replace('value', '')))
        except Exception:
            # Fallback to insertion order if keys are not in expected format
            items = list(headers_dict.items())
        return [v for k, v in items]
    
    def fetch_financial_data(self, frequency=1):
        """
        Fetch financial data from NASDAQ API for a given ticker.
        
        Args:
            frequency (int): 1 for annual, 2 for quarterly
        
        Returns:
            dict: JSON response data or None if request fails
        """
        url = f"https://api.nasdaq.com/api/company/{self.ticker}/financials?frequency={frequency}"
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Request failed with status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def _clean_numeric_value(self, value):
        """
        Clean financial values by removing formatting and converting to numeric.
        """
        if pd.isna(value) or value == '' or value == 'N/A':
            return np.nan
        
        # Convert to string and clean
        value_str = str(value)
        
        # Handle parentheses for negative numbers
        if '(' in value_str:
            value_str = '-' + value_str.replace('(', '').replace(')', '')
        
        # Remove common formatting
        value_str = value_str.replace('$', '').replace(',', '').replace('%', '')
        
        try:
            return float(value_str)
        except:
            return np.nan
    
    def _format_currency(self, value):
        """
        Format numeric value with $ and commas.
        """
        if pd.isna(value):
            return np.nan
        if value < 0:
            return f'$({abs(value):,.0f})'
        else:
            return f'${value:,.0f}'
    
    def _calculate_percentage_change(self, current, previous):
        """
        Calculate percentage change between two values.
        """
        if pd.isna(current) or pd.isna(previous) or previous == 0:
            return np.nan
        return ((current - previous) / abs(previous))
    
    def _process_statement_data(self, quarterly_data, annual_data, metrics_list, statement_name):
        """
        Process financial statement data into a DataFrame matching Excel format.
        
        Args:
            quarterly_data (dict): Quarterly financial data
            annual_data (dict): Annual financial data
            metrics_list (list): List of metrics to include
            statement_name (str): Name of the financial statement
        
        Returns:
            pd.DataFrame: Processed DataFrame with latest 3 quarterly and 3 annual periods
        """
        # Create DataFrame structure
        df_data = {}
        df_data['Metric'] = metrics_list
        
        # Process quarterly data (latest 3 quarters)
        if quarterly_data and 'rows' in quarterly_data:
            headers = quarterly_data.get('headers', {})
            rows = quarterly_data['rows']
            
            # Get header values
            header_vals = self._ordered_header_values(headers) if headers else []
            
            # Extract latest 3 quarters
            num_quarters = min(3, len(header_vals) - 1)  # -1 for 'Period Ending:' header
            
            for i in range(num_quarters):
                col_idx = i + 1  # Skip first header
                if col_idx < len(header_vals):
                    # Add quarter date column
                    quarter_col = f'Q{i+1}_{header_vals[col_idx]}'
                    df_data[quarter_col] = []
                    
                    # Add percentage change column only for first 2 quarters
                    if i < 2:
                        change_col = f'Q{i+1}_Δ%'
                        df_data[change_col] = []
                    
                    # Fill data for each metric
                    for metric in metrics_list:
                        # Find the metric in rows
                        metric_value = None
                        for row in rows:
                            if row.get('value1', '').strip() == metric:
                                metric_value = row.get(f'value{col_idx+1}', np.nan)
                                break
                        
                        # Clean and format value
                        clean_value = self._clean_numeric_value(metric_value)
                        formatted_value = self._format_currency(clean_value)
                        df_data[quarter_col].append(formatted_value)
                        
                        # Calculate percentage change only for first 2 quarters
                        if i < 2:
                            if col_idx + 1 < len(header_vals):
                                prev_value = None
                                for row in rows:
                                    if row.get('value1', '').strip() == metric:
                                        prev_value = row.get(f'value{col_idx+2}', np.nan)
                                        break
                                prev_clean = self._clean_numeric_value(prev_value)
                                pct_change = self._calculate_percentage_change(clean_value, prev_clean)
                                df_data[change_col].append(pct_change)
                            else:
                                df_data[change_col].append(np.nan)
        
        # Process annual data (latest 3 years)
        if annual_data and 'rows' in annual_data:
            headers = annual_data.get('headers', {})
            rows = annual_data['rows']
            
            # Get header values
            header_vals = self._ordered_header_values(headers) if headers else []
            
            # Extract latest 3 years
            num_years = min(3, len(header_vals) - 1)  # -1 for 'Period Ending:' header
            
            for i in range(num_years):
                col_idx = i + 1  # Skip first header
                if col_idx < len(header_vals):
                    # Add year column
                    year_col = f'FY_{header_vals[col_idx]}'
                    df_data[year_col] = []
                    
                    # Add percentage change column only for first 2 years
                    if i < 2:
                        change_col = f'FY_{header_vals[col_idx]}_Δ%'
                        df_data[change_col] = []
                    
                    # Fill data for each metric
                    for metric in metrics_list:
                        # Find the metric in rows
                        metric_value = None
                        for row in rows:
                            if row.get('value1', '').strip() == metric:
                                metric_value = row.get(f'value{col_idx+1}', np.nan)
                                break
                        
                        # Clean and format value
                        clean_value = self._clean_numeric_value(metric_value)
                        formatted_value = self._format_currency(clean_value)
                        df_data[year_col].append(formatted_value)
                        
                        # Calculate percentage change only for first 2 years
                        if i < 2:
                            if col_idx + 1 < len(header_vals):
                                prev_value = None
                                for row in rows:
                                    if row.get('value1', '').strip() == metric:
                                        prev_value = row.get(f'value{col_idx+2}', np.nan)
                                        break
                                prev_clean = self._clean_numeric_value(prev_value)
                                pct_change = self._calculate_percentage_change(clean_value, prev_clean)
                                df_data[change_col].append(pct_change)
                            else:
                                df_data[change_col].append(np.nan)
        
        # Create DataFrame
        df = pd.DataFrame(df_data)
        
        # Set Metric as index for easier access
        if not df.empty:
            df.set_index('Metric', inplace=True)
        
        return df
    
    def get_income_statement(self):
        """
        Extract and process income statement data with latest 3 quarterly and 3 annual periods.
        
        Returns:
            pd.DataFrame: Income statement DataFrame with values and percentage changes
        """
        # Define Income Statement metrics matching Excel format
        income_metrics = [
            'Total Revenue',
            'Cost of Revenue',
            'Gross Profit',
            'Research and Development', 
            'Sales, General and Admin.',
            'Non-Recurring Items',
            'Other Operating Items',
            'Operating Expenses',
            'Earnings Before Interest and Tax',
            'Interest Expense',
            'Income Tax',
            'Net Income'
        ]
        
        # Fetch quarterly and annual data
        quarterly_data = self.fetch_financial_data(frequency=2)  # Quarterly
        annual_data = self.fetch_financial_data(frequency=1)     # Annual
        
        # Extract income statement tables
        quarterly_income = None
        annual_income = None
        
        if quarterly_data and 'data' in quarterly_data:
            quarterly_income = quarterly_data['data'].get('incomeStatementTable')
        
        if annual_data and 'data' in annual_data:
            annual_income = annual_data['data'].get('incomeStatementTable')
        
        # Process and combine data
        df_income = self._process_statement_data(
            quarterly_income, 
            annual_income, 
            income_metrics, 
            'Income Statement'
        )

        if not df_income.empty:
            # Calculate Operation Expenses = Research and Development + Sales, General and Admin. + Non-Recurring Items + Other Operating Items
            if 'Operating Expenses' in df_income.index:
                for col in df_income.columns:
                    if 'Δ%' not in col:  # Only for value columns
                        try:
                            # Get individual expense values
                            r_and_d_val = df_income.loc['Research and Development', col]
                            sg_and_a_val = df_income.loc['Sales, General and Admin.', col]
                            non_recurring_val = df_income.loc['Non-Recurring Items', col]
                            other_operating_val = df_income.loc['Other Operating Items', col]
                            
                            # Clean values to numeric for calculation
                            r_and_d_numeric = self._clean_numeric_value(r_and_d_val)
                            sg_and_a_numeric = self._clean_numeric_value(sg_and_a_val)
                            non_recurring_numeric = self._clean_numeric_value(non_recurring_val)
                            other_operating_numeric = self._clean_numeric_value(other_operating_val)
                            
                            # Sum up to get Operating Expenses
                            total_operating_expenses = sum(filter(pd.notna, [
                                r_and_d_numeric,
                                sg_and_a_numeric,
                                non_recurring_numeric,
                                other_operating_numeric
                            ]))
                            
                            df_income.loc['Operating Expenses', col] = self._format_currency(total_operating_expenses)
                        except:
                            pass
        
        return df_income
    
    def get_balance_sheet(self):
        """
        Extract and process balance sheet data with latest 3 quarterly and 3 annual periods.
        
        Returns:
            pd.DataFrame: Balance sheet DataFrame with values and percentage changes
        """
        # Define Balance Sheet metrics matching Excel format
        balance_metrics = [
            'Cash and Cash Equivalents',
            'Short-Term Investments',
            'Net Receivables',
            'Inventory',
            'Total Current Assets',
            'Total Assets',
            'Working Capital',
            'Short-Term Debt / Current Portion of Long-Term Debt',
            'Accounts Payable',
            'Other Current Liabilities',
            'Total Current Liabilities',
            'Long-Term Debt',
            'Total Liabilities',
            'Net Worth(OE)'
        ]
        
        # Fetch quarterly and annual data
        quarterly_data = self.fetch_financial_data(frequency=2)  # Quarterly
        annual_data = self.fetch_financial_data(frequency=1)     # Annual
        
        # Extract balance sheet tables
        quarterly_balance = None
        annual_balance = None
        
        if quarterly_data and 'data' in quarterly_data:
            quarterly_balance = quarterly_data['data'].get('balanceSheetTable')
        
        if annual_data and 'data' in annual_data:
            annual_balance = annual_data['data'].get('balanceSheetTable')
        
        # Process and combine data
        df_balance = self._process_statement_data(
            quarterly_balance,
            annual_balance,
            balance_metrics,
            'Balance Sheet'
        )
        
        # Calculate Working Capital and Shares Outstanding
        if not df_balance.empty:
            # Calculate Working Capital = Total Current Assets - Total Current Liabilities
            if 'Working Capital' in df_balance.index:
                for col in df_balance.columns:
                    if 'Δ%' not in col:  # Only for value columns
                        try:
                            # Get Total Current Assets value
                            current_assets_val = df_balance.loc['Total Current Assets', col]
                            # Get Total Current Liabilities value
                            current_liabilities_val = df_balance.loc['Total Current Liabilities', col]
                            
                            # Clean values to numeric for calculation
                            ca_numeric = self._clean_numeric_value(current_assets_val)
                            cl_numeric = self._clean_numeric_value(current_liabilities_val)
                            
                            if pd.notna(ca_numeric) and pd.notna(cl_numeric):
                                working_capital = ca_numeric - cl_numeric
                                df_balance.loc['Working Capital', col] = self._format_currency(working_capital)
                        except:
                            pass
            
            # Calculate Shares Outstanding = Total Assets - Total Liabilities
            if 'Net Worth(OE)' in df_balance.index:
                for col in df_balance.columns:
                    if 'Δ%' not in col:  # Only for value columns
                        try:
                            # Get Total Assets value
                            total_assets_val = df_balance.loc['Total Assets', col]
                            # Get Total Liabilities value
                            total_liabilities_val = df_balance.loc['Total Liabilities', col]
                            
                            # Clean values to numeric for calculation
                            ta_numeric = self._clean_numeric_value(total_assets_val)
                            tl_numeric = self._clean_numeric_value(total_liabilities_val)
                            
                            if pd.notna(ta_numeric) and pd.notna(tl_numeric):
                                shares_outstanding = ta_numeric - tl_numeric
                                df_balance.loc['Net Worth(OE)', col] = self._format_currency(shares_outstanding)
                        except:
                            pass
        
        return df_balance
    
    def get_cash_flow(self):
        """
        Extract and process cash flow statement data with latest 3 quarterly and 3 annual periods.
        
        Returns:
            pd.DataFrame: Cash flow DataFrame with values and percentage changes
        """
        # Define Cash Flow metrics matching Excel format
        cashflow_metrics = [
            'Net Income',
            'Cash Flows-Operating Activities',
            'Depreciation',
            'Net Income Adjustments',
            'Accounts Receivable',
            'Changes in Inventories',
            'Other Operating Activities',
            'Liabilities',
            'Net Cash Flow-Operating',
            'Cash Flows-Investing Activities',
            'Capital Expenditures',
            'Investments',
            'Other Investing Activities',
            'Net Cash Flows-Investing',
            'Cash Flows-Financing Activities',
            'Sale and Purchase of Stock',
            'Net Borrowings',
            'Other Financing Activities',
            'Net Cash Flows-Financing',
            'Net Cash Flow'
        ]
        
        # Fetch quarterly and annual data
        quarterly_data = self.fetch_financial_data(frequency=2)  # Quarterly
        annual_data = self.fetch_financial_data(frequency=1)     # Annual
        
        # Extract cash flow tables
        quarterly_cashflow = None
        annual_cashflow = None
        
        if quarterly_data and 'data' in quarterly_data:
            quarterly_cashflow = quarterly_data['data'].get('cashFlowTable')
        
        if annual_data and 'data' in annual_data:
            annual_cashflow = annual_data['data'].get('cashFlowTable')
        
        # Process and combine data
        df_cashflow = self._process_statement_data(
            quarterly_cashflow,
            annual_cashflow,
            cashflow_metrics,
            'Cash Flow Statement'
        )
        
        return df_cashflow
    
    def get_financial_ratios(self):
        """
        Extract and process financial ratios data with latest 3 quarterly and 3 annual periods.
        
        Returns:
            pd.DataFrame: Financial ratios DataFrame with decimal values (no percentage changes)
        """
        # Define Financial Ratios metrics matching Excel format
        ratios_metrics = [
            'Current Ratio',
            'Quick Ratio'
        ]
        
        # Fetch quarterly and annual data
        quarterly_data = self.fetch_financial_data(frequency=2)  # Quarterly
        annual_data = self.fetch_financial_data(frequency=1)     # Annual
        
        # Extract financial ratios tables (if available)
        quarterly_ratios = None
        annual_ratios = None
        
        if quarterly_data and 'data' in quarterly_data:
            quarterly_ratios = quarterly_data['data'].get('financialRatiosTable')
            # If not available, calculate from other statements
            if not quarterly_ratios:
                quarterly_ratios = self._calculate_ratios_from_statements(quarterly_data['data'], 'quarterly')
        
        if annual_data and 'data' in annual_data:
            annual_ratios = annual_data['data'].get('financialRatiosTable')
            # If not available, calculate from other statements
            if not annual_ratios:
                annual_ratios = self._calculate_ratios_from_statements(annual_data['data'], 'annual')
        
        # Process ratios data without currency formatting and percentage changes
        df_ratios = self._process_ratios_data(
            quarterly_ratios,
            annual_ratios,
            ratios_metrics
        )
        
        return df_ratios
    
    def _process_ratios_data(self, quarterly_data, annual_data, metrics_list):
        """
        Process financial ratios data into a DataFrame without currency formatting or percentage changes.
        
        Args:
            quarterly_data (dict): Quarterly financial ratios data
            annual_data (dict): Annual financial ratios data
            metrics_list (list): List of ratio metrics to include
        
        Returns:
            pd.DataFrame: Processed DataFrame with ratios as decimal values
        """
        # Create DataFrame structure
        df_data = {}
        df_data['Metric'] = metrics_list
        
        # Process quarterly data (latest 3 quarters)
        if quarterly_data and 'rows' in quarterly_data:
            headers = quarterly_data.get('headers', {})
            rows = quarterly_data['rows']
            
            # Get header values
            header_vals = self._ordered_header_values(headers) if headers else []
            
            # Extract latest 3 quarters
            num_quarters = min(3, len(header_vals) - 1)  # -1 for 'Period Ending:' header
            
            for i in range(num_quarters):
                col_idx = i + 1  # Skip first header
                if col_idx < len(header_vals):
                    # Add quarter date column (no percentage change for ratios)
                    quarter_col = f'Q{i+1}_{header_vals[col_idx]}'
                    df_data[quarter_col] = []
                    
                    # Fill data for each metric
                    for metric in metrics_list:
                        # Find the metric in rows
                        metric_value = None
                        for row in rows:
                            if row.get('value1', '').strip() == metric:
                                metric_value = row.get(f'value{col_idx+1}', np.nan)
                                break
                        
                        # Clean value but keep as numeric (no currency formatting for ratios)
                        clean_value = self._clean_numeric_value(metric_value)
                        # Round to 2 decimal places for ratios
                        if pd.notna(clean_value):
                            clean_value = round(clean_value, 2)
                        df_data[quarter_col].append(clean_value)
        
        # Process annual data (latest 3 years)
        if annual_data and 'rows' in annual_data:
            headers = annual_data.get('headers', {})
            rows = annual_data['rows']
            
            # Get header values
            header_vals = self._ordered_header_values(headers) if headers else []
            
            # Extract latest 3 years
            num_years = min(3, len(header_vals) - 1)  # -1 for 'Period Ending:' header
            
            for i in range(num_years):
                col_idx = i + 1  # Skip first header
                if col_idx < len(header_vals):
                    # Add year column (no percentage change for ratios)
                    year_col = f'FY_{header_vals[col_idx]}'
                    df_data[year_col] = []
                    
                    # Fill data for each metric
                    for metric in metrics_list:
                        # Find the metric in rows
                        metric_value = None
                        for row in rows:
                            if row.get('value1', '').strip() == metric:
                                metric_value = row.get(f'value{col_idx+1}', np.nan)
                                break
                        
                        # Clean value but keep as numeric (no currency formatting for ratios)
                        clean_value = self._clean_numeric_value(metric_value)
                        # Round to 2 decimal places for ratios
                        if pd.notna(clean_value):
                            clean_value = round(clean_value, 2)
                        df_data[year_col].append(clean_value)
        
        # Create DataFrame
        df = pd.DataFrame(df_data)
        
        # Set Metric as index for easier access
        if not df.empty:
            df.set_index('Metric', inplace=True)
        
        return df
    
    def _calculate_ratios_from_statements(self, financial_data, period_type):
        """
        Calculate financial ratios from income statement and balance sheet data.
        This is a fallback method when ratios are not directly available.
        
        Args:
            financial_data (dict): Financial data containing statements
            period_type (str): 'quarterly' or 'annual'
        
        Returns:
            dict: Calculated financial ratios in API format
        """
        # This is a simplified implementation - would need actual calculation logic
        # based on balance sheet and income statement values
        return None
    
    def get_all_financials(self):
        """
        Get all financial statements with latest 3 quarterly and 3 annual periods.
        
        Returns:
            dict: Dictionary containing all financial statement DataFrames
        """
        financials = {
            'income_statement': self.get_income_statement(),
            'balance_sheet': self.get_balance_sheet(),
            'cash_flow': self.get_cash_flow(),
            'financial_ratios': self.get_financial_ratios()
        }
        
        return financials
    
    def save_to_excel(self, filename='financial_statements.xlsx'):
        """
        Save all financial statements to an Excel file matching the format.
        
        Args:
            filename (str): Output filename
        """
        financials = self.get_all_financials()
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Write each statement to a separate sheet
            for sheet_name, df in financials.items():
                if df is not None and not df.empty:
                    # Format sheet name
                    formatted_name = sheet_name.replace('_', ' ').title()
                    df.to_excel(writer, sheet_name=formatted_name)
                    
                    # Format percentage columns
                    worksheet = writer.sheets[formatted_name]
                    for col in df.columns:
                        if 'Δ%' in col:
                            col_letter = chr(65 + df.columns.get_loc(col) + 1)  # +1 for index column
                            for row in range(2, len(df) + 2):  # +2 for header and 1-based indexing
                                cell = f'{col_letter}{row}'
                                try:
                                    worksheet[cell].number_format = '0.00%'
                                except:
                                    pass
        
        print(f"Financial data saved to {filename}")


# Main execution
if __name__ == "__main__":
    # Example usage
    ticker = "DASH"
    
    # Create instance of Financial_api class
    financial_api = Financial_api(ticker)
    
    # Get individual statements with latest 3 quarterly and 3 annual periods
    print(f"\nFetching financial data for {ticker}...")
    
    # Get Income Statement
    # print("\n" + "="*80)
    # print("INCOME STATEMENT (Latest 3 Quarters and 3 Years)")
    # print("="*80)
    # income_stmt = financial_api.get_income_statement()
    # if income_stmt is not None and not income_stmt.empty:
    #     print(income_stmt)
    #     print(f"\nShape: {income_stmt.shape}")
    #     print(f"Columns: {list(income_stmt.columns)}")
    
    # Get Balance Sheet  
    # print("\n" + "="*80)
    # print("BALANCE SHEET (Latest 3 Quarters and 3 Years)")
    # print("="*80)
    # balance_sheet = financial_api.get_balance_sheet()
    # if balance_sheet is not None and not balance_sheet.empty:
    #     print(balance_sheet)
    #     print(f"\nShape: {balance_sheet.shape}")
    
    # Get Cash Flow Statement
    # print("\n" + "="*80)
    # print("CASH FLOW STATEMENT (Latest 3 Quarters and 3 Years)")
    # print("="*80)
    # cash_flow = financial_api.get_cash_flow()
    # if cash_flow is not None and not cash_flow.empty:
    #     print(cash_flow.head(10))
    #     print(f"\nShape: {cash_flow.shape}")
    
    # Get Financial Ratios
    print("\n" + "="*80)
    print("FINANCIAL RATIOS (Latest 3 Quarters and 3 Years)")
    print("="*80)
    ratios = financial_api.get_financial_ratios()
    if ratios is not None and not ratios.empty:
        print(ratios.head(10))
        print(f"\nShape: {ratios.shape}")
    
    # # Save all to Excel
    # print("\n" + "="*80)
    # print("SAVING TO EXCEL")
    # print("="*80)
    # financial_api.save_to_excel(f'{ticker}_financials_enhanced.xlsx')
