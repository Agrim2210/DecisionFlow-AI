   
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import structlog

from app.domains.extraction.domain.entities import MemoryChunk
from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.gemini_embed_client import GeminiEmbedClient
from app.shared.config import settings
from app.domains.extraction.domain.pipeline.stages.s2_decision_extractor import DecisionDraft
from app.domains.extraction.domain.pipeline.stages.s3_action_extractor import ActionItemDraft

logger = structlog.get_logger(__name__)


@dataclass
class EmbedResult:
    decision_embeddings: dict[str, list[float]]                               
    task_embeddings: dict[str, list[float]]                                
    memory_chunks: list[MemoryChunk]
    total_tokens: int


class S6Embedder:

    def __init__(self, client: BaseAIClient | None = None) -> None:
        self._client = client or GeminiEmbedClient()

    async def run(
        self,
        org_id: uuid.UUID,
        meeting_id: uuid.UUID,
        decisions: list[DecisionDraft],
        action_items: list[ActionItemDraft],
        decision_ids: dict[str, uuid.UUID],                                        
        task_ids: dict[str, uuid.UUID],                      
        transcript_text: str = "",
    ) -> EmbedResult:
        t0 = time.perf_counter()

                              
        texts: list[str] = []
        labels: list[tuple[str, str, str, uuid.UUID]] = []                                  

        for d in decisions:
            text = f"Decision: {d.title}. {d.description}"
            texts.append(text)
            labels.append(("decision", d.title, text, decision_ids[d.title]))

        for a in action_items:
            owner_part = f" Owner: {a.owner_name}." if a.owner_name else ""
            deadline_part = f" Due: {a.deadline_text}." if a.deadline_text else ""
            text = f"Task: {a.title}.{owner_part}{deadline_part} {a.description}"
            texts.append(text)
            labels.append(("action_item", a.title, text, task_ids[a.title]))

                                                                          
                                                                             
                                               
        for index, chunk in enumerate(self._transcript_chunks(transcript_text)):
            text = f"Meeting transcript: {chunk}"
            texts.append(text)
            labels.append(("meeting", f"Meeting content {index + 1}", text, meeting_id))

        if not texts:
            return EmbedResult(
                decision_embeddings={},
                task_embeddings={},
                memory_chunks=[],
                total_tokens=0,
            )

                           
        embed_response = await self._client.embed(texts)
        if embed_response.dimensions != settings.AI_EMBEDDING_DIMS:
            raise RuntimeError(
                f"Embedding dimensionality mismatch: expected {settings.AI_EMBEDDING_DIMS}, "
                f"got {embed_response.dimensions}. Check AI_EMBEDDING_MODEL and provider settings."
            )
        embeddings = embed_response.embeddings
        if any(len(embedding) != embed_response.dimensions for embedding in embeddings):
            raise RuntimeError(
                "Embedding vectors returned by the provider are not all the expected length. "
                "Check provider configuration and model choice."
            )

                  
        decision_embeddings: dict[str, list[float]] = {}
        task_embeddings: dict[str, list[float]] = {}
        memory_chunks: list[MemoryChunk] = []

        for i, (entity_type, title, text, source_id) in enumerate(labels):
            if i >= len(embeddings):
                break
            emb = embeddings[i]

            if entity_type == "decision":
                decision_embeddings[title] = emb
            elif entity_type == "action_item":
                task_embeddings[title] = emb

            memory_chunks.append(MemoryChunk(
                id=uuid.uuid4(),
                org_id=org_id,
                meeting_id=meeting_id,
                source_type=entity_type,
                source_id=source_id,
                content=text,
                embedding=emb,
                metadata={"title": title},
            ))

        logger.info(
            "s6_complete",
            total_embedded=len(texts),
            total_tokens=embed_response.input_tokens,
            elapsed=round(time.perf_counter() - t0, 2),
        )

        return EmbedResult(
            decision_embeddings=decision_embeddings,
            task_embeddings=task_embeddings,
            memory_chunks=memory_chunks,
            total_tokens=embed_response.input_tokens,
        )

    async def embed_additional_memory(
        self,
        *,
        org_id: uuid.UUID,
        meeting_id: uuid.UUID,
        documents: list[tuple[str, uuid.UUID, str, str, dict]],
    ) -> list[MemoryChunk]:
                                                                                 
        if not documents:
            return []
        texts = [document[3] for document in documents]
        response = await self._client.embed(texts)
        if response.dimensions != settings.AI_EMBEDDING_DIMS:
            raise RuntimeError("Embedding dimensionality does not match the configured vector column")
        return [
            MemoryChunk(
                id=uuid.uuid4(), org_id=org_id, meeting_id=meeting_id,
                source_type=source_type, source_id=source_id, content=content,
                embedding=embedding, metadata={"title": title, **metadata},
            )
            for (source_type, source_id, title, content, metadata), embedding
            in zip(documents, response.embeddings)
        ]

    @staticmethod
    def _transcript_chunks(transcript_text: str, chunk_size: int = 3_500, max_chunks: int = 12) -> list[str]:
                                                                             
        text = transcript_text.strip()
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)][:max_chunks]
