# The Investment Guru 📈🤖

> An AI Financial Analyst expert system that ingests market data, retrieves relevant financial context, and generates professional investment insights.

## Project Overview

"The Investment Guru" aims to be more than just an LLM chatbot wrapper. It is a highly technical and valuable product built as an **expert system**. It is designed to emulate the analytical rigor of a professional financial analyst by combining live market data ingestion, structured and unstructured data processing, and advanced Retrieval-Augmented Generation (RAG).

## Current Progress

We have just completed the **Project Initialization & Architecture Setup** phase.

### What's been done:
- **Dependency Management:** Initialized a `pyproject.toml` using **Poetry**.
- **Core Dependencies Added:**
  - `zenml`: For robust MLOps pipeline orchestration.
  - `pymongo`: For interactions with a MongoDB NoSQL Data Warehouse (storing raw financial data, news, filings).
  - `qdrant-client`: For our Vector Database to support RAG capabilities.
  - `huggingface-hub`: For integrating open-source LLMs and embedding models.
  - `python-dotenv`: For managing environment variables securely.
- **Directory Structure Established:**
  - `llm_engineering/`: Following Domain-Driven Design (DDD) with `application/`, `domain/`, `infrastructure/`, and `model/`.
  - `pipelines/`: For ZenML MLOps pipelines (e.g., feature engineering, model training, deployment).
  - `steps/`: Individual ZenML steps.
  - `tools/`: Scaffolding for core tools:
    - `data_warehouse.py`
    - `ml_service.py`
    - `rag.py`
    - `run.py`
  - `configs/`, `tests/`, and `code_snippets/` directories mapped out.

## Tech Stack Overview

- **Language:** Python (`>=3.11, <3.14`)
- **Package Manager:** Poetry
- **MLOps Framework:** ZenML
- **Data Warehouse:** MongoDB
- **Vector Database:** Qdrant
- **AI/LLM Ecosystem:** Hugging Face Models

## Next Steps

1. **Implement Infrastructure Layer:** Connect to MongoDB and Qdrant using the scaffolding in `llm_engineering/infrastructure/`.
2. **Data Ingestion Pipelines:** Create ZenML pipelines to fetch financial data (e.g., stock tickers, financial statements, news) and store them in the Data Warehouse.
3. **Embedding & RAG System:** Develop the pipeline to process text, generate embeddings via Hugging Face, and store them in Qdrant (`tools/rag.py`).
4. **Analyst Agent Implementation:** Build the core logic that orchestrates retrieving context from Qdrant and prompting the LLM to generate professional financial reports.
