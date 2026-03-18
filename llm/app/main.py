import time

from fastapi import FastAPI, HTTPException

from app.model_client import (
    DMR_BASE_URL,
    DMR_MODEL,
    ModelClientError,
    generate_chat_completion,
    get_models,
)
from app.prompt_builder import (
    build_generate_system_prompt,
    build_generate_user_prompt,
    build_recommendation_system_prompt,
    build_recommendation_user_prompt,
)
from app.schemas import (
    SimpleGenerateRequest,
    GenerateResponse,
    RecommendationRequest,
    SourceItem,
)

app = FastAPI(title="Legal LLM Service", version="0.3.0")


def _collect_sources(chunks) -> list[SourceItem]:
    unique = {}
    for chunk in chunks:
        key = (chunk.source, chunk.page, chunk.chunk_id)
        if key not in unique:
            unique[key] = SourceItem(
                source=chunk.source,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
            )
    return list(unique.values())

def detect_user_intent(query: str) -> dict:
    q = query.lower()

    advisory_markers = [
        "что делать",
        "что делать дальше",
        "как поступить",
        "какие действия",
        "рекомендации",
        "посоветуй",
        "риски",
        "оценка",
        "как лучше",
        "стоит ли"
    ]

    is_advisory = any(marker in q for marker in advisory_markers)

    return {
        "answer_only_from_context": not is_advisory,
        "allow_recommendations": is_advisory,
        "cite_sources": True,
        "structured_output": True,
    }

@app.get("/status")
def status() -> dict:
    try:
        models_data = get_models()
        available_models = [item.get("id") for item in models_data.get("data", [])]
        return {
            "status": "ok",
            "dmr_base_url": DMR_BASE_URL,
            "model_configured": DMR_MODEL,
            "available_models": available_models,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "dmr_base_url": DMR_BASE_URL,
            "model_configured": DMR_MODEL,
            "error": str(e),
        }


@app.post("/generate", response_model=GenerateResponse)
def generate(req: SimpleGenerateRequest) -> GenerateResponse:
    if not req.chunks:
        raise HTTPException(status_code=400, detail="chunks are empty")

    instructions = detect_user_intent(req.query)

    generation = {
        "temperature": 0.1,
        "max_tokens": 700,
        "enable_thinking": False,
    }

    system_prompt = build_generate_system_prompt(instructions)
    user_prompt = build_generate_user_prompt(req.query, req.chunks)

    started_at = time.perf_counter()

    try:
        result = generate_chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=generation["temperature"],
            max_tokens=generation["max_tokens"],
            enable_thinking=generation["enable_thinking"],
        )
    except ModelClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    elapsed = time.perf_counter() - started_at
    sources = _collect_sources(req.chunks)
    raw = result["raw"]
    usage = raw.get("usage", {})

    return GenerateResponse(
        answer=result["content"],
        sources=sources,
        meta={
            "mode": "generate",
            "case_id": req.case_id,
            "model": DMR_MODEL,
            "generation_time_sec": round(elapsed, 3),
            "usage": usage,
            "chunks_count": len(req.chunks),
        },
    )


@app.post("/recommendations", response_model=GenerateResponse)
def recommendations(req: RecommendationRequest) -> GenerateResponse:
    if not req.context.chunks:
        raise HTTPException(status_code=400, detail="recommendation context chunks are empty")

    system_prompt = build_recommendation_system_prompt(req.instructions)
    user_prompt = build_recommendation_user_prompt(req.context)

    started_at = time.perf_counter()

    try:
        result = generate_chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=req.generation.temperature,
            max_tokens=req.generation.max_tokens,
            enable_thinking=req.generation.enable_thinking,
        )
    except ModelClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    elapsed = time.perf_counter() - started_at
    sources = _collect_sources(req.context.chunks)
    raw = result["raw"]
    usage = raw.get("usage", {})

    return GenerateResponse(
        answer=result["content"],
        sources=sources,
        meta={
            "mode": "recommendations",
            "case_id": req.case_id,
            "model": DMR_MODEL,
            "generation_time_sec": round(elapsed, 3),
            "usage": usage,
            "chunks_count": len(req.context.chunks),
            "facts_count": len(req.context.facts),
            "risks_count": len(req.context.risks),
            "missing_info_count": len(req.context.missing_info),
        },
    )