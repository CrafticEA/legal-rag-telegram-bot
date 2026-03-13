import numpy as np
import torch
from sentence_transformers import SentenceTransformer

_MODEL = None


def get_embedder():
    global _MODEL

    if _MODEL is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        _MODEL = SentenceTransformer(
            "intfloat/multilingual-e5-base",
            device=device
        )

    return _MODEL


def embed_texts(texts, batch_size=8):
    model = get_embedder()

    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        emb = model.encode(
            batch,
            normalize_embeddings=True
        )

        embeddings.append(emb)

    return np.vstack(embeddings)