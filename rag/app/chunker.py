import re


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_into_paragraphs(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return paragraphs


def split_into_sentences(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []

    # Простое деление по знакам конца предложения.
    # Для юридических текстов этого обычно достаточно как базового варианта.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def split_long_sentence(sentence: str, max_len: int) -> list[str]:
    sentence = sentence.strip()
    if len(sentence) <= max_len:
        return [sentence]

    parts = re.split(r'(?<=[,;:])\s+', sentence)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        return [sentence[i:i + max_len].strip() for i in range(0, len(sentence), max_len)]

    chunks = []
    current = []

    for part in parts:
        candidate = " ".join(current + [part])
        if len(candidate) <= max_len:
            current.append(part)
        else:
            if current:
                chunks.append(" ".join(current).strip())
            current = [part]

    if current:
        chunks.append(" ".join(current).strip())

    return chunks


def build_chunks_from_sentences(
    sentences: list[str],
    chunk_size: int = 500,
    overlap_sentences: int = 1,
) -> list[str]:
    if not sentences:
        return []

    prepared_sentences = []
    for sentence in sentences:
        prepared_sentences.extend(split_long_sentence(sentence, chunk_size))

    chunks = []
    current_chunk = []

    for sentence in prepared_sentences:
        candidate = " ".join(current_chunk + [sentence]).strip()

        if len(candidate) <= chunk_size:
            current_chunk.append(sentence)
            continue

        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())

            if overlap_sentences > 0:
                current_chunk = current_chunk[-overlap_sentences:]
            else:
                current_chunk = []

            candidate = " ".join(current_chunk + [sentence]).strip()

            if len(candidate) <= chunk_size:
                current_chunk.append(sentence)
            else:
                chunks.append(sentence.strip())
                current_chunk = []
        else:
            chunks.append(sentence.strip())

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    return [chunk for chunk in chunks if chunk]


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap_sentences: int = 1,
    paragraph_merge_threshold: int = 200,
) -> list[str]:
    paragraphs = split_into_paragraphs(text)

    if not paragraphs:
        return []

    chunks = []
    buffer_paragraph = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Если абзац короткий, пробуем склеить его со следующим,
        # чтобы не плодить слишком мелкие чанки.
        if len(paragraph) < paragraph_merge_threshold:
            if buffer_paragraph:
                buffer_paragraph = f"{buffer_paragraph} {paragraph}".strip()
            else:
                buffer_paragraph = paragraph
            continue

        if buffer_paragraph:
            paragraph = f"{buffer_paragraph} {paragraph}".strip()
            buffer_paragraph = ""

        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
            continue

        sentences = split_into_sentences(paragraph)
        paragraph_chunks = build_chunks_from_sentences(
            sentences=sentences,
            chunk_size=chunk_size,
            overlap_sentences=overlap_sentences,
        )
        chunks.extend(paragraph_chunks)

    if buffer_paragraph:
        if len(buffer_paragraph) <= chunk_size:
            chunks.append(buffer_paragraph)
        else:
            sentences = split_into_sentences(buffer_paragraph)
            chunks.extend(
                build_chunks_from_sentences(
                    sentences=sentences,
                    chunk_size=chunk_size,
                    overlap_sentences=overlap_sentences,
                )
            )

    return [chunk.strip() for chunk in chunks if chunk.strip()]