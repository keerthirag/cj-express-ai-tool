# CJ Express AI Innovation Suite

Welcome to the **CJ Express AI Innovation Suite**, a collection of Streamlit-based applications designed to empower **CJ Express** with cutting-edge tools for strategic decision-making, technology scouting, and innovation planning. This suite leverages AI, data analytics, and user-friendly interfaces to support CJ Express's goals of global expansion, operational efficiency, and enhanced customer experience over a 3-5 year horizon.

This README provides a detailed overview of each application, its functionality, setup instructions, and how to run the suite.

---

## Table of Contents

- [Overview](#overview)
- [Applications](#applications)
  - [CJ Express AI Agent](#cj-express-ai-agent-apppy)
  - [CMU Spin-off Analysis](#cmu-spin-off-analysis-cmu_techtransfer_startup_analysispy)
  - [M&A Strategic Analysis](#ma-strategic-analysis-ma_apppy)
  - [Patent Relevancy Analysis](#patent-relevancy-analysis-patent_apppy)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Applications](#running-the-applications)
- [Directory Structure](#directory-structure)
- [Usage Guide](#usage-guide)
  - [Accessing Features](#accessing-features)
  - [Expected Inputs and Outputs](#expected-inputs-and-outputs)
- [Troubleshooting](#troubleshooting)

---

## Overview

The CJ Express AI Innovation Suite is tailored to support CJ Express's strategic objectives in the retail sector, focusing on five key pillars:

- **Category Management**: Optimizing product assortment.
- **Product Development**: Creating innovative offerings.
- **Offline Promotion**: Enhancing in-store engagement.
- **Supply Chain/Logistics**: Improving distribution efficiency.
- **Store Operations**: Streamlining in-store processes.

Each application addresses a specific aspect of CJ Express's innovation strategy—from analyzing university spin-off startups to evaluating M&A opportunities and patent technologies. Built with Streamlit, these tools offer interactive, web-based interfaces that integrate AI (via OpenAI's API), data processing, and visualization to deliver actionable insights.

---

## Applications

### CJ Express AI Agent (`app.py`)

**Purpose**: A versatile AI assistant that allows CJ Express's team to expand the knowledge base, query information, and analyze pre-processed CMU startup data for technology scouting.

**Features**:

- **Dynamic Context Addition**: Upload PDFs or text files using a RAG framework with FAISS and Sentence Transformers.
- **Query Interface**: Ask questions about retail trends or customer behaviors using `gpt-4o-mini`.
- **Context Management**: View, download, or delete stored context files.
- **Tech Disruptor Analyzer**: Analyze `cmu_startups.xlsx` for tech disruptors.
- **Branding**: Displays CJ Express logo.
- **Data Preview and Download**: View/download the CMU startup analysis as Excel.

**Access**: Navigate via sidebar to:

- Add Context
- Ask a Question
- View Context
- Tech Disruptor Analyzer

**Use Case**:

- Upload a market research PDF.
- Ask: *“What are the top technologies for Supply Chain/Logistics?”*

---

### CMU Spin-off Analysis (`cmu_techtransfer_startup_analysis.py`)

**Purpose**: Analyze CMU spin-off startups to identify technologies aligned with CJ Express’s goals.

**Features**:

- **PDF Parsing** of CMU tech transfer PDF.
- **AI-Powered Analysis** using `gpt-4-turbo`.
- **Excel Output** with detailed tech analysis and scores.
- **Debugging** and **Downloadable Results**.

**Use Case**:

- Upload CMU spin-off PDF.
- Identify startups like Carnegie Robotics for supply chain automation.

---

### M&A Strategic Analysis (`ma_app.py`)

**Purpose**: Analyze M&A activity in the retail sector and generate strategic insights.

**Features**:

- **Excel Input** of M&A data.
- **RAG Analysis** with `gpt-3.5-turbo`.
- **Stacked Bar Chart** visualization of trends.
- **Chatbot** for ad-hoc M&A queries.
- **Excel Download** of enriched data.

**Use Case**:

- Upload M&A dataset.
- Ask: *“What are the benefits of acquiring e-commerce platforms?”*

---

### Patent Relevancy Analysis (`patent_app.py`)

**Purpose**: Evaluate patents for relevance to CJ Express’s goals.

**Features**:

- **Excel Input** of patent data.
- **AI Recommendations** using `gpt-3.5-turbo`.
- **Scoring Logic** with Priority Score.
- **Excel Download** and scoring explanation.

**Use Case**:

- Evaluate tech like contactless vital signs detection.
- Use Priority Score to decide Build vs Buy.

---

## Setup Instructions

### Prerequisites

- **Python**: ≥ 3.8  
- **Git**
- **OpenAI API Key**: Access to `gpt-3.5-turbo`, `gpt-4o-mini`, or `gpt-4-turbo`
- **macOS Users**: `libomp` via `brew install libomp` for FAISS

---

### Installation

**Clone the Repository**:

```bash
git clone https://github.com/keerthirag/cj-express-ai-tool.git
cd cj-express-ai-tool
```

**Create Virtual Environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install Dependencies**:

```bash
pip install -r requirements.txt
```

#### `requirements.txt` Includes:

```txt
streamlit==1.31.0
PyPDF2==3.0.1
sentence-transformers==2.7.0
faiss-cpu==1.8.0
numpy==1.26.4
openai==1.51.0
python-dotenv==1.0.1
pythainlp==5.0.4
pdfplumber==0.11.4
pandas==2.2.3
xlsxwriter==3.2.0
matplotlib
```

**Set Up Environment Variables**:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

**Prepare Data Directory**:

```bash
mkdir -p data
```

> Optional: Add `initial_context.txt` to `data/`

**Add CJ Express Logo**:

```bash
mkdir -p static
# Place your logo at static/cj_express_logo.png
```

---

### Running the Applications

Each application is a standalone Streamlit app:

```bash
# CJ Express AI Agent
streamlit run app.py

# CMU Spin-off Analysis
streamlit run cmu_techtransfer_startup_analysis.py

# M&A Strategic Analysis
streamlit run patent-and-ma-search/ma_app.py

# Patent Relevancy Analysis
streamlit run patent-and-ma-search/patent_app.py
```

**Access**:  
Go to `http://localhost:8501`

**API Keys**:  
- For `ma_app.py` & `patent_app.py`: enter API key in UI  
- For `app.py` & `cmu_techtransfer_startup_analysis.py`: ensure `.env` contains key

---

## Directory Structure

```plaintext
CJ-EXPRESS-AI-TOOL/
├── app.py
├── cmu_techtransfer_startup_analysis.py
├── patent-and-ma-search/
│   ├── ma_app.py
│   ├── patent_app.py
│   ├── venv/
├── data/
│   └── initial_context.txt
├── static/
│   └── cj_express_logo.png
├── requirements.txt
└── .env
```

---

## Usage Guide

### Accessing Features

- Navigate via the sidebar in each Streamlit app
- Upload files via UI components
- Interact with embedded chatbots and download results

### Expected Inputs and Outputs

| App                     | Input                          | Output                             |
|------------------------|--------------------------------|------------------------------------|
| `app.py`               | PDFs, TXT, Excel               | Answers, startup tech analysis     |
| `cmu_techtransfer...`  | CMU PDF                        | Excel with evaluated startups      |
| `ma_app.py`            | Excel with M&A deals           | Strategic insights, visuals, Excel |
| `patent_app.py`        | Patent Excel                   | Scores, strategy, Excel            |

---

## Troubleshooting

- **FAISS on macOS**: Ensure `libomp` is installed.
- **OpenAI API errors**: Check rate limits and model availability.
- **File not found**: Verify filenames and paths in `data/` and `static/`.

---

*Maintained by the CJ Express Innovation Team & Contributors.*
