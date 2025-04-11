# CJ Express AI Agent

A Streamlit-based AI tool for CJ Express's data and innovation team in Thailand. This tool allows the team to dynamically add context via PDFs or text, query the knowledge base, and view stored context. It uses a Retrieval-Augmented Generation (RAG) framework with Open AI's API for question answering.

## Features
- **Dynamic Context Addition**: Upload PDFs or text to expand the knowledge base.
- **Query Interface**: Ask questions and get answers grounded in the context, with improved accuracy and reasoning using the `gpt-4o-mini` model.
- **Context Retrieval**: View all stored files, their full content, and manage them (view, download, delete).
- **Branding**: Displays the CJ Express logo at the top (width: 150 pixels).
- **GitHub Ready**: Structured for easy deployment to GitHub.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Git
- An Open AI API key (with access to the `gpt-4o-mini` model)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/keerthirag/cj-express-ai-tool.git
   cd cj-express-ai-tool