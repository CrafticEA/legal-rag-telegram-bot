import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "intfloat/multilingual-e5-base",
    device="cuda"
)


def embed_texts(texts, batch_size=8):

    embeddings = []

    for i in range(0, len(texts), batch_size):

        batch = texts[i:i+batch_size]

        emb = model.encode(
            batch,
            normalize_embeddings=True
        )

        embeddings.append(emb)

    return np.vstack(embeddings)