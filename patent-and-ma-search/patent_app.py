import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# Streamlit app title and description
st.title("Patent Relevancy Analysis for CJ Express")
st.markdown("""
This tool analyzes patents to help CJ Express prioritize technologies for global expansion, efficiency, and customer experience. Upload an Excel file with patent details to get strategic recommendations and scores.
""")

st.markdown("""
        View or download the patent data here:  
        [Patent Data](https://docs.google.com/spreadsheets/d/1JPxWXzFZZOjAOamRe43H6XuOfITbcAFM/edit?gid=2127879699#gid=2127879699)
        """)

# Input for OpenAI API key
api_key = st.text_input("Enter your OpenAI API Key", type="password")

# File uploader for Excel sheet
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

# Company context
CJ_EXPRESS_CONTEXT = """
CJ Express, a Thai supermarket chain, aims to disrupt global retail with high-tech solutions. Targets: mid-high to low-income, multi-generational, diverse lifestyles (e.g., trendy women, pet lovers). Focus: (1) Category Management (optimizing product assortment), (2) Product Development (innovative offerings), (3) Offline Promotion (in-store engagement), (4) Supply Chain/Logistics (efficient distribution), (5) Store Operations (streamlined processes). Goals: global expansion, efficiency, customer experience (3-5 years).
"""

# Categories to evaluate
CATEGORIES = [
    "Category Management",
    "Price and Promotion Management",
    "Product Placement",
    "Retail Management",
    "Store Operations",
    "Supply Chain and Logistics",
    "Contactless Vital Sign Detection"
]

# Strategic LLM prompt (corrected to avoid KeyError)
PROMPT = """
You are a retail strategy expert evaluating patents for CJ Express, a Thai supermarket chain.
Company Context: {CJ_EXPRESS_CONTEXT}
Patent Data: {PATENT_DATA}
Categories:
- Category Management: Optimizing product assortment
- Price and Promotion Management: Dynamic pricing and promotions
- Product Placement: Enhancing in-store product layouts
- Retail Management: Overall operational efficiency
- Store Operations: Streamlining in-store processes
- Supply Chain and Logistics: Efficient distribution
- Contactless Vital Sign Detection: Customer experience innovations

Instructions:
1. Analyze the patent’s description and application.
2. Provide a strategic recommendation (max 50 words) tailored to CJ Express’s goals (global expansion, efficiency, customer experience), including a Build vs. Buy suggestion.
3. Assign scores (0-100):
   - Impact: How much it improves CJ’s goals (high if aligns with focus areas).
   - Readiness: Technology maturity (concept=20, prototype=50, market-ready=90).
   - Feasibility: Ease of implementation (cost, time, build vs. buy).
   - Category Impact: Impact per category (high if matches application).
4. Return a JSON object with: "Patent Number", "Recommendation", "Priority_Score" (Impact * 0.5 + Readiness * 0.3 + Feasibility * 0.2), "Impact", "Readiness", "Feasibility", and "Category_Impact" as a dictionary of category scores.
"""

if uploaded_file and api_key:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)
    st.write("Uploaded Data Preview:")
    st.dataframe(df)

    # OpenAI API endpoint and headers
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Process each patent
    results = []
    for index, row in df.iterrows():
        patent_data = f"Patent Number: {row['Patent Number']}\nPatent Name: {row['Patent name']}\nWhat it does: {row['What it does']}\nApplication: {row['Application']}"
        full_prompt = PROMPT.format(CJ_EXPRESS_CONTEXT=CJ_EXPRESS_CONTEXT, PATENT_DATA=patent_data)

        # Prepare payload for OpenAI API
        payload = {
            "model": "gpt-3.5-turbo",  # Change to "gpt-4" if you have access
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.3
        }

        # Make the API request
        response = requests.post(url, headers=headers, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse JSON response
            json_response = json.loads(response.json()["choices"][0]["message"]["content"])
            results.append(json_response)
        else:
            st.error(f"API request failed for patent {row['Patent Number']}: {response.text}")
            continue

    # Append results to DataFrame
    recommendation_col = []
    priority_score_col = []
    impact_col = []
    readiness_col = []
    feasibility_col = []
    category_impact_cols = {cat: [] for cat in CATEGORIES}

    for result in results:
        recommendation_col.append(result["Recommendation"])
        priority_score_col.append(result["Priority_Score"])
        impact_col.append(result["Impact"])
        readiness_col.append(result["Readiness"])
        feasibility_col.append(result["Feasibility"])
        for cat in CATEGORIES:
            category_impact_cols[cat].append(result["Category_Impact"][cat])

    df["Strategic Recommendation"] = recommendation_col
    df["Priority Score"] = priority_score_col
    df["Impact"] = impact_col
    df["Readiness"] = readiness_col
    df["Feasibility"] = feasibility_col
    for cat in CATEGORIES:
        df[f"{cat} Impact"] = category_impact_cols[cat]

    # Display scoring logic explanation
    st.write("### Scoring Logic Explained")
    st.markdown("""
    - **Priority Score (0-100)**: Overall patent priority = (Impact * 0.5) + (Readiness * 0.3) + (Feasibility * 0.2).
      - Higher scores = top priorities for CJ Express.
    - **Impact (0-100)**: How much the patent improves CJ’s goals (expansion, efficiency, customer experience).
    - **Readiness (0-100)**: Technology maturity (concept=20, prototype=50, market-ready=90).
    - **Feasibility (0-100)**: Ease of implementation (cost, time, build vs. buy).
    - **Category Impact (0-100)**: Impact per category (high if aligns with patent’s application).
    - **Recommendation**: Strategic action (max 50 words) with Build vs. Buy suggestion.
    """)

    # Display updated DataFrame
    st.write("### Analysis Results")
    st.write("Sort by 'Priority Score' to prioritize patents. High scores indicate impactful, ready, and feasible technologies.")
    st.dataframe(df)

    # Download updated Excel file
    output_file = f"patent_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(output_file, index=False)
    with open(output_file, "rb") as file:
        st.download_button("Download Updated Excel", file, file_name=output_file)

else:
    st.write("Please upload an Excel file and provide your OpenAI API key to proceed.")