# EU Policy Compliance Checker
## Multi-Agent System with GraphRAG

**Authors:** Léo Bouchand, Benjamin Rasson  
**Academic Project** — Applied AI & Data Science 2025

---

## Project Overview

### Problem Statement
- Companies need to ensure internal policies comply with EU regulations
- Manual compliance checking is time-consuming and error-prone
- Need for automated comparison with specific article citations

### Solution
Intelligent Policy Compliance Checker that:
- Analyzes internal policy documents against EU regulations
- Flags discrepancies with cited articles
- Generates comprehensive compliance reports

---

## Architecture: Multi-Agent System

### LLM-Mesh Pattern
```
Orchestrator
    ├── Document Agent      (Parsing & Chunking)
    ├── Regulation Agent    (RAG Retrieval)
    ├── Comparison Agent    (Compliance Analysis)
    ├── Citation Agent      (Article Extraction)
    └── Report Agent        (PDF Generation)
```

**Benefits:**
- Specialized agents for each task
- Modular and extensible
- Parallel processing capabilities

---

## Architecture: GraphRAG

### Hybrid Retrieval Approach

**Vector RAG (Baseline):**
- Semantic similarity search
- Fast retrieval of relevant documents

**Knowledge Graph:**
- Entity extraction (articles, clauses)
- Relationship mapping
- Article-level citations

**Hybrid Combination:**
- Vector search for initial retrieval
- Graph traversal for context enhancement
- Better citation accuracy

---

## Key Features

### 1. Document Processing
- Support for PDF, DOCX, TXT
- Semantic chunking with structure preservation
- Metadata extraction

### 2. Compliance Comparison
- Automated policy vs. regulation comparison
- Discrepancy detection with severity classification
- Missing requirement identification

### 3. Citation Extraction
- Automatic article number extraction
- Validation against regulation database
- Context-aware citation meaning

### 4. Report Generation
- Comprehensive PDF reports
- Compliance scores (0-100)
- Actionable recommendations
- Article-by-article breakdown

---

## Technical Implementation

### Multi-Agent Communication
- Shared state management
- Message passing protocol
- Agent coordination via orchestrator

### GraphRAG Components
- Entity Extractor (LLM + Pattern-based)
- Relationship Builder (Semantic + Citation-based)
- Graph Store (NetworkX with JSON fallback)
- Hybrid Retriever (Vector + Graph)

### Frontend & API
- Streamlit UI for interactive analysis
- FastAPI REST API for programmatic access
- Docker containerization for deployment

---

## Demo Workflow

### Step 1: Upload Policy Document
- User uploads internal policy (PDF/DOCX/TXT)
- System parses with semantic chunking

### Step 2: Regulation Retrieval
- RAG system retrieves relevant EU regulations
- Graph enhances with article-level context

### Step 3: Compliance Analysis
- Multi-agent system compares policy vs. regulations
- Identifies discrepancies and missing requirements

### Step 4: Report Generation
- Generates comprehensive PDF report
- Includes compliance score, citations, recommendations

---

## Results & Evaluation

### Metrics
- **Citation Accuracy**: Automatic extraction and validation
- **Discrepancy Detection**: Severity-based classification
- **Compliance Scoring**: Automated 0-100 scoring
- **Processing Speed**: Multi-agent parallel processing

### Supported Regulations
- GDPR (General Data Protection Regulation)
- AI Act (Artificial Intelligence Act)
- NIS2 (Network and Information Systems Directive 2)
- DSA (Digital Services Act)
- DMA (Digital Markets Act)

---

## Deliverables

### Code Components
- ✅ Multi-agent system implementation
- ✅ GraphRAG with hybrid retrieval
- ✅ Streamlit frontend interface
- ✅ FastAPI REST API
- ✅ Docker containerization
- ✅ Document parsing module
- ✅ Report generation system

### Documentation
- ✅ Comprehensive README
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Code documentation with docstrings
- ✅ Docker deployment guide

### Presentation
- ✅ Architecture overview
- ✅ Technical implementation details
- ✅ Demo workflow
- ✅ Results and evaluation

---

## Future Work

### Enhancements
- Multilingual support (FR/EN)
- Advanced graph visualization
- Batch document processing
- Fine-tuned models for compliance
- Real-time collaboration features
- Compliance tracking over time

### Production Readiness
- Authentication and authorization
- Rate limiting and quotas
- Database for document storage
- Caching layer for performance
- Monitoring and logging

---

## Conclusion

### Achievements
- ✅ Complete multi-agent system
- ✅ GraphRAG implementation
- ✅ Production-ready architecture
- ✅ Docker containerization
- ✅ Comprehensive documentation

### Impact
- Automated compliance checking
- Reduced manual effort
- Consistent analysis
- Article-level citation accuracy

### Technologies Used
- LangChain, OpenAI, ChromaDB
- NetworkX, FastAPI, Streamlit
- Docker, Multi-Agent Systems
- GraphRAG, Hybrid RAG

---

## Questions?

Thank you!

**Project Repository:** [GitHub URL]  
**Documentation:** See README.md  
**API Docs:** http://localhost:8000/docs
