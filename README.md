# EU Policy Compliance Checker

An intelligent Policy Compliance Checker that analyzes internal policy documents against EU regulations (GDPR, AI Act, NIS2, etc.) and identifies discrepancies with cited articles.

## Features

- **Document Upload & Parsing**: Support for PDF, DOCX, and TXT files with semantic chunking
- **Multi-Agent Architecture**: Specialized agents for document parsing, regulation retrieval, comparison, citation extraction, and report generation
- **GraphRAG (Hybrid RAG)**: Combines vector similarity search with knowledge graph traversal for enhanced regulation retrieval
- **Compliance Comparison**: Automated comparison of policies against EU regulations with discrepancy detection
- **Citation Extraction**: Automatic extraction and validation of regulation article citations
- **Interactive UI**: Streamlit frontend for document upload, comparison visualization, and report generation
- **REST API**: FastAPI backend for programmatic access and integration
- **Dockerized Deployment**: Production-ready Docker containers for easy deployment
- **Comprehensive Reports**: PDF reports with compliance scores, discrepancies, citations, and actionable recommendations

## Architecture Overview

```
┌─────────────────┐
│  User Interface │
│  (Streamlit)    │
└────────┬────────┘
         │
┌────────▼──────────────────────────────────┐
│        Agent Orchestrator                 │
│     (LLM-Mesh Pattern)                    │
├───────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐      │
│  │  Document   │  │  Regulation  │      │
│  │   Agent     │  │    Agent     │      │
│  └──────┬──────┘  └──────┬───────┘      │
│         │                │              │
│  ┌──────▼─────────┬──────▼───────┐      │
│  │  Comparison    │  Citation    │      │
│  │    Agent       │    Agent     │      │
│  └──────┬─────────┴──────┬───────┘      │
│         │                │              │
│  ┌──────▼────────────────▼───────┐      │
│  │      Report Generator          │      │
│  └────────────────────────────────┘      │
└───────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────┐
│       Hybrid Retriever                    │
│  ┌─────────────┐  ┌──────────────┐      │
│  │   Vector    │  │  Knowledge   │      │
│  │   Search    │  │    Graph     │      │
│  │  (ChromaDB) │  │  (NetworkX)  │      │
│  └─────────────┘  └──────────────┘      │
└───────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────┐
│  EU Regulation Database                   │
│  (GDPR, AI Act, NIS2, DSA, DMA)          │
└───────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key
- Docker (optional, for containerized deployment)

### 1. Clone & Setup Environment

```bash
git clone <your_repo_url>
cd genai_final_project_leo_benjo
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file (copy from `env.example`) and set your key:

```env
OPENAI_API_KEY=sk-...
CHROMA_DIR=chroma_eu_laws
```

### 3. Run the Application

#### Streamlit Frontend (Recommended)

```bash
streamlit run streamlit_app.py
```

Access at: http://localhost:8501

#### FastAPI Backend

```bash
python api/main.py
# Or using uvicorn directly:
uvicorn api.main:app --reload
```

API docs at: http://localhost:8000/docs

#### Chainlit (Original Interface)

```bash
chainlit run app.py -w
```

## Docker Deployment

### Build and Run with Docker Compose

```bash
docker-compose up --build
```

This starts both:
- FastAPI backend on http://localhost:8000
- Streamlit frontend on http://localhost:8501

### Build Docker Image Manually

```bash
docker build -t compliance-checker .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... compliance-checker
```

## Usage

### Via Streamlit Interface

1. Open http://localhost:8501
2. Select regulations to check (GDPR, AI Act, NIS2, etc.)
3. Upload your policy document (PDF, DOCX, or TXT)
4. Click "Analyze Compliance"
5. View results:
   - Compliance score
   - Identified discrepancies
   - Regulation citations
   - Download PDF report

### Via REST API

#### Upload Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@your_policy.pdf"
```

Response:
```json
{
  "document_id": "uuid-here",
  "filename": "your_policy.pdf",
  "file_type": "PDF",
  "status": "uploaded"
}
```

#### Analyze Compliance

```bash
curl -X POST "http://localhost:8000/api/comparison/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "uuid-here",
    "regulation_types": ["GDPR", "AI Act"]
  }'
```

#### Get Analysis Results

```bash
curl "http://localhost:8000/api/comparison/{analysis_id}"
```

#### Download PDF Report

```bash
curl "http://localhost:8000/api/reports/{analysis_id}/pdf" \
  -o compliance_report.pdf
```

## Project Structure

```
genai_final_project_leo_benjo/
├── app.py                          # Chainlit application (original)
├── streamlit_app.py                # Streamlit frontend
├── document_parser.py              # Document parsing module
├── agent_orchestrator.py           # Multi-agent orchestrator
│
├── agents/                         # Multi-agent system
│   ├── base.py                    # Base agent class
│   ├── document_agent.py          # Document parsing agent
│   ├── regulation_agent.py        # Regulation retrieval agent
│   ├── comparison_agent.py        # Compliance comparison agent
│   ├── citation_agent.py          # Citation extraction agent
│   └── report_agent.py            # Report generation agent
│
├── comparison/                     # Comparison module
│   ├── comparator.py              # Core comparison logic
│   ├── discrepancy_detector.py    # Discrepancy detection
│   └── severity_assessor.py       # Severity classification
│
├── graphrag/                       # GraphRAG implementation
│   ├── entity_extractor.py        # Entity extraction
│   ├── relationship_builder.py    # Relationship building
│   ├── graph_store.py             # Graph storage
│   └── hybrid_retriever.py        # Hybrid retrieval
│
├── api/                            # FastAPI backend
│   ├── main.py                    # FastAPI app
│   ├── schemas.py                 # Pydantic models
│   └── routes/
│       ├── documents.py           # Document endpoints
│       ├── comparison.py          # Analysis endpoints
│       └── reports.py             # Report endpoints
│
├── docker/
│   ├── Dockerfile                 # Multi-stage Dockerfile
│   └── docker-compose.yml         # Docker Compose config
│
├── report_generator.py            # PDF report generator
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Key Technologies

| Component | Technology |
|-----------|-----------|
| **Multi-Agent System** | LLM-Mesh pattern with specialized agents |
| **GraphRAG** | Hybrid vector + graph retrieval |
| **Vector DB** | ChromaDB |
| **Knowledge Graph** | NetworkX (with JSON fallback) |
| **Embeddings** | OpenAI text-embedding-3-small |
| **LLM** | OpenAI GPT-4o-mini |
| **Frontend** | Streamlit |
| **Backend API** | FastAPI + Uvicorn |
| **PDF Generation** | ReportLab |
| **Document Parsing** | PyPDF2, python-docx |

## Multi-Agent Workflow

1. **Document Agent**: Parses uploaded policy document with semantic chunking
2. **Regulation Agent**: Retrieves relevant EU regulations via RAG
3. **Comparison Agent**: Compares policy content against regulations
4. **Citation Agent**: Extracts and validates article citations
5. **Report Agent**: Generates comprehensive compliance report

## GraphRAG Implementation

- **Entity Extraction**: Identifies articles, clauses, and requirements from regulations
- **Relationship Building**: Maps connections between policy elements and regulation articles
- **Hybrid Retrieval**: Combines vector similarity with graph traversal for better context
- **Citation Tracking**: Maintains article-level relationships for accurate citation

## API Endpoints

- `POST /api/documents/upload` - Upload policy document
- `GET /api/documents/{id}` - Get document info
- `POST /api/comparison/analyze` - Run compliance analysis
- `GET /api/comparison/{id}` - Get analysis results
- `GET /api/reports/{id}/pdf` - Download PDF report
- `GET /api/regulations` - List available regulations
- `GET /health` - Health check

## Evaluation

A dedicated `evaluation.ipynb` notebook is provided for:
- Testing RAG pipeline accuracy
- Validating citation extraction
- Measuring discrepancy detection performance
- Benchmarking system performance

## Future Improvements

- [ ] Multilingual support (FR/EN)
- [ ] Advanced graph visualization
- [ ] Batch document processing
- [ ] Integration with document management systems
- [ ] Fine-tuned models for compliance language
- [ ] Real-time collaboration features
- [ ] Compliance tracking over time

## Authors

Léo Bouchand, Benjamin Rasson

**Academic Project** — Applied AI & Data Science 2025

## License

See LICENSE file for details.