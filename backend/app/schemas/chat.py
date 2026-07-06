from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Employee question")
    top_k: int = Field(default=5, ge=1, le=20)
    candidate_k: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Number of dense candidates retrieved before reranking",
    )
    score_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional minimum dense similarity score",
    )
    use_reranking: bool = Field(default=True)
    use_query_rewriting: bool = Field(default=True)

    document_type: str | None = Field(default=None)
    policy_name: str | None = Field(default=None)
    department_owner: str | None = Field(default=None)
    access_level: str | None = Field(default=None)
    chunk_type: str | None = Field(default=None)


class SourceMetadata(BaseModel):
    document_id: int | None = None
    file_name: str | None = None
    document_type: str | None = None
    policy_name: str | None = None
    department_owner: str | None = None
    access_level: str | None = None
    page_number: int | None = None
    chunk_index: int | None = None
    section_title: str | None = None
    chunk_type: str | None = None
    extractor: str | None = None
    ocr_applied: bool | None = None


class RetrievalResult(BaseModel):
    score: float
    rerank_score: float | None = None
    rerank_score_raw: float | None = None
    text: str | None = None
    source: SourceMetadata


class RetrieveResponse(BaseModel):
    query: str
    rewritten_query: str
    top_k: int
    candidate_k: int
    score_threshold: float | None = None
    use_reranking: bool
    use_query_rewriting: bool
    filters: dict
    results_count: int
    results: list[RetrievalResult]


class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Employee question")
    top_k: int = Field(default=5, ge=1, le=10)
    candidate_k: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Number of dense candidates retrieved before reranking",
    )
    score_threshold: float | None = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Minimum dense retrieval similarity score",
    )
    max_sources: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of source citations returned",
    )
    use_reranking: bool = Field(default=True)
    use_query_rewriting: bool = Field(default=True)

    document_type: str | None = Field(default=None)
    policy_name: str | None = Field(default=None)
    department_owner: str | None = Field(default=None)
    access_level: str | None = Field(default=None)
    chunk_type: str | None = Field(default=None)


class AnswerSource(BaseModel):
    source_id: int
    score: float
    rerank_score: float | None = None
    document_id: int | None = None
    file_name: str | None = None
    policy_name: str | None = None
    document_type: str | None = None
    department_owner: str | None = None
    page_number: int | None = None
    chunk_index: int | None = None
    chunk_type: str | None = None
    text_preview: str | None = None


class AskResponse(BaseModel):
    query: str
    rewritten_query: str | None = None
    route: str
    answer: str
    confidence: str
    use_reranking: bool
    use_query_rewriting: bool
    filters: dict
    results_count: int
    sources: list[AnswerSource]