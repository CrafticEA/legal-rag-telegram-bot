import time

from fastapi import FastAPI, HTTPException

from app.model_client import (
    DMR_BASE_URL,
    DMR_MODEL,
    ModelClientError,
    generate_chat_completion,
    get_models,
)
from app.prompt_builder import build_system_prompt, build_user_prompt
from app.schemas import GenerateRequest, GenerateResponse, SourceItem

app = FastAPI(title="Legal LLM Service", version="0.1.0")


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
def generate(req: GenerateRequest) -> GenerateResponse:
    if not req.context.chunks:
        raise HTTPException(status_code=400, detail="context chunks are empty")

    system_prompt = build_system_prompt(req.instructions)
    user_prompt = build_user_prompt(req.query, req.context.chunks)

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

    sources = [
        SourceItem(source=chunk.source, page=chunk.page, chunk_id=chunk.chunk_id)
        for chunk in req.context.chunks
    ]

    raw = result["raw"]
    usage = raw.get("usage", {})

    return GenerateResponse(
        answer=result["content"],
        sources=sources,
        meta={
            "case_id": req.case_id,
            "model": DMR_MODEL,
            "generation_time_sec": round(elapsed, 3),
            "usage": usage,
            "chunks_count": len(req.context.chunks),
        },
    )