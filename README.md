# NotebookLM Clone

A NotebookLM-like Document Research System for analyzing and querying documents with AI-powered citations.

## Features

- **Notebook Management**: Create and organize research notebooks
- **Source Ingestion**: Add URLs as sources with automatic content extraction
- **Vector Search**: Semantic search across all document chunks
- **RAG Queries**: Ask questions and get answers with precise citations
- **Citation Navigation**: Navigate to exact locations in source documents

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd ntlm-clone

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload
```

### CLI Usage

```bash
# Create a notebook
ntlm notebook create "My Research"

# Add a source
ntlm source add <notebook-id> https://example.com/article

# Query the notebook
ntlm query ask <notebook-id> "What are the main findings?"
```

## API Endpoints

- `POST /api/v1/notebooks` - Create notebook
- `GET /api/v1/notebooks` - List notebooks
- `GET /api/v1/notebooks/{id}` - Get notebook details
- `POST /api/v1/notebooks/{id}/sources` - Add source URL
- `GET /api/v1/notebooks/{id}/sources` - List sources
- `POST /api/v1/notebooks/{id}/query` - Query with RAG

## Architecture

This project follows Domain-Driven Design (DDD) principles:

- **Domain Layer**: Pure business logic with immutable entities
- **Application Layer**: Handlers for commands and queries
- **Infrastructure Layer**: Database, external APIs, repositories
- **Entrypoint Layer**: REST API and CLI

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Format and lint
ruff format src tests
ruff check src tests
```

## License

MIT
