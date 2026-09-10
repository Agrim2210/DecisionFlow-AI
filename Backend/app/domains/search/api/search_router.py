   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.search.api.schemas import (
    SearchRequest,
    MeetingSemanticSearchRequest,
    SearchResultResponse,
    SuggestRequest,
    SuggestResponse,
    map_search_result,
    map_suggestions,
)
from app.domains.search.application.search_service import SearchService
from app.domains.search.application.queries import SearchQuery, SuggestQuery
from app.domains.search.infra.memory_repo import SearchMemoryRepository
from app.shared.config import settings
from app.shared.deps import CurrentUser, DBSession

router = APIRouter(prefix="/search", tags=["Semantic Search"])


                                                                     

def _svc(db) -> SearchService:
       
    embed_client = None
    try:
        if settings.AI_EMBEDDING_MODEL.startswith("gemini"):
            from app.domains.extraction.domain.pipeline.clients.gemini_embed_client import GeminiEmbedClient
            if settings.GEMINI_API_KEY or getattr(settings, "GOOGLE_API_KEY", ""):
                embed_client = GeminiEmbedClient()
        elif settings.AI_EMBEDDING_MODEL.startswith("text-embedding"):
            from app.domains.extraction.domain.pipeline.clients.openai_embed_client import OpenAIEmbedClient
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
                embed_client = OpenAIEmbedClient()
    except Exception:
        pass                                                                

    return SearchService(
        memory_repo=SearchMemoryRepository(db),
        embed_client=embed_client,
    )


                                                                    

@router.post(
    "",
    response_model=SearchResultResponse,
    summary="Hybrid semantic + keyword search across org meeting memory",
    description=(
        "Search across meeting content, decisions, tasks, risks, and open questions.\n\n"
        "**Modes:**\n"
        "- `hybrid` (default) — combines semantic and keyword search using Reciprocal Rank Fusion. "
        "Best for most queries.\n"
        "- `semantic` — vector similarity search using the configured embedding provider. "
        "Best for conceptual queries ('authentication approach', 'API design').\n"
        "- `keyword` — PostgreSQL full-text search. "
        "Best for exact terms ('Rahul', 'Q3 deadline', specific names).\n\n"
        "**Filters:**\n"
        "- `source_type` narrows to `meeting`, `decision`, `action_item`, `risk`, or `question`\n"
        "- `meeting_id` narrows to a single meeting\n"
        "- `min_score` filters out low-relevance results\n\n"
        "**Tenant isolation:**\n"
        "Results are always scoped to your organization. "
        "The org_id is read from your JWT — never from the request body."
    ),
)
async def search(
    body: SearchRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> SearchResultResponse:
    svc = _svc(db)
    result = await svc.search(
        SearchQuery(
            org_id=current_user.org_id,                                       
            text=body.query,
            mode=body.mode,
            limit=body.limit,
            source_type=body.source_type,
            meeting_id=body.meeting_id,
            date_from=body.date_from,
            date_to=body.date_to,
            min_score=body.min_score,
        )
    )
    return map_search_result(result)


@router.post(
    "/meetings/{meeting_id}",
    response_model=SearchResultResponse,
    summary="Semantic search within one meeting",
    description=(
        "Search only the selected meeting's transcript chunks, decisions, tasks, "
        "risks, and open questions. The meeting is additionally scoped to the "
        "authenticated user's organization."
    ),
)
async def search_meeting(
    meeting_id: uuid.UUID,
    body: MeetingSemanticSearchRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> SearchResultResponse:
    result = await _svc(db).search(
        SearchQuery(
            org_id=current_user.org_id,
            meeting_id=meeting_id,
            text=body.query,
            mode="semantic",
            limit=body.limit,
            source_type=body.source_type,
            min_score=body.min_score,
        )
    )
    return map_search_result(result)


                                                                    

@router.post(
    "/suggest",
    response_model=SuggestResponse,
    summary="Autocomplete suggestions for search input",
    description=(
        "Returns up to 10 title suggestions matching the given prefix. "
        "Used to power the search bar autocomplete dropdown. "
        "Searches across decision and action_item titles using ILIKE prefix match.\n\n"
        "Minimum 2 characters required to trigger suggestions."
    ),
)
async def suggest(
    body: SuggestRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> SuggestResponse:
    svc = _svc(db)
    suggestions = await svc.suggest(
        SuggestQuery(
            org_id=current_user.org_id,
            prefix=body.prefix,
            source_type=body.source_type,
            limit=body.limit,
        )
    )
    return map_suggestions(suggestions, body.prefix)
