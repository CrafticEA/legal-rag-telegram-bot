from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    text: str
    source: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    score: Optional[float] = None


class SimpleGenerateRequest(BaseModel):
    case_id: Optional[str] = None
    query: str
    chunks: List[Chunk] = Field(default_factory=list)


class Instructions(BaseModel):
    answer_only_from_context: bool = True
    cite_sources: bool = True
    structured_output: bool = True


class GenerationParams(BaseModel):
    temperature: float = 0.1
    max_tokens: int = 700
    enable_thinking: bool = False


class RecommendationContext(BaseModel):
    case_summary: Optional[str] = None
    goal: Optional[str] = None
    facts: List[str] = Field(default_factory=list)
    claimant_position: Optional[str] = None
    respondent_position: Optional[str] = None
    risks: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    procedural_stage: Optional[str] = None
    requested_output: Optional[str] = None
    chunks: List[Chunk] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    case_id: str
    context: RecommendationContext
    instructions: Instructions = Field(default_factory=Instructions)
    generation: GenerationParams = Field(default_factory=GenerationParams)


class SourceItem(BaseModel):
    source: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None


class GenerateResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    meta: dict[str, Any] = Field(default_factory=dict)