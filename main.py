import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import io
import json
import re
import requests
import os
import Account_Overview
from pathlib import Path
from html_account_oveview import account_overview_to_html

from Config_file import logger
from Azure_OpenAI_Analyzer import AzureOpenAIAnalyzer
from Financial_Data_Fetcher import ( 
    FinancialDataFetcher, 
    display_financial_statements, 
    display_risk_analysis, 
    display_liquidity_analysis, 
    display_profitability_analysis, 
    display_cashflow_analysis, 
    display_AI_recommendation,
    generate_print_report,

    )
from query_engine import AI_rec_main
def main():
    """Main Streamlit app"""
    st.title("CreditIQ - Credit Compliance report with AI")
    # Input Section: Ticker and filing source choice
    col1, col2, col3 = st.columns([1, 2, 3])

    with col1:
        ticker = st.text_input("Enter Stock Ticker Symbol").upper()

    with col2:
        filing_source = st.radio(
            "Select 10-Q Filing Source:",
            ("Auto-fetch latest from SEC", "Upload custom file"),
            index=0,
            key="filing_source"
        )
        uploaded_file = None
        if filing_source == "Upload custom file":
            uploaded_file = st.file_uploader(
                "Upload 10-Q Filing",
                type=["pdf", "docx", "txt"],
                help="Upload your 10-Q filing in PDF, Word, or Text format",
                key="filing_upload"
            )
    with col3:
        Item_List_Source = st.file_uploader(
            "Upload Item  List (Optional)", 
            type=["xlsx", "xls", "csv"],
            help="Upload a excel or CSV file containing Item List"
        )
        Payment_History_source = st.file_uploader(
            "Upload Payment History (Optional)", 
            type=["xlsx", "xls", "csv"],
            help="Upload a excel or CSV file containing Payment History"
        )

    if st.button("Submit", type="primary"):

        pdf_file = None
        raw_text = ""

        # Handle filing source
        analyzer = AzureOpenAIAnalyzer()  # construct once
        # if filing_source == "Upload custom file":
        #     uploaded_file = st.file_uploader(
        #         "Upload 10-Q Filing", 
        #         type=["pdf", "docx", "txt"],
        #         help="Upload your 10-Q filing in PDF, Word, or Text format"
        #     )
        if uploaded_file:
            with st.spinner("Extracting text from uploaded document..."):
                raw_text = analyzer.extract_text_from_file(uploaded_file, filename=getattr(uploaded_file, "name", None), file_type=getattr(uploaded_file, "type", None))
            if raw_text:
                st.success("Document uploaded and processed successfully!")
        else:
            # Auto-fetch from SEC
            if ticker:
                try:
                    # Load CIK mapping JSON (adjust path or add your own mapping as needed)
                    mapping_path = "company_tickers_exchange.json"
                    if os.path.exists(mapping_path):
                        with open(mapping_path, "r") as f:
                            CIK_dict = json.load(f)
                        CIK_df = pd.DataFrame(CIK_dict["data"], columns=CIK_dict["fields"])
                        CIK = CIK_df[CIK_df["ticker"] == ticker].cik.values[0]
                    else:
                        # Minimal fallback: try SEC submissions search by ticker via known endpoint (requires CIK);
                        # Here we gracefully warn if mapping file is missing.
                        st.warning("Local CIK mapping not found. Please provide the mapping file or switch to 'Upload custom file'.")
                        CIK = None

                    if CIK is not None:
                        # SEC headers and URLs
                        headers = {"User-Agent": "your.email@domain.com"}
                        submissions_url = f"https://data.sec.gov/submissions/CIK{str(CIK).zfill(10)}.json"
                        subs = requests.get(submissions_url, headers=headers).json()
                        recent = pd.DataFrame(subs["filings"]["recent"])
                        acc_num = recent[recent.form == "10-Q"].accessionNumber.values[0].replace("-", "")
                        doc_name = recent[recent.form == "10-Q"].primaryDocument.values[0]
                        html_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_num}/{doc_name}"
                        pdf_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_num}/{doc_name.replace('.htm', '.pdf')}"

                        pdf_response = requests.get(pdf_url, headers=headers)
                        # AI_rec_main(html_url)

                        if pdf_response.status_code == 200:
                            pdf_file = io.BytesIO(pdf_response.content)
                        else:
                            # Fallback to HTML -> PDF conversion (best-effort)
                            html_content = requests.get(html_url, headers=headers).content.decode("utf-8", errors="ignore")
                            html_content = re.sub(r'<img[^>]*>', '', html_content)
                            # html_content = re.sub(r'<table[^>]*>.*?</table>', '', html_content, flags=re.DOTALL)
                            try:
                                from xhtml2pdf import pisa
                                pdf_buffer = io.BytesIO()
                                pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
                                pdf_buffer.seek(0)
                                pdf_file = pdf_buffer
                            except Exception:
                                # If conversion not available, keep raw HTML text
                                raw_text = re.sub("<[^<]+?>", " ", html_content)

                        if pdf_file and not raw_text:
                            st.success(f"Latest 10-Q filing fetched for {ticker}")
                except Exception as e:
                    st.error(f"Failed to fetch 10-Q from SEC: {e}")
        #Converting Item List and Payment History to DataFrame

        
        
        if Item_List_Source and Payment_History_source:
            try:
                if Item_List_Source:
                    if Item_List_Source.name.endswith('.csv'):
                        item_list_df = pd.read_csv(Item_List_Source)
                    else:
                        item_list_df = pd.read_excel(Item_List_Source)

                if Payment_History_source:
                    if Payment_History_source.name.endswith('.csv'):
                        payment_history_df = pd.read_csv(Payment_History_source)
                    else:
                        payment_history_df = pd.read_excel(Payment_History_source)
        
            except Exception as e:
                st.error(f"Failed to process uploaded files: {e}")
        # Process if we have either uploaded text or fetched PDF
        if ticker and (raw_text or pdf_file):
            try:
                fetcher = FinancialDataFetcher(ticker)
                finincial_statements_dataframe = fetcher.get_financial_statements()

                # Extract text from PDF if needed (pass explicit file_type to avoid .type error)
                if not raw_text and pdf_file:
                    with st.spinner("Extracting text from 10-Q document..."):
                        raw_text = analyzer.extract_text_from_file(pdf_file, filename=f"{ticker}_10q.pdf", file_type="application/pdf")

                # If we still don't have text, stop early
                if not raw_text:
                    st.error("Could not extract text from the 10-Q document.")
                    return

                # Build vector index ONCE here so downstream analyses are not empty
                analyzer.vector_index = analyzer.create_vector_index(raw_text)

                # Fetch financial statements
                financial_data = fetcher.get_financial_statements()

                # Perform AI-driven analyses using vector embeddings
                with st.spinner("Analyzing risks using AI"):
                    risk_analysis = analyzer.analyze_risks(raw_text)

                with st.spinner("Analyzing liquidity using AI"):
                    liquidity_analysis = analyzer.analyze_liquidity(raw_text)

                with st.spinner("Analyzing profitability using AI"):
                    profitability_analysis = analyzer.analyze_profitability(raw_text)

                with st.spinner("Analyzing cash flow using AI"):
                    cashflow_analysis = analyzer.analyze_cashflow(raw_text)

                with st.spinner("Analysing AI Recommendation form 10q"):
                     AI_rec_main(html_url)
                
                AI_Recommendation = Path("financial_analysis_output\step4_extractred_summary.txt").read_text(encoding="utf-8")
                

                # account_overview_html = ""
                # if 'item_list_df' in locals() and 'payment_history_df' in locals():
                #     try:
                #         # Call the Account Overview function to get the DataFrame
                #         account_overview_result = Account_Overview.main(item_list_df, payment_history_df)
                        
                #         # Convert the DataFrame to HTML
                #         if account_overview_result is not None and not account_overview_result.empty:
                #             account_overview_html = f"""
                #             <h3>Account Overview</h3>
                #             {account_overview_result.to_html(index=True, escape=False, na_rep="")}
                #             """
                #     except Exception as e:
                #         logger.warning(f"Could not generate Account Overview for report: {e}")
                #         account_overview_html = "<h3>Account Overview</h3><p>Account Overview data not available</p>"

                # Prepare HTML snippets for print
                # Financial tables
                bal_html = fetcher.format_financial_table(financial_data).to_html(index=False, escape=False, na_rep="")
                inc_html = fetcher.format_income_statement(financial_data).to_html(index=False, escape=False, na_rep="")
                cf_html = fetcher.format_cash_flow(financial_data).to_html(index=False, escape=False, na_rep="")
                tables_html = f"<h3>Balance Sheet</h3>{bal_html}<h3>Income Statement</h3>{inc_html}<h3>Cash Flow</h3>{cf_html}"
                # Acc_Over_html = Account_Overview.main(item_list_df,payment_history_df).to_html(index=False, escape=False, na_rep="")
                

                # Main tabs for interactive display - Added Cash Flow tab
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Financial Statements", "Risk Analysis", "Liquidity", "Profitability", "Cash Flow", "Account Overview", "AI Recommendation"])

                with tab1:
                    display_financial_statements(financial_data, ticker)

                with tab2:
                    display_risk_analysis(risk_analysis)

                with tab3:
                    display_liquidity_analysis(liquidity_analysis)

                with tab4:
                    display_profitability_analysis(profitability_analysis)

                with tab5:
                    display_cashflow_analysis(cashflow_analysis)
                with tab6:
                    Account_Overview.main(item_list_df,payment_history_df)
                with tab7:
                    display_AI_recommendation("financial_analysis_output\step4_extractred_summary.txt")

                # Generate full report for download
                st.markdown("---")
                st.subheader("📥 Export Report")

                # Download full HTML report
                all_html = {
                    'tables': tables_html,
                    'risk_analysis': risk_analysis.replace('\n', '<br>'),
                    'liquidity_analysis': liquidity_analysis.replace('\n', '<br>'),
                    'profitability_analysis': profitability_analysis.replace('\n', '<br>'),
                    'cashflow_analysis': cashflow_analysis.replace('\n', '<br>'),
                    'account_overview': account_overview_to_html(item_list_df, payment_history_df),
                    'AI_Recommendation': AI_Recommendation.replace('\n', '<br>')
                    # 'Account_Overview': Acc_Over_html
                }
                report_html = generate_print_report(ticker, all_html)

                st.download_button(
                    label="📊 Download Full Report (HTML)",
                    data=report_html,
                    file_name=f"{ticker}_financial_report_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your Azure OpenAI credentials and ensure the ticker symbol is valid.")
                logger.exception("Main app error:")
        else:
            if ticker:
                st.info("Please wait for the 10-Q filing to be fetched or upload a custom file.")
            else:
                st.info("Please enter a ticker symbol to proceed.")

    # if Item_List_Source and Payment_History_source:
    #     try:
    #         if Item_List_Source:
    #             if Item_List_Source.name.endswith('.csv'):
    #                 item_list_df = pd.read_csv(Item_List_Source)
    #             else:
    #                 item_list_df = pd.read_excel(Item_List_Source)
    #             st.subheader("Uploaded Item List")
    #             st.dataframe(item_list_df)

    #         if Payment_History_source:
    #             if Payment_History_source.name.endswith('.csv'):
    #                 payment_history_df = pd.read_csv(Payment_History_source)
    #             else:
    #                 payment_history_df = pd.read_excel(Payment_History_source)
    #             st.subheader("Uploaded Payment History")
    #             st.dataframe(payment_history_df)

    #     except Exception as e:
    #         st.error(f"Failed to process uploaded files: {e}")

if __name__ == "__main__":
    main()