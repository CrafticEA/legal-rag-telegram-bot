from app.schemas import Chunk, Instructions, RecommendationContext


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


def _join_chunks(chunks: list[Chunk]) -> str:
    if not chunks:
        return "[Контекст отсутствует]"
    return "\n\n".join(
        _format_chunk(chunk, i) for i, chunk in enumerate(chunks, start=1)
    )


def build_generate_system_prompt(instructions: Instructions) -> str:
    rules = [
        "Ты помощник по анализу юридических документов.",
        "Отвечай на русском языке.",
    ]

    if instructions.answer_only_from_context:
        rules.append(
            "Используй только предоставленный контекст. Если данных недостаточно, прямо скажи об этом."
        )

    if instructions.cite_sources:
        rules.append(
            "Не вставляй источники в текст ответа. Источники будут добавлены системой отдельно."
        )

    if instructions.structured_output:
        rules.append(
            "Структурируй ответ: сначала краткий вывод, затем детали."
        )

    rules.append("Не придумывай факты, которых нет в контексте.")

    return "\n".join(f"- {rule}" for rule in rules)


def build_generate_user_prompt(query: str, chunks: list[Chunk]) -> str:
    context_block = _join_chunks(chunks)

    return f"""Вопрос пользователя:
{query.strip()}

Контекст:
{context_block}

Сформируй ответ строго по этому контексту.
"""


def build_recommendation_system_prompt(instructions: Instructions) -> str:
    rules = [
        "Ты помощник по анализу юридических документов.",
        "Отвечай на русском языке.",
        "Тебе нужно сформировать рекомендации по материалам дела.",
    ]

    if instructions.answer_only_from_context:
        rules.append(
            "Используй только предоставленный контекст. Если данных недостаточно, прямо укажи, чего не хватает."
        )

    if instructions.cite_sources:
        rules.append(
            "Не вставляй источники в текст ответа. Источники будут добавлены системой отдельно."
        )

    if instructions.structured_output:
        rules.append(
            "Структурируй ответ в 4 блоках: краткий вывод, ключевые обстоятельства, риски и слабые места, практические рекомендации."
        )

    rules.append("Не придумывай факты, которых нет в контексте.")
    rules.append("Если информации недостаточно, укажи это отдельно.")

    return "\n".join(f"- {rule}" for rule in rules)


def build_recommendation_user_prompt(context: RecommendationContext) -> str:
    chunks_block = _join_chunks(context.chunks)

    facts_block = (
        "\n".join(f"- {item}" for item in context.facts)
        if context.facts
        else "- Нет данных"
    )
    risks_block = (
        "\n".join(f"- {item}" for item in context.risks)
        if context.risks
        else "- Нет данных"
    )
    missing_block = (
        "\n".join(f"- {item}" for item in context.missing_info)
        if context.missing_info
        else "- Нет данных"
    )

    claimant = context.claimant_position or "Нет данных"
    respondent = context.respondent_position or "Нет данных"
    case_summary = context.case_summary or "Нет данных"
    goal = context.goal or "Нет данных"
    procedural_stage = context.procedural_stage or "Нет данных"
    requested_output = context.requested_output or "Сформируй общие рекомендации по делу."

    extra_lines = []
    for key, value in context.extra.items():
        extra_lines.append(f"{key}: {value}")
    extra_block = "\n".join(extra_lines) if extra_lines else "Нет данных"

    return f"""Материалы дела для анализа рекомендаций.

Краткая сводка дела:
{case_summary}

Цель анализа:
{goal}

Стадия процесса:
{procedural_stage}

Что нужно получить:
{requested_output}

Ключевые факты:
{facts_block}

Позиция заявителя / истца:
{claimant}

Позиция ответчика:
{respondent}

Известные риски:
{risks_block}

Чего не хватает:
{missing_block}

Дополнительные структурированные данные:
{extra_block}

Фрагменты документов:
{chunks_block}

Сформируй рекомендации строго по этим материалам.
"""