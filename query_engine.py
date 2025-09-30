import os
import json
import requests
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from llama_index.core import Document, VectorStoreIndex, ServiceContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.settings import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever

class FinancialRAGPipeline:
    """
    Complete RAG pipeline for financial document analysis with 3-step process:
    1. Data Extraction & Ratio Calculation
    2. Analysis & Preliminary Rating Summary
    3. Verification
    """
    
    def __init__(self, 
                 azure_endpoint: str,
                 api_key: str,
                 embedding_deployment: str = "text-embedding-ada-002",
                 AZURE_OPENAI_DEPLOYMENT: str = "dev-gpt-4o",
                 api_version: str = "2024-02-01"):
        """
        Initialize the RAG pipeline with Azure OpenAI configurations.
        """
        
        # Configure Azure OpenAI Embedding model
        self.embed_model = AzureOpenAIEmbedding(
            model=embedding_deployment,
            deployment_name=embedding_deployment,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        
        # Configure Azure OpenAI LLM
        self.llm = AzureOpenAI(
            model="gpt-4o",
            deployment_name=AZURE_OPENAI_DEPLOYMENT,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=0.0,  # Set to 0 for consistent extraction
            max_tokens=4000,
        )
        
        # Configure LlamaIndex settings
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm

        
        
        # Store the source text for verification
        self.source_text = ""
        self.vector_index = None
        
    # =================== STEP 1: DATA EXTRACTION ===================
    
    def step1_extract_financial_data(self, html_url: str) -> Dict:
        """
        Step 1: Extract financial data from HTML URL and calculate ratios.
        
        Args:
            html_url: URL of the 10-Q HTML document
            
        Returns:
            Extracted financial data in JSON format
        """
        print("=" * 60)
        print("STEP 1: DATA EXTRACTION & RATIO CALCULATION")
        print("=" * 60)
        
        extraction_prompt = """You are a financial data extractor. From the provided 10-Q document, extract and calculate the following into valid JSON:

{
  "Company": "",
  "Report_Date": "",
  "Liquidity": {
    "Cash_and_Equivalents": "",
    "Total_Current_Assets": "",
    "Total_Current_Liabilities": "",
    "Current_Ratio": "Total_Current_Assets / Total_Current_Liabilities",
    "Operating_Cash_Flow": "",
    "Liquidity_Runway_Months": "If OCF <0, Cash_and_Equivalents / |Operating_Cash_Flow/12| else 'Not applicable'"
  },
  "Leverage": {
    "Total_Debt": "",
    "Shareholders_Equity": "",
    "Debt_to_Equity": "Total_Debt / Shareholders_Equity",
    "Debt_Maturities": {
      "2025": "",
      "2026": "",
      "2027": "",
      "2028": "",
      "2029_and_beyond": ""
    },
    "Undrawn_Facilities": ""
  },
  "Profitability": {
    "Revenue": "",
    "Operating_Income": "",
    "Net_Income": "",
    "Operating_Margin": "Operating_Income / Revenue"
  },
  "Cash_Flow": {
    "Operating_Cash_Flow": "",
    "Capex": "",
    "Free_Cash_Flow": "Operating_Cash_Flow - Capex"
  },
  "Commitments_Contingencies": {
    "Purchase_Obligations": "",
    "Legal_Tax_Exposure": ""
  }
}

Rules:
- Use exact reported values and currency units
- Do not invent values; leave as "" if not disclosed
- Perform calculations only if both inputs exist
- Output must be valid JSON only (no commentary)
- Look for the most recent quarter data
- For debt maturities, check the notes section
- For undrawn facilities, check credit agreements or liquidity sections"""

        try:
            # Parse HTML and create vector index
            print(f"Fetching and parsing HTML from: {html_url}")
            self.source_text = self._parse_html(html_url)
            print(f"Extracted {len(self.source_text)} characters of text")
            
            print("Creating vector index with Azure OpenAI embeddings...")
            self.vector_index = self._create_vector_index(self.source_text)
            
            # Query for financial data extraction
            print("Extracting financial data...")
            query_engine = self.vector_index.as_query_engine(
                llm=self.llm,
                similarity_top_k=15,  # Retrieve more chunks for comprehensive data
                response_mode="compact"
            )
            
            response = query_engine.query(extraction_prompt)
            
            # Parse JSON response
            financial_data = self._parse_json_response(str(response))
            
            # Perform calculations if needed
            financial_data = self._calculate_ratios(financial_data)
            
            print("\n✅ Step 1 Complete: Financial data extracted")
            return financial_data
            
        except Exception as e:
            print(f"❌ Error in Step 1: {e}")
            return {"error": str(e)}
    
    # =================== STEP 2: ANALYSIS & RATING ===================
    
    def step2_analyze_and_rate(self, financial_data: Dict) -> str:
        """
        Step 2: Analyze financial data and generate preliminary credit rating summary.
        
        Args:
            financial_data: Extracted financial data from Step 1
            
        Returns:
            One-page credit rating summary
        """
        print("\n" + "=" * 60)
        print("STEP 2: ANALYSIS & PRELIMINARY RATING SUMMARY")
        print("=" * 60)
        
        analysis_prompt = f"""You are a credit risk analyst. Using the following financial data, generate a one-page "System Preliminary Credit Rating Summary":

Financial Data:
{json.dumps(financial_data, indent=2)}

Format the summary with these sections:

1. **Company Snapshot** – Company, Report Date, Sector (if known)


2. **Liquidity & Cash Flow** – Show values (Cash, Current Ratio, OCF, Runway) + 1-2 sentences commentary

3. **Debt & Capital Structure** – Show values (Debt, Debt/Equity, Near-term maturities, Revolver availability) + commentary

4. **Profitability** – Show values (Revenue, Net Income, Margin) + commentary

5. **Commitments & Contingencies** – Show obligations, lawsuits, exposures + commentary

6. **Peer Benchmark** – If not available, state "Not disclosed."

7. **Risk Flags**:
   🔴 Critical (if any metric indicates severe distress)
   🟠 Moderate (if metrics show concern)
   🟢 Favorable (if metrics are healthy)

8. **System Preliminary Rating Guidance**:
   - Risk Level: [Low/Medium/High]
   - Equivalent Rating Band: [AAA-BBB (Investment Grade) / BB-B (Speculative) / CCC-D (Distressed)]
   - Suggested Action: [Increase / Maintain / Reduce exposure]
   - Disclaimer: "This is system preliminary guidance only. Final decision rests with the Credit Compliance Team."

Rules:
- Commentary max 2 sentences per section
- Do not invent missing values
- Ensure ratios and calculations match JSON
- Keep to one page length"""

        try:
            # Use the LLM directly for analysis
            response = self.llm.complete(analysis_prompt)
            analysis_summary = str(response)
            
            print("\n✅ Step 2 Complete: Credit rating summary generated")
            return analysis_summary
            
        except Exception as e:
            print(f"❌ Error in Step 2: {e}")
            return f"Error generating analysis: {str(e)}"
    
    # =================== STEP 3: VERIFICATION ===================
    
    def step3_verify_data(self, financial_data: Dict) -> str:
        """
        Step 3: Verify extracted JSON numbers against source text.
        
        Args:
            financial_data: Extracted financial data from Step 1
            
        Returns:
            Verification report
        """
        print("\n" + "=" * 60)
        print("STEP 3: VERIFICATION")
        print("=" * 60)
        
        if not self.vector_index:
            return "Error: No source text available for verification"
        
        verification_prompt = f"""You are a verifier. Compare these extracted JSON numbers to the source text:

Extracted Data:
{json.dumps(financial_data, indent=2)}

For each value in the JSON:
1. Search for the corresponding value in the source document
2. Verify if the extracted value matches the source
3. If there's a mismatch, flag it and provide the correct value
4. Pay special attention to:
   - Currency units (millions vs billions)
   - Negative values
   - Calculated ratios

Report format:
- If all values match: "✅ All values verified."
- If mismatches exist: List each mismatch as "❌ [Field]: Extracted [X] but source shows [Y]"
"""

        try:
            query_engine = self.vector_index.as_query_engine(
                llm=self.llm,
                similarity_top_k=20,  # Get more context for verification
                response_mode="tree_summarize"
            )
            
            verification_result = query_engine.query(verification_prompt)
            
            print("\n✅ Step 3 Complete: Verification performed")
            return str(verification_result)
            
        except Exception as e:
            print(f"❌ Error in Step 3: {e}")
            return f"Error during verification: {str(e)}"
        
    def step_4_extract_summary(self, ext_summary: str) -> str:
        """
        Step 4: from the extracted analysis from step-2, extract only summary not any financial numbers.
        
        Args:
            analysis_summary: Extracted analysis_summary from Step 2
            
        Returns:
            short summary of the company financials
        """
        print("\n" + "=" * 60)
        print("STEP 4: Extract summary")
        print("=" * 60)

        extract_summary_prompt = f""""
        Finincial Data:
        {ext_summary}

        You are a credit analyst. From the provided financial data, generate the following output:

        Commentary Summary – concise bullet points with insights for each section.

        Risk Flags – exactly as provided in the data (🔴 Critical, 🟠 Moderate, 🟢 Favorable).

        System Preliminary Rating Guidance – exactly as provided in the data.

        Ensure the response strictly follows this format:

        Commentary Summary:

        Point 1

        Point 2

        Point 3

        Point 4

        Risk Flags:
        [List as in provided data]

        System Preliminary Rating Guidance:
        [Show guidance as in provided data]

        """
        try:
            # Use the LLM directly for analysis
            response = self.llm.complete(extract_summary_prompt)
            extracted_summary = str(response)
            
            print("\n✅ Step 2 Complete: Credit rating summary generated")
            return extracted_summary
            
        except Exception as e:
            print(f"❌ Error in Step 2: {e}")
            return f"Error generating analysis: {str(e)}"
    
    # =================== HELPER METHODS ===================
    
    def _parse_html(self, html_url: str) -> str:
        """Parse HTML from URL and extract text content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(html_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract tables separately to preserve structure
            tables = soup.find_all('table')
            table_texts = []
            for table in tables:
                table_text = self._extract_table_text(table)
                table_texts.append(table_text)
            
            # Get all text
            text = soup.get_text(separator=' ', strip=True)
            
            # Add table texts
            text = text + "\n\nTABLES:\n" + "\n".join(table_texts)
            
            # Clean up
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            return text
            
        except Exception as e:
            raise Exception(f"Error parsing HTML: {e}")
    
    def _extract_table_text(self, table) -> str:
        """Extract text from HTML table preserving structure."""
        rows = table.find_all('tr')
        table_data = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            table_data.append(' | '.join(row_data))
        return '\n'.join(table_data)
    
    def _create_vector_index(self, text: str) -> VectorStoreIndex:
        """Create a vector index from text."""
        document = Document(text=text)
        
        # Create node parser for better chunking
        node_parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=256
        )
        
        nodes = node_parser.get_nodes_from_documents([document])
        
        # Create index
        index = VectorStoreIndex(
            nodes,
            embed_model=self.embed_model,
            show_progress=True
        )
        
        return index
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """Extract JSON from LLM response."""
        try:
            # Find JSON content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            # Return template with error
            return {
                "error": "Failed to parse JSON",
                "raw_response": response_text[:500]
            }
    
    def _calculate_ratios(self, data: Dict) -> Dict:
        """Calculate financial ratios if not already calculated."""
        try:
            # Current Ratio
            liquidity = data.get("Liquidity", {})
            if (liquidity.get("Total_Current_Assets") and 
                liquidity.get("Total_Current_Liabilities") and 
                not liquidity.get("Current_Ratio")):
                
                assets = self._extract_number(liquidity["Total_Current_Assets"])
                liabilities = self._extract_number(liquidity["Total_Current_Liabilities"])
                if assets and liabilities:
                    liquidity["Current_Ratio"] = f"{assets / liabilities:.2f}"
            
            # Debt to Equity
            leverage = data.get("Leverage", {})
            if (leverage.get("Total_Debt") and 
                leverage.get("Shareholders_Equity") and 
                not leverage.get("Debt_to_Equity")):
                
                debt = self._extract_number(leverage["Total_Debt"])
                equity = self._extract_number(leverage["Shareholders_Equity"])
                if debt and equity:
                    leverage["Debt_to_Equity"] = f"{debt / equity:.2f}"
            
            # Operating Margin
            profitability = data.get("Profitability", {})
            if (profitability.get("Operating_Income") and 
                profitability.get("Revenue") and 
                not profitability.get("Operating_Margin")):
                
                op_income = self._extract_number(profitability["Operating_Income"])
                revenue = self._extract_number(profitability["Revenue"])
                if op_income and revenue:
                    profitability["Operating_Margin"] = f"{(op_income / revenue) * 100:.2f}%"
            
            # Free Cash Flow
            cash_flow = data.get("Cash_Flow", {})
            if (cash_flow.get("Operating_Cash_Flow") and 
                cash_flow.get("Capex") and 
                not cash_flow.get("Free_Cash_Flow")):
                
                ocf = self._extract_number(cash_flow["Operating_Cash_Flow"])
                capex = self._extract_number(cash_flow["Capex"])
                if ocf is not None and capex is not None:
                    fcf = ocf - abs(capex)  # Capex is typically negative
                    cash_flow["Free_Cash_Flow"] = f"${fcf:,.0f}"
            
            # Liquidity Runway
            if (liquidity.get("Operating_Cash_Flow") and 
                liquidity.get("Cash_and_Equivalents")):
                
                ocf = self._extract_number(liquidity["Operating_Cash_Flow"])
                cash = self._extract_number(liquidity["Cash_and_Equivalents"])
                
                if ocf and ocf < 0 and cash:
                    monthly_burn = abs(ocf) / 12
                    runway_months = cash / monthly_burn
                    liquidity["Liquidity_Runway_Months"] = f"{runway_months:.1f} months"
                elif not liquidity.get("Liquidity_Runway_Months"):
                    liquidity["Liquidity_Runway_Months"] = "Not applicable"
            
        except Exception as e:
            print(f"Warning: Error calculating ratios: {e}")
        
        return data
    
    def _extract_number(self, value_str: str) -> Optional[float]:
        """Extract numeric value from string with currency/units."""
        if not value_str or value_str == "":
            return None
        
        try:
            # Remove currency symbols and commas
            clean_str = re.sub(r'[$,()]', '', str(value_str))
            
            # Handle parentheses for negative numbers
            if '(' in str(value_str) and ')' in str(value_str):
                clean_str = '-' + clean_str
            
            # Extract number
            match = re.search(r'-?\d+\.?\d*', clean_str)
            if match:
                number = float(match.group())
                
                # Handle millions/billions
                if 'million' in value_str.lower():
                    number *= 1_000_000
                elif 'billion' in value_str.lower():
                    number *= 1_000_000_000
                
                return number
        except:
            pass
        
        return None
    
    # =================== MAIN PIPELINE METHOD ===================
    
    def run_complete_pipeline(self, html_url: str) -> Dict:
        """
        Run the complete 3-step financial analysis pipeline.
        
        Args:
            html_url: URL of the 10-Q HTML document
            
        Returns:
            Dictionary containing results from all 3 steps
        """
        print("\n" + "=" * 60)
        print("FINANCIAL RAG PIPELINE - STARTING")
        print("=" * 60)
        print(f"URL: {html_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            "url": html_url,
            "timestamp": datetime.now().isoformat(),
            "step1_extraction": None,
            "step2_analysis": None,
            "step3_verification": None,
            "step4_extract_summary": None
        }
        
        # Step 1: Extract Financial Data
        financial_data = self.step1_extract_financial_data(html_url)
        results["step1_extraction"] = financial_data
        
        if "error" in financial_data:
            print(f"\n❌ Pipeline halted due to Step 1 error: {financial_data['error']}")
            return results
        
        # Step 2: Analyze and Rate
        analysis_summary = self.step2_analyze_and_rate(financial_data)
        results["step2_analysis"] = analysis_summary
        
        # Step 3: Verify Data
        verification_report = self.step3_verify_data(financial_data)
        results["step3_verification"] = verification_report

        # Step 4: Extract summary

        extract_summary = self.step_4_extract_summary(analysis_summary)
        results["step4_extract_summary"] = extract_summary
        
        print("\n" + "=" * 60)
        print("FINANCIAL RAG PIPELINE - COMPLETE")
        print("=" * 60)
        
        return results


# =================== USAGE EXAMPLE ===================

def AI_rec_main(html_url):

    
    """
    Example usage of the Financial RAG Pipeline.
    """
    
    # Configure Azure OpenAI credentials
    AZURE_ENDPOINT = "https://ea-oai-sandbox.openai.azure.com"
    API_KEY = "2f6e41aa534f49908feb01c6de771d6b"
    EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
    AZURE_OPENAI_DEPLOYMENT = "dev-gpt-4o"
    
    # Initialize the pipeline
    pipeline = FinancialRAGPipeline(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=API_KEY,
        embedding_deployment=EMBEDDING_DEPLOYMENT,
        AZURE_OPENAI_DEPLOYMENT=AZURE_OPENAI_DEPLOYMENT
    )
    
    # Example 10-Q URL
    # html_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/aapl-20250628.htm"
    
    # Run the complete pipeline
    results = pipeline.run_complete_pipeline(html_url)
    
    # Save results
    output_dir = "financial_analysis_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save Step 1 - JSON extraction
    with open(f"{output_dir}/step1_extraction.json", "w") as f:
        json.dump(results["step1_extraction"], f, indent=2)
    
    # Save Step 2 - Analysis summary
    with open(f"{output_dir}/step2_analysis.md", "w", encoding="utf-8") as f:
        f.write(results["step2_analysis"])
    
    # Save Step 3 - Verification report
    with open(f"{output_dir}/step3_verification.txt", "w",encoding="utf-8") as f:
        f.write(results["step3_verification"])

    # Save Step 4- Extract Summary
    with open(f"{output_dir}/step4_extractred_summary.txt", "w",encoding="utf-8") as f:
        f.write(results["step4_extract_summary"])
    
    # Save complete results
    with open(f"{output_dir}/complete_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to '{output_dir}/' directory")
    
    # Display summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    print("\n📊 Step 1 - Extracted Data:")
    if results["step1_extraction"] and "error" not in results["step1_extraction"]:
        print(f"  Company: {results['step1_extraction'].get('Company', 'N/A')}")
        print(f"  Report Date: {results['step1_extraction'].get('Report_Date', 'N/A')}")
    
    print("\n📈 Step 2 - Rating Summary:")
    if "Risk Level:" in str(results["step2_analysis"]):
        print("  Credit rating analysis generated successfully")
    
    print("\n✅ Step 3 - Verification:")
    if "verified" in str(results["step3_verification"]).lower():
        print("  Verification completed")
    print("\n📈 Step 4 - Extract Summary:")
    if "Risk Level:" in str(results["step4_extract_summary"]):
        print("  Extracted the summary sucessfully from step 2")
    return results


# =================== ADVANCED FEATURES ===================

class EnhancedFinancialRAGPipeline(FinancialRAGPipeline):
    """
    Enhanced pipeline with additional features for production use.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.audit_log = []
    
    def batch_process_urls(self, urls: List[str]) -> List[Dict]:
        """
        Process multiple 10-Q URLs in batch.
        
        Args:
            urls: List of HTML URLs to process
            
        Returns:
            List of results for each URL
        """
        batch_results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"Processing URL {i}/{len(urls)}")
            print(f"{'='*60}")
            
            try:
                results = self.run_complete_pipeline(url)
                batch_results.append(results)
                
                # Log audit trail
                self.audit_log.append({
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success" if "error" not in results["step1_extraction"] else "failed"
                })
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                batch_results.append({
                    "url": url,
                    "error": str(e)
                })
        
        return batch_results
    
    def generate_comparison_report(self, results_list: List[Dict]) -> str:
        """
        Generate a comparison report across multiple companies.
        
        Args:
            results_list: List of pipeline results
            
        Returns:
            Comparison report in markdown format
        """
        comparison_prompt = f"""
        Generate a comparative analysis report for the following companies:
        
        {json.dumps([r["step1_extraction"] for r in results_list], indent=2)}
        
        Include:
        1. Ranking by Current Ratio
        2. Ranking by Debt-to-Equity
        3. Ranking by Operating Margin
        4. Overall Risk Assessment Comparison
        5. Investment Recommendation
        """
        
        response = self.llm.complete(comparison_prompt)
        return str(response)
    
    def export_to_excel(self, results: Dict, filename: str = "financial_analysis.xlsx"):
        """
        Export results to Excel format (requires openpyxl).
        
        Note: This is a template - requires openpyxl installation.
        """
        try:
            import pandas as pd
            
            # Flatten the JSON data
            extraction = results["step1_extraction"]
            
            # Create DataFrames
            df_liquidity = pd.DataFrame([extraction.get("Liquidity", {})])
            df_leverage = pd.DataFrame([extraction.get("Leverage", {})])
            df_profitability = pd.DataFrame([extraction.get("Profitability", {})])
            
            # Write to Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df_liquidity.to_excel(writer, sheet_name='Liquidity', index=False)
                df_leverage.to_excel(writer, sheet_name='Leverage', index=False)
                df_profitability.to_excel(writer, sheet_name='Profitability', index=False)
            
            print(f"✅ Exported to {filename}")
            
        except ImportError:
            print("⚠️ Install pandas and openpyxl for Excel export functionality")


if __name__ == "__main__":
    AI_rec_main()