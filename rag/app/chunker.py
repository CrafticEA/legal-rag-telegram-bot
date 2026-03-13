import re


def split_into_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str, chunk_size: int = 400, overlap_sentences: int = 1) -> list[str]:
    sentences = split_into_sentences(text)

    if not sentences:
        return []

    chunks = []
    current_chunk = []

    for sentence in sentences:
        candidate = " ".join(current_chunk + [sentence])

        if len(candidate) <= chunk_size:
            current_chunk.append(sentence)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))

                if overlap_sentences > 0:
                    current_chunk = current_chunk[-overlap_sentences:]
                else:
                    current_chunk = []

                if len(" ".join(current_chunk + [sentence])) <= chunk_size:
                    current_chunk.append(sentence)
                else:
                    chunks.append(sentence)
                    current_chunk = []
            else:
                chunks.append(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks