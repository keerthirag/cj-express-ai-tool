import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Streamlit app title
st.title("CJ Express M&A Strategic Analysis")

# Create tabs
tab1, tab2 = st.tabs(["M&A Analysis Tool", "About This Tool"])

# Tab 1: M&A Analysis Tool (unchanged functionality)
with tab1:
    st.markdown("""
    This tool analyzes mergers and acquisitions (M&A) in the convenience store and retail sectors to provide strategic insights for CJ Express. Upload an Excel file to get recommendations, trends, and learnings. Use the chatbot to explore M&A questions further.
    """)
    
    st.markdown("""
        View or download the mergers & aquisition sheet here:  
        [Mergers & Aquisition Data](https://docs.google.com/spreadsheets/d/1Z4N-tyv4-yBQ186kmXyTAiwrncmQoffu/edit?gid=59682269#gid=59682269)
        """)

    # Input for OpenAI API key
    api_key = st.text_input("Enter your OpenAI API Key", type="password")

    # File uploader for Excel sheet
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    

  

    # CJ Express context
    CJ_EXPRESS_CONTEXT = """
    CJ Express, a Thai supermarket chain, aims to disrupt global retail with high-tech solutions. Targets: mid-high to low-income, multi-generational, diverse lifestyles (e.g., trendy women, pet lovers). Focus: (1) Category Management (optimizing product assortment), (2) Product Development (innovative offerings), (3) Offline Promotion (in-store engagement), (4) Supply Chain/Logistics (efficient distribution), (5) Store Operations (streamlined processes). Goals: global expansion, efficiency, customer experience (3-5 years).
    """

    # RAG Prompt for Learnings and Strategy
    RAG_PROMPT = """
    You are a retail M&A strategist for CJ Express, a Thai supermarket chain.
    Company Context: {CJ_EXPRESS_CONTEXT}
    M&A Data: {MNA_DATA}
    Additional Context: In Thailand, convenience store M&A trends show consolidation (e.g., CP Group's 2020 acquisition of Tesco Lotus for $10B+ added 2,000+ stores), focus on tech (e.g., robotics, e-commerce), and regional expansion. Globally, convenience and grocery sectors prioritize automation, digital engagement, and market presence.

    Instructions:
    1. Analyze the M&A data (Buyer, Seller, Year, Category, Value Added).
    2. Identify learnings for CJ Express (e.g., tech adoption, market expansion).
    3. Suggest a strategy for CJ Express based on the acquisition and trends (e.g., acquire similar tech, partner for scale).
    4. Return a JSON object with "Learnings" (string) and "Strategy" (string).
    """

    # Chatbot Prompt
    CHAT_PROMPT = """
    You are a retail M&A expert assisting CJ Express. Based on the provided M&A data and trends (Thailand: consolidation, tech focus; Global: automation, digital engagement), answer the user's question about mergers and acquisitions. Keep responses concise and strategic.
    M&A Data: {MNA_DATA}
    Question: {QUESTION}
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

        # Process each M&A row with RAG
        learnings_strategy_col = []
        for index, row in df.iterrows():
            mna_data = f"Buyer: {row['Buyer Company']}\nSeller: {row['Seller Company']}\nYear: {row['Year']}\nCategory: {row['Category']}\nValue Added: {row['Value Added']}"
            full_prompt = RAG_PROMPT.format(CJ_EXPRESS_CONTEXT=CJ_EXPRESS_CONTEXT, MNA_DATA=mna_data)

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": full_prompt}],
                "temperature": 0.3
            }

            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    json_response = json.loads(response.json()["choices"][0]["message"]["content"])
                    learnings_strategy_col.append(json.dumps(json_response))
                else:
                    st.error(f"API request failed for row {index}: {response.text}")
                    learnings_strategy_col.append('{"Learnings": "Error", "Strategy": "N/A"}')
            except Exception as e:
                st.error(f"Error processing row {index}: {str(e)}")
                learnings_strategy_col.append('{"Learnings": "Error", "Strategy": "N/A"}')

        # Add learnings and strategy to DataFrame
        df["Learnings_and_Strategy"] = learnings_strategy_col

        # Visualize trends
        st.write("### M&A Trends Over Years")
        category_counts = df.groupby(['Year', 'Category']).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 6))
        category_counts.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title("M&A Categories by Year")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Acquisitions")
        plt.legend(title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig)

        # Display updated DataFrame
        st.write("### Analysis Results")
        st.write("Each row includes learnings and strategies tailored to CJ Express. Download the updated Excel for full details.")
        st.dataframe(df)

        # Download updated Excel file
        output_file = f"mna_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        with open(output_file, "rb") as file:
            st.download_button("Download Updated Excel", file, file_name=output_file)

        # Chatbot Section
        st.write("### Ask About M&A Trends")
        question = st.text_input("Enter your question about M&A (e.g., 'What tech should CJ acquire?')")
        if question:
            chat_data = "\n".join(df.apply(lambda row: f"Buyer: {row['Buyer Company']}, Seller: {row['Seller Company']}, Year: {row['Year']}, Category: {row['Category']}", axis=1))
            chat_prompt = CHAT_PROMPT.format(MNA_DATA=chat_data, QUESTION=question)
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": chat_prompt}],
                "temperature": 0.3
            }
            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    answer = response.json()["choices"][0]["message"]["content"]
                    st.write(f"**Answer**: {answer}")
                else:
                    st.error(f"Chat API request failed: {response.text}")
            except Exception as e:
                st.error(f"Error in chatbot: {str(e)}")
    else:
        st.write("Please upload an Excel file and provide your OpenAI API key to proceed.")

# Tab 2: Explanation of the Tool
with tab2:
    st.header("About This Tool")
    st.markdown("""
    This section explains how the CJ Express M&A Strategic Analysis tool works and why it was designed this way.

    ### How It Works
    - **Excel Input Processing**:
      - Users upload an Excel file with M&A data (e.g., Buyer Company, Seller Company, Year, Category, Value Added).
      - The tool reads this into a DataFrame for analysis, ensuring compatibility with your data.
    - **RAG Framework**:
      - Uses Retrieval-Augmented Generation (RAG) via OpenAI API to combine Excel data with Thailand/global M&A trends.
      - Generates JSON with "Learnings" and "Strategy" for each row, added as a new column.
    - **Output Generation**:
      - Each M&A row gets a JSON string (e.g., {"Learnings": "Automation boosts efficiency", "Strategy": "Acquire robotics tech"}).
    - **Visualization**:
      - Displays a stacked bar chart of M&A categories by year, showing trends like automation or consolidation.
    - **Chatbot Functionality**:
      - Offers an interactive Q&A interface for M&A questions (e.g., “What tech should CJ acquire?”), using the same API.
    - **Excel Download**:
      - Outputs an updated Excel file with the original data plus "Learnings_and_Strategy", timestamped for tracking.
    - **Streamlit Interface**:
      - Combines table, chart, and chatbot in a user-friendly UI with guidance for ease of use.
    - **Error Handling**:
      - Includes try-except blocks to catch API failures and provide fallback values, ensuring the app doesn’t crash.

    ### What Is Working
    - **Data Integration**: Processes your Excel data fully, leveraging all columns for insights.
    - **Strategic Insights**: Delivers tailored learnings and strategies aligned with CJ Express’s goals (e.g., efficiency).
    - **Trend Visualization**: Bar chart highlights actionable trends (e.g., tech adoption rising since 2020).
    - **Interactive Q&A**: Chatbot enhances exploration with accurate, context-aware responses.
    - **Output Flexibility**: Provides in-app results and downloadable Excel for both real-time and offline use.
    - **Stability**: Error handling ensures smooth operation, even with partial failures.

    ### Thinking Behind the Design
    - **Why Use RAG?**:
      - Combines Excel data with broader trends for richer insights, avoiding complex web scraping for simplicity.
      - *Rationale*: CJ needs both specific acquisition lessons and market context to strategize effectively.
    - **Why JSON Output?**:
      - Structured format ensures clarity and future extensibility, added as a column to preserve original data.
      - *Rationale*: Practical for team review or integration into other systems.
    - **Why Include a Chatbot?**:
      - Adds flexibility for ad-hoc questions, making the tool dynamic and user-friendly.
      - *Rationale*: Empowers CJ to explore beyond static outputs without extra steps.

    ### Strategic Value for CJ Express
    - **Learning from M&A**: Identifies takeaways (e.g., Walmart’s robotics = efficiency) relevant to CJ’s focus areas.
    - **Trend Awareness**: Highlights shifts (e.g., automation, consolidation) to guide acquisition targets.
    - **Prioritization**: Strategies suggest specific moves (e.g., “Acquire robotics tech”) for decision-making.
    - **Flexibility**: Chatbot allows “what if” exploration, refining strategies dynamically.
    """)
