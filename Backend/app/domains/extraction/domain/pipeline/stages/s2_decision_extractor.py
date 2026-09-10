   
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.groq_client import GroqClient

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "v1" / "extract_decisions.txt"


@dataclass
class DecisionDraft:
    title: str
    description: str
    decision_type: str
    confidence_score: float
    made_by_speakers: list[str] = field(default_factory=list)
    rationale: str = ""
    raw_output: dict = field(default_factory=dict)


class S2DecisionExtractor:

    def __init__(self, client: BaseAIClient | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    async def run(self, chunks: list[str]) -> list[DecisionDraft]:
           
        t0 = time.perf_counter()
        all_drafts: list[DecisionDraft] = []

        for i, chunk in enumerate(chunks):
            drafts = await self._extract_from_chunk(chunk, chunk_index=i)
            all_drafts.extend(drafts)

                                                                                 
        deduped = self._deduplicate(all_drafts)

        logger.info(
            "s2_complete",
            chunks=len(chunks),
            raw_count=len(all_drafts),
            deduped_count=len(deduped),
            elapsed=round(time.perf_counter() - t0, 2),
        )
        return deduped

    async def _extract_from_chunk(self, chunk: str, chunk_index: int) -> list[DecisionDraft]:
        prompt = f"MEETING TRANSCRIPT:\n\n{chunk}"

        try:
            response = await self._client.complete(
                system_prompt=self._prompt_template,
                user_prompt=prompt,
                max_tokens=2048,
                temperature=0.1,
                json_mode=True,
            )
            data = GroqClient.parse_json(response.content)
            return [
                DecisionDraft(
                    title=d.get("title", "Untitled Decision")[:100],
                    description=d.get("description", ""),
                    decision_type=d.get("decision_type", "operational"),
                    confidence_score=float(d.get("confidence_score", 0.8)),
                    made_by_speakers=d.get("made_by_speakers", []),
                    rationale=d.get("rationale", ""),
                    raw_output=d,
                )
                for d in data.get("decisions", [])
                if float(d.get("confidence_score", 0)) >= 0.6
            ]
        except Exception as exc:
            logger.warning("s2_chunk_failed", chunk_index=chunk_index, error=str(exc))
            return []

    def _deduplicate(self, drafts: list[DecisionDraft]) -> list[DecisionDraft]:
                                                                                 
        seen: list[DecisionDraft] = []
        for draft in drafts:
            if not any(self._similar(draft.title, s.title) for s in seen):
                seen.append(draft)
        return seen

    @staticmethod
    def _similar(a: str, b: str) -> bool:
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return False
        return len(wa & wb) / len(wa | wb) > 0.8
