from typing import List, Optional

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    text: str
    source: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    score: Optional[float] = None


class Context(BaseModel):
    chunks: List[Chunk] = Field(default_factory=list)


class Instructions(BaseModel):
    answer_only_from_context: bool = True
    cite_sources: bool = True
    structured_output: bool = True


class GenerationParams(BaseModel):
    temperature: float = 0.1
    max_tokens: int = 700
    enable_thinking: bool = False


class GenerateRequest(BaseModel):
    case_id: str
    query: str
    context: Context
    instructions: Instructions = Field(default_factory=Instructions)
    generation: GenerationParams = Field(default_factory=GenerationParams)


class SourceItem(BaseModel):
    source: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None


class GenerateResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    meta: dict