# EU Policy Compliance Checker

An intelligent Regulatory Compliance Assistant that analyzes projects, company policies, or legal questions related to European law, GDPR, AI Act, and NIS2, and generates:
- A concise legal answer directly in the chat  
- A detailed compliance report in PDF format  
  (including compliance score, risk analysis, and actionable steps)

---

## Features

- **Retrieval-Augmented Generation (RAG)** with Chroma and OpenAI Embeddings
- **Automatic PDF report generator** (formatted and structured)
- **Interactive chatbot** built with [Chainlit](https://docs.chainlit.io/)
- **Dual-level intelligence**:
  - Short in-chat response for fast understanding
  - Full structured PDF with executive summary, compliance score, and next steps
- **Dynamic prompt logic**: no score is generated for general questions, only for detailed policy/project evaluations

---

## Architecture Overview

```
User <--> Chainlit Chat UI
       ↕
ChatOpenAI (gpt-4o-mini)
       ↕
Retriever (Chroma + OpenAI embeddings)
       ↕
Pre-processed EU Regulation Texts (PDF → Chunks)
       ↕
Report Generator (Markdown → PDF)
```

- Data: stored in `chroma_eu_laws/`
- Reports: generated dynamically on user queries
- Vector embeddings: `text-embedding-3-small`

---

## Installation

### 1. Clone & setup environment

```bash
git clone <your_repo_url>
cd genai_final_project_leo_benjo
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file (copy from `env.example`) and set your key:

```
OPENAI_API_KEY=sk-...
CHROMA_DIR=chroma_eu_laws
```

### 3. Run the app locally

```bash
chainlit run app.py -w
```

## How It Works

1. User enters a legal question or uploads policy content.
2. The app retrieves relevant EU legal texts using ChromaDB.
3. GPT-4o-mini analyzes and synthesizes the legal context.
4. The chatbot provides a short answer.
5. A full compliance report is generated (PDF).

## Evaluation Phase

A dedicated `evaluation.ipynb` notebook is provided to:

- Test the RAG pipeline across various queries
- Compare GPT answers vs expected legal interpretations
- Store results in a CSV for performance analysis

## Project Structure

```
genai_final_project_leo_benjo/
├── app.py                        # Chainlit main app
├── report_generator.py           # PDF generator module
├── chunking.ipynb                # PDF → text chunks
├── embedding_and_vector.ipynb    # Embedding creation + ChromaDB
├── rag.ipynb                     # RAG logic development
├── evaluation.ipynb              # Model performance analysis
├── eu_laws_chunks.jsonl          # Text chunks
├── chroma_eu_laws/               # Vector database
├── chainlit.md                   # Optional Chainlit config
├── requirements.txt              # Dependencies
├── .env.example                  # Example environment variables
├── .gitignore                    # Ignore venv, cache, artifacts
├── ruff.toml                     # Linting/formatting config
└── LICENSE
```

## Example Query

**Question:**

    Can I store photos of employees for internal authentication?

**Chat Answer:**

    Yes, you can store photos of employees for internal authentication under GDPR, 
    but you must adhere to specific legal requirements: ...

Full PDF report generated with compliance score, risk breakdown, and next steps.

## Technologies

| Component | Library |
|-----------|---------|
| Vector DB | Chroma |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | ChatOpenAI (gpt-4o-mini) |
| Interface | Chainlit |
| PDF Generator | ReportLab |
| Data | Official EU Regulation Texts (GDPR, AI Act, etc.) |

## Future Improvements

- Add multilingual support (FR/EN)
- Integrate document upload for company policies
- Add database of local EU Data Protection Authorities
- Fine-tune model on compliance language

---

**Authors:** Léo Bouchand, Benjamin Rasson  
**Academic Project** — Applied AI & Data Science 2025