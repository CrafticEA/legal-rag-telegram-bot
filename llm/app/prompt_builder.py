from app.schemas import Chunk, Instructions


def _format_chunk(chunk: Chunk, index: int) -> str:
    meta_parts = [f"#{index}"]

    if chunk.source:
        meta_parts.append(f"source={chunk.source}")
    if chunk.page is not None:
        meta_parts.append(f"page={chunk.page}")
    if chunk.chunk_id:
        meta_parts.append(f"chunk_id={chunk.chunk_id}")
    if chunk.score is not None:
        meta_parts.append(f"score={chunk.score:.4f}")

    meta = ", ".join(meta_parts)
    return f"[{meta}]\n{chunk.text.strip()}"


def build_system_prompt(instructions: Instructions) -> str:
    rules = [
        "Ты помощник по анализу документов.",
        "Отвечай на русском языке.",
    ]

    if instructions.answer_only_from_context:
        rules.append(
            "Используй только предоставленный контекст. Если данных недостаточно, прямо скажи об этом."
        )

    if instructions.cite_sources:
        rules.append(
            "Когда это возможно, в конце каждого смыслового пункта или абзаца указывай источники в формате [source, page, chunk_id]."
        )

    if instructions.structured_output:
        rules.append(
            "Структурируй ответ: краткий вывод, затем детали."
        )

    rules.append("Не придумывай факты, которых нет в контексте.")
    return "\n".join(f"- {rule}" for rule in rules)


def build_user_prompt(query: str, chunks: list[Chunk]) -> str:
    if not chunks:
        context_block = "[Контекст отсутствует]"
    else:
        context_block = "\n\n".join(
            _format_chunk(chunk, i) for i, chunk in enumerate(chunks, start=1)
        )

    return f"""Вопрос пользователя:
{query.strip()}

Контекст:
{context_block}

Сформируй ответ строго по этому контексту."""