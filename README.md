# CJ Express AI Innovation Suite

Welcome to the **CJ Express AI Innovation Suite**, a collection of Streamlit-based applications designed to empower CJ Express with cutting-edge tools for strategic decision-making, technology scouting, and innovation planning.

This suite leverages AI, data analytics, and user-friendly interfaces to support CJ Express's goals of global expansion, operational efficiency, and enhanced customer experience over a 3–5 year horizon.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Applications](#applications)
  - [CJ Express AI Agent (app.py)](#cj-express-ai-agent-apppy)
  - [CMU Spin-off Analysis (cmu_techtransfer_startup_analysis.py)](#cmu-spin-off-analysis-cmu_techtransfer_startup_analysispy)
  - [M&A Strategic Analysis (ma_app.py)](#ma-strategic-analysis-ma_apppy)
  - [Patent Relevancy Analysis (patent_app.py)](#patent-relevancy-analysis-patent_apppy)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Applications](#running-the-applications)
- [Directory Structure](#directory-structure)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🧭 Overview

The CJ Express AI Innovation Suite supports strategic objectives across five key pillars:

- **Category Management**: Optimizing product assortment.
- **Product Development**: Creating innovative offerings.
- **Offline Promotion**: Enhancing in-store engagement.
- **Supply Chain/Logistics**: Improving distribution efficiency.
- **Store Operations**: Streamlining in-store processes.

Each app in the suite addresses a specific aspect of CJ Express's innovation strategy. Built with Streamlit, they integrate AI (via OpenAI API), data processing, and interactive visualizations.

---

## ⚙️ Applications

### CJ Express AI Agent (`app.py`)

**Purpose**: A versatile AI assistant that allows the team to expand its knowledge base, query insights, and analyze CMU startup data.

**Features**:
- **Dynamic Context Addition** (RAG with FAISS & Sentence Transformers)
- **Query Interface** powered by `gpt-4o-mini`
- **Context Management** (upload, delete, view)
- **Tech Disruptor Analyzer** (interact with CMU startup data)
- **Branding**: CJ Express logo
- **Data Preview & Download**

**How It Works**:
- Uses SQLite + FAISS
- Embeds PDFs or text files
- Queries `cmu_startups.xlsx` via chatbot

**Use Case**:
> Upload a market research PDF → Ask, “What are the top technologies for Supply Chain/Logistics?”

---

### CMU Spin-off Analysis (`cmu_techtransfer_startup_analysis.py`)

**Purpose**: Analyze CMU spin-offs to find retail-relevant technologies.

**Features**:
- Parses tech transfer PDFs using `pdfplumber`
- AI evaluation (via `gpt-4-turbo`) across 5 pillars
- Scores (0–10) + Overall Score (0–100)
- Excel download with detailed output

**How It Works**:
- Extracts startup data → Sends to OpenAI → Scores & recommendations
- Outputs: `CMU_Startup_Analysis.xlsx`

**Use Case**:
> Discover startups like Carnegie Robotics for supply chain automation.

---

### M&A Strategic Analysis (`patent-and-ma-search/ma_app.py`)

**Purpose**: Analyze retail M&A trends to inform strategic moves.

**Features**:
- Upload M&A Excel file
- RAG-based learning & strategy per row
- Visual trends: Stacked bar chart by category/year
- Chatbot for insights
- Download enriched Excel

**Use Case**:
> Upload CP Group’s M&A dataset → Ask “What are the benefits of acquiring e-commerce platforms?”

---

### Patent Relevancy Analysis (`patent-and-ma-search/patent_app.py`)

**Purpose**: Evaluate patents for alignment with CJ Express’s goals.

**Features**:
- Upload patent Excel
- AI recommendations (Build vs. Buy)
- Scores: Impact, Readiness, Feasibility, Category Relevance
- Priority Score = `Impact * 0.5 + Readiness * 0.3 + Feasibility * 0.2`
- Download enriched Excel

**Use Case**:
> Evaluate tech like contactless vital sign detection for CX enhancement.

---

## 🛠 Setup Instructions

### Prerequisites

- **Python**: ≥ 3.8  
- **Git**
- **OpenAI API Key** (gpt-3.5-turbo / gpt-4o-mini / gpt-4-turbo for CMU analysis)
- **macOS**: `brew install libomp` (for FAISS)

---

### Installation

```bash
# Clone the repo
git clone https://github.com/keerthirag/cj-express-ai-tool.git
cd cj-express-ai-tool

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt