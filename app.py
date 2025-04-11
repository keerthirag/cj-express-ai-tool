import streamlit as st
import PyPDF2
import sqlite3
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import pythainlp
from pythainlp.tokenize import word_tokenize

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Open AI API key not found. Please set the OPENAI_API_KEY in the .env file.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# Initialize components
try:
    # Use a multilingual embedding model for better Thai support
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
                # Process initial context into embeddings with larger chunks
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
    # Reset the FAISS index
    index = faiss.IndexFlatL2(dimension)
    # Re-add embeddings for all remaining files
    files = cursor.execute("SELECT content FROM files").fetchall()
    for file_content in files:
        content = file_content[0]
        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
        embeddings = model.encode(chunks)
        index.add(np.array(embeddings))

# File processing function
def process_file(file, file_type):
    try:
        if file_type == 'pdf':
            reader = PyPDF2.PdfReader(file)
            text = ''.join([page.extract_text() for page in reader.pages])
        else:
            text = file.read().decode('utf-8')
        
        # Clean and tokenize text (support Thai)
        text = text.replace('\n', ' ').strip()
        tokens = word_tokenize(text, engine='newmm')
        cleaned_text = ' '.join(tokens)
        
        # Save raw file
        file_path = f"data/{file.name}"
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        
        # Chunk text for embeddings with larger chunks
        chunks = [cleaned_text[i:i+1000] for i in range(0, len(cleaned_text), 1000)]
        embeddings = model.encode(chunks)
        
        # Update FAISS index
        global index
        index.add(np.array(embeddings))
        
        # Store metadata in SQLite
        cursor.execute("INSERT INTO files (name, upload_date, content) VALUES (?, ?, ?)",
                       (file.name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), cleaned_text))
        conn.commit()
        return chunks
    except Exception as e:
        st.error(f"Failed to process file: {e}")
        return None

# Query handling with improved RAG
def answer_query(query):
    try:
        # Embed the query
        query_embedding = model.encode([query])
        # Retrieve top 10 chunks for broader context
        D, I = index.search(np.array(query_embedding), k=10)

        # Fetch relevant context
        context = []
        for idx in I[0]:
            cursor.execute("SELECT content FROM files WHERE id=?", (idx+1,))
            result = cursor.fetchone()
            if result:
                context.append(result[0][:1000])  # Limit each chunk to 1000 characters
        
        context_text = "\n".join(context)
        
        # Improved prompt with step-by-step reasoning
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
        
        # Call Open AI API with a more advanced model (if available)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-3.5-turbo-16k for better context handling
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context_text}\n\nQuestion: {query}"}
            ],
            max_tokens=1000,  # Increase token limit for more detailed answers
            temperature=0.7  # Balanced creativity and accuracy
        )
        
        # Post-process the answer for better readability
        answer = response.choices[0].message.content.strip()
        # Replace multiple newlines with a single newline for cleaner formatting
        answer = "\n".join(line.strip() for line in answer.splitlines() if line.strip())
        return answer
    except Exception as e:
        st.error(f"Failed to process query: {e}")
        return "An error occurred while processing your query."

# Streamlit UI
st.set_page_config(page_title="CJ Express AI Agent", page_icon="static/cj_express_logo.png")

# Display logo
if os.path.exists("static/cj_express_logo.png"):
    st.image("static/cj_express_logo.png", width=150)
else:
    st.warning("CJ Express logo (static/cj_express_logo.png) not found. Please ensure it exists.")

# Add a header with a divider for better separation
st.title("CJ Express AI Agent")
st.markdown("---")

# Sidebar for navigation with a cleaner layout
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select a page:",
        ["Add Context", "Ask a Question", "View Context"],
        label_visibility="collapsed"  # Hide the default label for a cleaner look
    )

# Main content area
if page == "Add Context":
    st.header("Add Context")
    st.write("Upload a PDF or text file to expand the knowledge base.")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'txt'], help="Supported formats: PDF, TXT")
    if uploaded_file:
        with st.spinner("Processing file..."):
            result = process_file(uploaded_file, uploaded_file.type.split('/')[-1])
        if result:
            st.success("File processed and context updated successfully!")
        else:
            st.error("Failed to process the uploaded file.")

elif page == "Ask a Question":
    st.header("Ask a Question")
    st.write("Enter your question below to get insights from the knowledge base.")
    query = st.text_input("Your question:", placeholder="e.g., What are the shopping behaviors of Weekly Shoppers?")
    if query:
        with st.spinner("Processing..."):
            answer = answer_query(query)
        st.subheader("Answer:")
        st.write(answer)
        
        # Add feedback mechanism
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
    st.write("Below is the list of all stored context files in the knowledge base. You can view, download, or delete files as needed.")

    files = cursor.execute("SELECT id, name, upload_date, content FROM files").fetchall()
    if files:
        for file in files:
            with st.expander(f"File: {file[1]} (Uploaded: {file[2]})"):
                # Display file metadata
                st.write(f"**File ID:** {file[0]}")
                
                # Display full content with preserved formatting
                st.write("**Content:**")
                st.text_area(
                    label="Content",
                    value=file[3],
                    height=300,
                    disabled=True,
                    label_visibility="collapsed"
                )

                # Create two columns for buttons
                col1, col2 = st.columns([1, 1])

                # Download button
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

                # Delete button
                with col2:
                    if file[1] != "data/initial_context.txt":  # Prevent deletion of initial context
                        if st.button("Delete", key=f"delete_{file[0]}"):
                            # Delete from SQLite
                            cursor.execute("DELETE FROM files WHERE id=?", (file[0],))
                            conn.commit()
                            
                            # Delete the file from data/ directory if it exists
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            
                            # Rebuild the FAISS index
                            rebuild_faiss_index()
                            
                            st.success(f"File {file[1]} deleted successfully!")
                            st.rerun()  # Refresh the page to update the list
                    else:
                        st.write("Initial context cannot be deleted.")
    else:
        st.info("No context available yet. Upload files to add context.")