import streamlit as st
import PyPDF2
import sqlite3
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd
import io
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Open AI API key not found. Please set the OPENAI_API_KEY in the .env file.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# Set page configuration
st.set_page_config(page_title="CJ Express AI Agent", page_icon="static/cj_express_logo.png")

# Initialize components for RAG (used only for context pages)
try:
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
except Exception as e:
    st.error(f"Failed to load SentenceTransformer model: {e}")
    st.stop()

dimension = 768  # Dimension of paraphrase-multilingual-mpnet-base-v2 embeddings
index = faiss.IndexFlatL2(dimension)

# Initialize SQLite database
try:
    conn = sqlite3.connect('context.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS files 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, upload_date TEXT, content TEXT)''')
    conn.commit()
except Exception as e:
    st.error(f"Failed to initialize SQLite database: {e}")
    st.stop()

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Load initial context if not already in database
initial_context_path = 'data/initial_context.txt'
if os.path.exists(initial_context_path):
    cursor.execute("SELECT COUNT(*) FROM files WHERE name=?", (initial_context_path,))
    if cursor.fetchone()[0] == 0:
        try:
            with open(initial_context_path, 'r', encoding='utf-8') as f:
                text = f.read()
                cursor.execute("INSERT INTO files (name, upload_date, content) VALUES (?, ?, ?)",
                               (initial_context_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text))
                conn.commit()
                chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
                embeddings = model.encode(chunks)
                index.add(np.array(embeddings))
        except Exception as e:
            st.error(f"Failed to load initial context: {e}")
            st.stop()
else:
    st.warning("Initial context file (data/initial_context.txt) not found. Please ensure it exists.")

# Function to rebuild the FAISS index after deletion
def rebuild_faiss_index():
    global index
    index = faiss.IndexFlatL2(dimension)
    files = cursor.execute("SELECT content FROM files").fetchall()
    for file_content in files:
        content = file_content[0]
        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
        embeddings = model.encode(chunks)
        index.add(np.array(embeddings))

# File processing function for RAG
def process_file(file, file_type):
    try:
        if file_type == 'pdf':
            reader = PyPDF2.PdfReader(file)
            text = ''.join([page.extract_text() for page in reader.pages])
        else:
            text = file.read().decode('utf-8')
        
        text = text.replace('\n', ' ').strip()
        
        file_path = f"data/{file.name}"
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        embeddings = model.encode(chunks)
        
        global index
        index.add(np.array(embeddings))
        
        cursor.execute("INSERT INTO files (name, upload_date, content) VALUES (?, ?, ?)",
                       (file.name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text))
        conn.commit()
        return chunks
    except Exception as e:
        st.error(f"Failed to process file: {e}")
        return None

# Query handling for RAG (used for context pages)
def answer_query(query):
    try:
        query_embedding = model.encode([query])
        D, I = index.search(np.array(query_embedding), k=10)
        
        context = []
        for idx in I[0]:
            cursor.execute("SELECT content FROM files WHERE id=?", (idx+1,))
            result = cursor.fetchone()
            if result:
                context.append(result[0][:1000])
        
        context_text = "\n".join(context)
        
        system_prompt = (
            "You are an AI assistant for CJ Express, a convenience store chain in Thailand. "
            "Your task is to provide accurate and insightful answers based on the provided context. "
            "Follow these steps:\n"
            "1. Analyze the context carefully to identify relevant information.\n"
            "2. If the context is insufficient, clearly state that the information is not available and provide a general response based on your knowledge of retail trends.\n"
            "3. Structure your answer in a clear and concise manner, using bullet points or paragraphs as appropriate.\n"
            "4. Avoid speculation and focus on the provided context.\n"
            "5. If the query is ambiguous, ask for clarification or interpret it in the most logical way."
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context_text}\n\nQuestion: {query}"}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content.strip()
        answer = "\n".join(line.strip() for line in answer.splitlines() if line.strip())
        return answer
    except Exception as e:
        st.error(f"Failed to process query: {e}")
        return "An error occurred while processing your query."

# Function to load Excel file
def load_excel_file(file_path):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        df = df.dropna(how='all')
        df = df.fillna('')
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

# Streamlit UI
if os.path.exists("static/cj_express_logo.png"):
    st.image("static/cj_express_logo.png", width=150)
else:
    st.warning("CJ Express logo (static/cj_express_logo.png) not found. Please ensure it exists.")

st.title("CJ Express AI Agent")
st.markdown("---")

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select a page:",
        ["Add Context", "Ask a Question", "View Context", "Tech Disruptor Analyzer"],
        label_visibility="collapsed"
    )

# Main content
if page == "Add Context":
    st.header("Add Context")
    st.write("Upload a PDF or text file to expand the knowledge base for general queries.")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'txt'])
    if uploaded_file:
        with st.spinner("Processing file..."):
            result = process_file(uploaded_file, uploaded_file.type.split('/')[-1])
        if result:
            st.success("File processed and context updated successfully!")
        else:
            st.error("Failed to process the uploaded file.")

elif page == "Ask a Question":
    st.header("Ask a Question")
    st.write("Enter your question below to get insights from the knowledge base (PDFs and text files).")
    query = st.text_input("Your question:", placeholder="e.g., What are the shopping behaviors of Weekly Shoppers?")
    if query:
        with st.spinner("Processing..."):
            answer = answer_query(query)
        st.subheader("Answer:")
        st.write(answer)
        
        st.write("---")
        st.write("Was this answer helpful?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes"):
                st.success("Thank you for your feedback!")
        with col2:
            if st.button("No"):
                st.warning("Sorry to hear that. Please try rephrasing your question or adding more context.")

elif page == "View Context":
    st.header("View Stored Context")
    st.write("Below is the list of all stored context files in the knowledge base.")
    
    files = cursor.execute("SELECT id, name, upload_date, content FROM files").fetchall()
    if files:
        for file in files:
            with st.expander(f"File: {file[1]} (Uploaded: {file[2]})"):
                st.write(f"**File ID:** {file[0]}")
                st.text_area(
                    label="Content",
                    value=file[3],
                    height=300,
                    disabled=True,
                    label_visibility="collapsed"
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    file_path = f"data/{file[1]}"
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="Download File",
                                data=f,
                                file_name=file[1],
                                mime="application/octet-stream"
                            )
                    else:
                        st.warning(f"File {file[1]} not found in data/ directory.")
                with col2:
                    if file[1] != "data/initial_context.txt":
                        if st.button("Delete", key=f"delete_{file[0]}"):
                            cursor.execute("DELETE FROM files WHERE id=?", (file[0],))
                            conn.commit()
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            rebuild_faiss_index()
                            st.success(f"File {file[1]} deleted successfully!")
                            st.rerun()
                    else:
                        st.write("Initial context cannot be deleted.")

elif page == "Tech Disruptor Analyzer":
    st.header("CJ Express Tech Disruptor Analyzer")
    
    tab1, tab2 = st.tabs(["Query Analyzer", "About This Tool"])
    
    with tab1:
        st.subheader("Query CMU Startup Technologies")
        
        # Add hyperlink to reanalyzed Google Sheet
        st.markdown("""
        View or download the reanalyzed CMU startup data on Google Sheets:  
        [Reanalyzed CMU Startup Data](https://docs.google.com/spreadsheets/d/1v9JWnBLIFW_7KSN_fnbXbKA_u31qNGHcp89uyBNGY-k/edit?usp=sharing)
        """)
        
        # Load Excel file
        file_path = "cmu_startups.xlsx"
        if os.path.exists(file_path):
            if 'data' not in st.session_state:
                st.session_state.data = load_excel_file(file_path)
            st.success("Loaded cmu_startups.xlsx successfully!")
        else:
            uploaded_file = st.file_uploader("Upload Excel file (cmu_startups.xlsx)", type=["xlsx"])
            if uploaded_file:
                st.session_state.data = load_excel_file(uploaded_file)
                st.success("File uploaded successfully!")
        
        if st.session_state.get('data') is not None:
            st.subheader("Data Preview")
            st.dataframe(st.session_state.data, use_container_width=True)
            
            # Download button for local Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                st.session_state.data.to_excel(writer, index=False, sheet_name="Startup Analysis")
            st.download_button(
                label="Download Local Analysis as Excel",
                data=output.getvalue(),
                file_name="CMU_Startup_Analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Chatbot-style query interface
            st.subheader("Ask a Question")
            query = st.text_input(
                "Enter your question about the CMU startup data (e.g., 'What are the top 3 technologies for CJ Express in Category Management?')",
                key="query_input"
            )
            
            if query:
                try:
                    data_context = st.session_state.data.to_string()
                    
                    system_prompt = (
                        "You are an expert analyst for CJ Express, a Thai supermarket chain. "
                        "Your task is to answer questions based solely on the provided Excel data about CMU startup technologies. "
                        "Follow these steps:\n"
                        "1. Analyze the data carefully to identify relevant information.\n"
                        "2. If the data is insufficient, clearly state that the information is not available and avoid speculation.\n"
                        "3. Structure your answer in a conversational, chatbot-like style, using bullet points or paragraphs as appropriate.\n"
                        "4. Focus on the five retail pillars: Category Management, Product Development, Offline Promotion, Supply Chain/Logistics, and Store Operations.\n"
                        "5. For questions about top technologies, rank them based on the Overall Score and relevance to the specified pillar.\n"
                        "6. Provide clear, concise recommendations tailored to CJ Express's goals of global expansion and efficiency.\n"
                        "7. If the query specifies a category (e.g., Category Management), prioritize technologies with high scores in that category."
                    )
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Data Context:\n{data_context}\n\nQuestion: {query}"}
                        ],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    
                    answer = response.choices[0].message.content.strip()
                    answer = "\n".join(line.strip() for line in answer.splitlines() if line.strip())
                    response_text = f"Alright, let's dive into your question: '{query}'.\n\n{answer}\n\nFeel free to ask another question!"
                    
                    st.subheader("Answer")
                    st.write(response_text)
                except Exception as e:
                    st.error(f"Error generating response: {e}")
        else:
            st.warning("Please ensure the Excel file is available or upload it to proceed.")
    
    with tab2:
        st.subheader("About This Tool: Educational Overview")
        st.markdown("""
        ### Overview
        This Streamlit application, the **CJ Express Global Tech Disruptor Analyzer**, enables strategic decision-making for CJ Express, a Thai supermarket chain, by allowing users to query pre-analyzed data on Carnegie Mellon University (CMU) spin-off startups. The tool ingests an Excel file containing detailed analyses of startup technologies and their relevance to CJ Express’s five key retail pillars: Category Management, Product Development, Offline Promotion, Supply Chain/Logistics, and Store Operations. Users can ask questions like “What are the top three technologies for CJ Express in Category Management?” to receive tailored recommendations for technology adoption and innovation.

        ### Data Sourcing and Analysis Process
        The data in the Excel file (`cmu_startups.xlsx`) originates from CMU’s tech transfer office, which supports the commercialization of university research through spin-off startups. The process to compile and analyze this data involved the following steps:

        1. **Data Collection**:
           - A separate tool (hosted on [GitHub](https://github.com/keerthirag/cj-express-ai-tool/blob/main/cmu_techtransfer_startup_analysis.py)) was used to scrape publicly available information from CMU’s tech transfer office, including startup profiles, technology descriptions, and sector classifications.
           - Sources included CMU’s tech transfer website, startup pages, and related publications, focusing on startups in categories like Chemistry and Materials Science, Cleantech/Energy, Electronics/Semiconductors, Medical Devices/Biotech, Robotics, Software and AI, and Social Ventures.
           - The scraping tool extracted details such as company names, technologies, abilities, and industry categories, ensuring compliance with web scraping best practices (e.g., respecting robots.txt, using browser-like headers).

        2. **Data Analysis**:
           - The scraped data was processed to assess each startup’s relevance to CJ Express’s retail operations. This involved mapping technologies to the five retail pillars using a scoring system.
           - For each startup, scores (0–10) were assigned for each pillar based on potential impact and feasibility, with weighted calculations to compute an Overall Score (0–100). For example, weights were: Category Management (0.5), Product Development (0.5), Offline Promotion (0.3), Supply Chain/Logistics (0.2), and Store Operations (0.1).
           - Contextual reasoning was developed for each score, explaining how the technology could benefit CJ Express (e.g., improving supply chain efficiency or enhancing in-store engagement).
           - The analysis was compiled into the Excel file, with columns for Company, Technology, Ability, Summary, Relevancy to Retail, pillar-specific scores and reasoning, Overall Score, Category, and Industry.

        3. **Tool Development**:
           - This Streamlit app was built to ingest the analyzed Excel file and provide an interactive interface for querying the data.
           - The app leverages an LLM to interpret user questions and generate responses based solely on the Excel data, ensuring recommendations are grounded in the pre-analyzed information.
           - The tool supports queries like ranking technologies by pillar, identifying high-impact startups, or assessing strategic fit for CJ Express’s global expansion goals.

        ### Purpose of This Tool
        The CJ Express Global Tech Disruptor Analyzer serves as a decision-support tool for CJ Express’s innovation strategy. By querying the pre-analyzed data, users can:
        - Identify high-potential technologies for adoption in specific retail areas (e.g., Category Management, Store Operations).
        - Evaluate startups based on their Overall Score and pillar-specific relevance to prioritize partnerships or investments.
        - Gain insights into how CMU’s cutting-edge technologies can support CJ Express’s goals of global expansion, operational efficiency, and enhanced customer experience.

        For example, a query like “What are the top three technologies for Supply Chain/Logistics?” will return startups with the highest scores in that pillar, along with reasoning on how their technologies (e.g., AI-driven logistics optimization) can benefit CJ Express.

        ### Future Scope
        The current tool is tailored to CMU spin-off startups, but its framework can be expanded to include other universities’ tech transfer ecosystems, such as MIT, Stanford, or the University of Pittsburgh. Potential enhancements include:

        - **Multi-University Data Integration**:
          - Extend the separate scraping tool to collect data from additional university tech transfer offices, standardizing data formats to enable cross-university comparisons.
          - Develop a unified database of startup technologies across institutions, allowing CJ Express to explore a broader innovation landscape.

        - **Advanced Query Capabilities**:
          - Implement filters for industry, stage (e.g., Early-Stage, Venture-Backed), or specific technologies (e.g., AI, robotics).
          - Add support for complex queries, such as “Compare technologies for Store Operations across Cleantech and Software industries.”

        - **Automated Updates**:
          - Schedule periodic scraping to refresh the dataset with new startups or updated information.
          - Integrate real-time patent or publication data to capture emerging technologies.

        - **Integration with Other Tools**:
          - Link the analyzer to CJ Express’s internal systems for seamless integration with strategic planning or procurement processes.
          - Develop APIs to connect with external innovation platforms or startup databases.

        - **Scalability**:
          - Deploy the tool on a cloud platform (e.g., Streamlit Cloud) for enterprise-wide access across CJ Express’s global teams.
          - Create user roles (e.g., analyst, executive) with customized dashboards for different decision-making needs.

        ### Separate Scraping and Analysis Tool
        The data collection and analysis were performed using a separate Python-based tool, available on [GitHub](https://github.com/keerthirag/cj-express-ai-tool/blob/main/cmu_techtransfer_startup_analysis.py). This tool includes:
        - Web scraping scripts to extract startup data from CMU’s tech transfer office and related websites.
        - Analysis pipelines to score technologies and generate pillar-specific insights, leveraging AI for contextual reasoning.
        - Export functionality to produce the Excel file (`cmu_startups.xlsx`) used by this Streamlit app.

        Users interested in replicating or extending the data collection process can refer to the GitHub repository for documentation and source code.

        ### Conclusion
        The CJ Express Global Tech Disruptor Analyzer empowers CJ Express to make data-driven decisions by querying a comprehensive dataset of CMU spin-off startups. By focusing on pre-analyzed data, the tool eliminates the need for real-time scraping or analysis, providing a user-friendly interface for strategic innovation planning. Its educational design ensures users understand the data’s origins and potential, while the future scope outlines a path for broader adoption across other universities and enhanced functionalities.

        For questions or support, contact the CJ Express innovation team or refer to the GitHub repository for technical details.
        """)