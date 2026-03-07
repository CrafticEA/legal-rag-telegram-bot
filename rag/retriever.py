import os
import json
import faiss
import numpy as np

from embedder import embed_texts
from reranker import rerank


def load_chunks(path):

    chunks = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    return chunks


def retrieve(case_path, query, top_k=6, retrieve_k=30):

    index = faiss.read_index(
        os.path.join(case_path, "faiss.index")
    )

    chunks = load_chunks(
        os.path.join(case_path, "chunks.jsonl")
    )

    query_vec = embed_texts([query])

    scores, ids = index.search(
        np.array(query_vec, dtype=np.float32),
        retrieve_k
    )

    candidates = []

    for score, idx in zip(scores[0], ids[0]):

        chunk = chunks[idx]

        candidates.append({
            "text": chunk["text"],
            "score": float(score),
            "doc_name": chunk["doc_name"],
            "page": chunk["page"]
        })

    return rerank(query, candidates, top_k)