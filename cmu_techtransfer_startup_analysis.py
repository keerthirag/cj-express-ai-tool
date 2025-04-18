import streamlit as st
from openai import OpenAI
import pdfplumber
import re
from typing import List, Dict
import time
import pandas as pd
import io
import json
import base64
import numpy as np

# Set up OpenAI API (use environment variables in production)
client = OpenAI(api_key="***")

# CJ Express Context
CJ_EXPRESS_CONTEXT = """
CJ Express, a Thai supermarket chain, aims to disrupt global retail with high-tech solutions. Targets: mid-high to low-income, multi-generational, diverse lifestyles (e.g., trendy women, pet lovers). Focus: (1) Category Management (optimizing product assortment), (2) Product Development (innovative offerings), (3) Offline Promotion (in-store engagement), (4) Supply Chain/Logistics (efficient distribution), (5) Store Operations (streamlined processes). Goals: global expansion, efficiency, customer experience (3-5 years).
"""

# CMU Research Context
CMU_RESEARCH_CONTEXT = """
CMU research (Computer Science, Tepper): AI predictive analytics, quantum optimization, robotics. Applications: demand forecasting, supply chain, real-time decisions (3-5 year horizon).
"""

# Checklist of startups to analyze (from Pages 32-33)
CHECKLIST_STARTUPS = {
    "Acatar", "Accel Diagnostics", "Acrobatiq", "Advanced Optronics", "Advanced Respiratory Technologies",
    "AirViz", "Akustica", "All-Access Transit Solutions", "Amira Learning, Inc.", "Anactisis", "AnCure",
    "Ansatz", "Aquatonomy Inc.", "Arieca", "Astrobotic Technology Inc", "ATRP Solutions", "Beyond Reach Labs Inc.",
    "BioBind", "BioCognon", "Biohybrid Solutions", "BirdBrain Technologies LLC", "Blade Diagnostics Corporation",
    "Bloomfield Robotics", "Blue Belt Technologies", "Butterfly Haptics", "Capio, Inc.", "Carley Technologies / Netanomics",
    "Carmell Therapeutics", "Carnegie Group, Inc.", "Carnegie Learning", "Carnegie Robotics", "Chameleon Semiconductor",
    "Change Dyslexia", "Chement", "Chemia Biosciences", "Consistency", "Conviva", "CorePower Magnetics", "CurvePoint",
    "Duolingo", "Edulis", "Efficient Computer Corporation", "ELIO.ai", "Equa Health", "ESTAT Actuation", "FacioMetrics",
    "Fluid Reality", "FluidForm", "ForAllSecure", "Freespace Robotics", "FuturHand Robotics", "Hebi Robotics",
    "HexSpline3D", "Hikari Labs", "Human Motion Technologies, LLC", "Impact Proteomics", "InceptEV", "JP Robotics",
    "Kestrel", "LeanFM Technologies", "Liquid X™ Printed Metals, Inc.", "LumiShield Technologies", "Magnify Bioscience",
    "Marinus Analytics", "MedRespond", "Mimetic Ink", "MindTrace", "Mine Vision Systems", "Modular Robotics",
    "myScribe", "NAIMA Health", "NovoLINC", "Omnibus Medical Devices", "Optimized Markets", "Ottomatika",
    "Pajama Cats Media", "Panopto", "Pearl Street Technologies", "Peca Labs", "Peoples Energy Analytics",
    "Phlux Technologies", "Pittsburgh Pattern Recognition", "Platypus Technologies", "Plextronics", "Power3D",
    "Precision Neuroscopics", "Propel Aero", "Qeexo", "Quantitative Medicine", "Rapid Biosense", "Rapid Flow",
    "re2 Inc", "Reach Neuro", "Recaptcha", "RedZone Robotics", "RoadBotics", "RoboCars, Inc.", "RoboTutor LLC",
    "Rockfish Data", "Rubitection, Inc.", "Safaba Translations Solutions, Inc", "SafeRails", "Script Biosciences",
    "SeaLion Energy", "Sensible Photonics", "Setex Technologies", "Sharp Therapeutics", "Shield AI", "SilisiumTech",
    "SkinJect Inc", "Snail Biosciences", "Solar Energy Estimation", "SpectraGenetics", "StimGen", "Strategic Machine",
    "Strategy Robot", "SUDOC", "Synapse Symphony", "Targeted delivery of agricultural chemicals", "TeraSpatial, Inc.",
    "Teratonix", "Three Rivers Material Separation", "Titan Robotics", "Traffiqure Technologies", "UltronAI", "Veniam",
    "Vera Therapeutics", "Virtual Traffic Lights", "Vivisimo", "Voci™ Technologies Inc.", "VoxEQ",
    "Wombat Security Technologies", "Wood Wide AI", "YinzCam", "Ziel Therapeutics"
}

# Function to parse the PDF and extract startups with descriptions
def extract_startups_from_document(pdf_path: str) -> List[Dict]:
    startups = []
    current_section = ""
    current_industry = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            try:
                text = page.extract_text()
                lines = text.split("\n") if text else []
                
                # Regex patterns
                section_pattern = re.compile(r"^(Recent and Selected Acquisitions/Exits of CMU spin-off companies|CMU spin-off companies backed by venture capital/ institutional investment|CMU early-stage spin-off companies without institutional investment|Pipeline: Emerging Spin-offs)$")
                industry_pattern = re.compile(r"^(Cleantech/energy|Electronics/Semiconductors|Robotics|Social Networking/Mobile Computing|Software and AI|Medical Devices/Biotech|Chemistry and Materials Science|Social Ventures)$")
                startup_pattern = re.compile(r"^\d+\.\s+([A-Za-z0-9\s]+(?:, Inc\.| LLC)?(?:\s+\(Joint with .*\))?):")
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Identify section
                    section_match = section_pattern.match(line)
                    if section_match:
                        current_section = section_match.group(1)
                        current_industry = ""
                        continue
                    
                    # Identify industry
                    if current_section != "Recent and Selected Acquisitions/Exits of CMU spin-off companies":
                        industry_match = industry_pattern.match(line)
                        if industry_match:
                            current_industry = industry_match.group(1)
                            continue
                    
                    # Identify startup
                    startup_match = startup_pattern.match(line)
                    if startup_match and current_section:
                        name = startup_match.group(1).strip()
                        if name not in CHECKLIST_STARTUPS:
                            continue
                        description_start = line.find(":") + 1
                        description = line[description_start:].strip()
                        
                        # Collect full description
                        j = i + 1
                        while j < len(lines) and not (startup_pattern.match(lines[j]) or industry_pattern.match(lines[j]) or section_pattern.match(lines[j])):
                            description += " " + lines[j].strip()
                            j += 1
                        
                        startups.append({
                            "Company Name": name,
                            "Description": description.strip(),
                            "Section": current_section,
                            "Industry Category": current_industry if current_industry else "N/A",
                            "Website": ""  # No website data in PDF
                        })
            except Exception as e:
                st.error(f"Error processing page {page_num}: {str(e)}")
                continue
    
    return startups

# GPT Analysis Function (from analysis_app.py, adapted for PDF input)
def analyze_with_gpt(startups: List[Dict], output_file: str = "raw_gpt_outputs.json") -> List[Dict]:
    results = []
    raw_outputs = []
    
    for startup in startups:
        prompt = f"""
{CJ_EXPRESS_CONTEXT}

Analyze the following startup for relevance to CJ Express’s retail goals based solely on its description. **Return the analysis as a JSON object enclosed in triple backticks (```), with no additional text or labels outside the JSON (e.g., do not add 'json')**. For each of the five pillars (Category Management, Product Development, Offline Promotion, Supply Chain/Logistics, Store Operations), evaluate **how the startup’s technology could directly or indirectly benefit CJ Express**, even if the connection is subtle or long-term. Provide detailed reasoning for each pillar, avoiding blanket 'no relevance' unless truly inapplicable. Assign scores (0-10) reflecting potential impact, and calculate the Overall Score as a weighted sum (Category*0.3125 + Product*0.3125 + Promotion*0.1875 + Supply*0.125 + Operations*0.0625), then multiply by 10 to scale to 0-100. Use this exact structure:
{{
"Company": "{startup['Company Name']}",
"Technology": "<core technology>",
"Ability": "<specific functions>",
"Summary": "<specific benefit to CJ Express or 'No retail benefit' if none>",
"Relevancy to Retail": "<detailed fit with CJ Express’s goals, direct or indirect, or 'No relevancy' if none>",
"Category Management Score": <int>,
"Category Management Reasoning": "<how it could optimize product assortment>",
"Product Development Score": <int>,
"Product Development Reasoning": "<how it could lead to innovative offerings>",
"Offline Promotion Score": <int>,
"Offline Promotion Reasoning": "<how it could enhance in-store engagement>",
"Supply Chain/Logistics Score": <int>,
"Supply Chain/Logistics Reasoning": "<how it could improve distribution or sustainability>",
"Store Operations Score": <int>,
"Store Operations Reasoning": "<how it could streamline in-store processes>",
"Overall Score": <float>,
"Category": "{startup['Section']}",
"Industry": "{startup['Industry Category']}"
}}

Startup Description:
{startup['Company Name']} ({startup['Section']}, {startup['Industry Category']}): {startup['Description']}
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.5
            )
            output = response.choices[0].message.content.strip()
            if not output.startswith("```") or not output.endswith("```"):
                output = f"```{output}```"
            raw_outputs.append({
                "company": startup["Company Name"],
                "raw_output": output
            })
            result = parse_gpt_output(output, startup)
            results.append(result)
        except Exception as e:
            st.error(f"OpenAI API Error for {startup['Company Name']}: {str(e)}")
            result = {
                "Company": startup["Company Name"],
                "Technology": "API Failure",
                "Ability": "N/A",
                "Summary": "Analysis failed due to API error",
                "Relevancy to Retail": "Not assessed",
                "Category Management Score": 0,
                "Category Management Reasoning": "Error",
                "Product Development Score": 0,
                "Product Development Reasoning": "Error",
                "Offline Promotion Score": 0,
                "Offline Promotion Reasoning": "Error",
                "Supply Chain/Logistics Score": 0,
                "Supply Chain/Logistics Reasoning": "Error",
                "Store Operations Score": 0,
                "Store Operations Reasoning": "Error",
                "Overall Score": 0,
                "Category": startup["Section"],
                "Industry": startup["Industry Category"]
            }
            raw_outputs.append({
                "company": startup["Company Name"],
                "raw_output": f"Error: {str(e)}"
            })
            results.append(result)
        time.sleep(10)
    
    with open(output_file, "w") as f:
        json.dump(raw_outputs, f, indent=2)
    
    return results

# Parse GPT Output
def parse_gpt_output(output: str, startup: Dict) -> Dict:
    result = {
        "Company": startup["Company Name"],
        "Technology": "",
        "Ability": "",
        "Summary": "",
        "Relevancy to Retail": "",
        "Category Management Score": 0,
        "Category Management Reasoning": "Not provided",
        "Product Development Score": 0,
        "Product Development Reasoning": "Not provided",
        "Offline Promotion Score": 0,
        "Offline Promotion Reasoning": "Not provided",
        "Supply Chain/Logistics Score": 0,
        "Supply Chain/Logistics Reasoning": "Not provided",
        "Store Operations Score": 0,
        "Store Operations Reasoning": "Not provided",
        "Overall Score": 0,
        "Category": startup["Section"],
        "Industry": startup["Industry Category"]
    }
    
    if not output.startswith("```") or not output.endswith("```"):
        st.warning(f"GPT output for {startup['Company Name']} missing ``` markers or not in JSON format")
        result["Summary"] = "Parsing failed - incorrect format"
        return result
    
    json_str = output.strip("```").strip()
    json_str = re.sub(r'^json\s*', '', json_str, flags=re.IGNORECASE)
    try:
        data = json.loads(json_str)
        result.update(data)
        
        # Verify Overall Score
        calculated_score = (data["Category Management Score"] * 0.3125 +
                           data["Product Development Score"] * 0.3125 +
                           data["Offline Promotion Score"] * 0.1875 +
                           data["Supply Chain/Logistics Score"] * 0.125 +
                           data["Store Operations Score"] * 0.0625) * 10
        if abs(calculated_score - result["Overall Score"]) > 1:
            st.warning(f"Score mismatch for {startup['Company Name']}: GPT={result['Overall Score']}, Calculated={calculated_score}")
            result["Overall Score"] = calculated_score
        
        if result["Company"] != startup["Company Name"]:
            st.warning(f"Company name mismatch for {startup['Company Name']}: {result['Company']}")
            result["Summary"] = "Parsing failed - company name mismatch"
            return result
        
    except Exception as e:
        st.warning(f"JSON parsing error for {startup['Company Name']}: {str(e)}")
        result["Summary"] = f"Parsing failed - {str(e)}"
        return result
    
    return result

# Function to convert results to Excel
def results_to_excel(results: List[Dict]) -> bytes:
    data = [{
        "Company": r["Company"],
        "Technology": r["Technology"],
        "Ability": r["Ability"],
        "Summary": r["Summary"],
        "Relevancy to Retail": r["Relevancy to Retail"],
        "Category Management Score": r["Category Management Score"],
        "Category Management Reasoning": r["Category Management Reasoning"],
        "Product Development Score": r["Product Development Score"],
        "Product Development Reasoning": r["Product Development Reasoning"],
        "Offline Promotion Score": r["Offline Promotion Score"],
        "Offline Promotion Reasoning": r["Offline Promotion Reasoning"],
        "Supply Chain/Logistics Score": r["Supply Chain/Logistics Score"],
        "Supply Chain/Logistics Reasoning": r["Supply Chain/Logistics Reasoning"],
        "Store Operations Score": r["Store Operations Score"],
        "Store Operations Reasoning": r["Store Operations Reasoning"],
        "Overall Score": r["Overall Score"],
        "Category": r["Category"],
        "Industry": r["Industry"]
    } for r in results]
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Startup Analysis")
        workbook = writer.book
        worksheet = writer.sheets["Startup Analysis"]
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_length)
    
    return output.getvalue()

# Streamlit App
def main():
    st.title("CMU Spin-off Analysis for CJ Express")
    st.write("Upload the CMU Spin-off Companies and Pipeline PDF to analyze startups for CJ Express's retail goals.")
    
    uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
    
    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Extract startups from PDF
            startups = extract_startups_from_document("temp.pdf")
            st.write(f"Extracted {len(startups)} startups from the PDF (filtered to checklist).")
            with st.expander("Extracted Startups (Debug)"):
                for startup in startups:
                    st.write(f"Name: {startup['Company Name']}, Description: {startup['Description']}")
            
            if st.button("Analyze Startups"):
                with st.spinner("Analyzing startups with GPT..."):
                    results = analyze_with_gpt(startups, output_file="raw_gpt_outputs.json")
                
                st.subheader("Analysis Results")
                results_df = pd.DataFrame([{
                    "Company": r["Company"],
                    "Technology": r["Technology"],
                    "Ability": r["Ability"],
                    "Summary": r["Summary"],
                    "Relevancy to Retail": r["Relevancy to Retail"],
                    "Category Management Score": r["Category Management Score"],
                    "Category Management Reasoning": r["Category Management Reasoning"],
                    "Product Development Score": r["Product Development Score"],
                    "Product Development Reasoning": r["Product Development Reasoning"],
                    "Offline Promotion Score": r["Offline Promotion Score"],
                    "Offline Promotion Reasoning": r["Offline Promotion Reasoning"],
                    "Supply Chain/Logistics Score": r["Supply Chain/Logistics Score"],
                    "Supply Chain/Logistics Reasoning": r["Supply Chain/Logistics Reasoning"],
                    "Store Operations Score": r["Store Operations Score"],
                    "Store Operations Reasoning": r["Store Operations Reasoning"],
                    "Overall Score": r["Overall Score"],
                    "Category": r["Category"],
                    "Industry": r["Industry"]
                } for r in results])
                
                st.dataframe(results_df)
                
                # Generate Excel file
                excel_data = results_to_excel(results)
                st.download_button(
                    label="Download Analysis as Excel",
                    data=excel_data,
                    file_name="CMU_Startup_Analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.write("Raw GPT outputs have been saved to 'raw_gpt_outputs.json' for reference.")
        
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    main()