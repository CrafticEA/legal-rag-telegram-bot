# API Service

FastAPI service responsible for:

- Case management
- Document upload handling
- Database operations
- Orchestration between RAG and LLM services

## Responsibilities

- Create and manage cases
- Store metadata in DB
- Trigger RAG indexing
- Call LLM for answer generation
- Return structured responses to n8n

## Exposed Port

8000

## Depends On

- RAG service
- LLM service