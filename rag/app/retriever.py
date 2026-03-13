import numpy as np

from app.embedder import embed_texts
from app.reranker import rerank
from app.storage import get_case_resources


def retrieve(chat_id, case_id, query, top_k=6, retrieve_k=30):
    index, chunks = get_case_resources(chat_id, case_id)

    query_vec = embed_texts([query])

    scores, ids = index.search(
        np.array(query_vec, dtype=np.float32),
        retrieve_k
    )

    candidates = []

    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(chunks):
            continue

        chunk = chunks[idx]

        candidates.append({
            "text": chunk["text"],
            "source": chunk["doc_name"],
            "page": chunk["page"],
            "chunk_id": chunk["chunk_id"],
            "score": float(score)
        })

    ranked = rerank(query, candidates, top_k)

    for chunk in ranked:
        if "rerank_score" in chunk:
            chunk["score"] = float(chunk["rerank_score"])
            chunk.pop("rerank_score", None)

    return ranked