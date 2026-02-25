# RAG Service

Semantic retrieval service.

## Responsibilities

- Parse uploaded documents (PDF, DOCX, TXT)
- Chunk text into semantic units
- Generate embeddings (E5 model)
- Build and update FAISS index per case
- Retrieve top-K relevant chunks for queries

## Data Storage

Indexes and chunks are stored in:

data/cases/<chat_id>/<case_id>/

## Exposed Port

8001