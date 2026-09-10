   
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.groq_client import GroqClient

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "v1" / "extract_questions.txt"


@dataclass
class QuestionDraft:
    question: str
    context: str
    raised_by_speaker: str | None
    category: str


class S7QuestionExtractor:

    def __init__(self, client: BaseAIClient | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    async def run(self, chunks: list[str]) -> list[QuestionDraft]:
        t0 = time.perf_counter()
        all_questions: list[QuestionDraft] = []

        for i, chunk in enumerate(chunks):
            questions = await self._extract_from_chunk(chunk, i)
            all_questions.extend(questions)

        deduped = self._deduplicate(all_questions)

        logger.info(
            "s7_complete",
            raw=len(all_questions),
            deduped=len(deduped),
            elapsed=round(time.perf_counter() - t0, 2),
        )
        return deduped

    async def _extract_from_chunk(self, chunk: str, idx: int) -> list[QuestionDraft]:
        try:
            response = await self._client.complete(
                system_prompt=self._prompt_template,
                user_prompt=f"MEETING TRANSCRIPT:\n\n{chunk}",
                max_tokens=1500,
                temperature=0.1,
                json_mode=True,
            )
            data = GroqClient.parse_json(response.content)
            return [
                QuestionDraft(
                    question=q.get("question", "")[:500],
                    context=q.get("context", "")[:300],
                    raised_by_speaker=q.get("raised_by_speaker") or None,
                    category=q.get("category", "other"),
                )
                for q in data.get("open_questions", [])
                if q.get("question")
            ]
        except Exception as exc:
            logger.warning("s7_chunk_failed", chunk_index=idx, error=str(exc))
            return []

    def _deduplicate(self, questions: list[QuestionDraft]) -> list[QuestionDraft]:
        seen: list[QuestionDraft] = []
        for q in questions:
            if not any(self._similar(q.question, s.question) for s in seen):
                seen.append(q)
        return seen

    @staticmethod
    def _similar(a: str, b: str) -> bool:
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return False
        return len(wa & wb) / len(wa | wb) > 0.7
