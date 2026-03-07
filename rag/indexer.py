import os
import json
import faiss
import numpy as np

from chunker import chunk_text
from embedder import embed_texts
from parser import parse_document

from storage import get_case_path


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

    if len(texts) == 0:
        raise ValueError("No text extracted from documents")

    embeddings = embed_texts(texts)

    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype=np.float32))

    faiss.write_index(
        index,
        os.path.join(case_path, "faiss.index")
    )

    with open(os.path.join(case_path, "chunks.jsonl"), "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    return {
        "chunks": len(chunks),
        "dim": dim
    }