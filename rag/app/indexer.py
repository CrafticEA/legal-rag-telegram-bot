import json
import os

import faiss
import numpy as np

from app.chunker import chunk_text
from app.embedder import embed_texts
from app.parser import parse_document
from app.storage import get_case_path, invalidate_case_cache


def build_index(chat_id, case_id, docs):
    case_path = get_case_path(chat_id, case_id)
    os.makedirs(case_path, exist_ok=True)

    chunks = []
    texts = []

    chunk_id = 0

    for path in docs:
        filename = os.path.basename(path)
        pages = parse_document(path)

        for page in pages:
            pieces = chunk_text(page["text"])

            for piece in pieces:
                chunks.append({
                    "chunk_id": f"c{chunk_id}",
                    "text": piece,
                    "doc_name": filename,
                    "page": page["page"]
                })
                texts.append(piece)
                chunk_id += 1

    if not texts:
        raise ValueError("No text extracted from documents")

    embeddings = embed_texts(texts)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype=np.float32))

    index_path = os.path.join(case_path, "faiss.index")
    chunks_path = os.path.join(case_path, "chunks.jsonl")

    faiss.write_index(index, index_path)

    with open(chunks_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    invalidate_case_cache(chat_id, case_id)

    return {
        "chunks": len(chunks),
        "dim": dim
    }