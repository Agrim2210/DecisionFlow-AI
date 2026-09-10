   
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import structlog

from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.groq_client import GroqClient
from app.domains.extraction.domain.pipeline.stages.s2_decision_extractor import DecisionDraft

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "v1" / "extract_actions.txt"


@dataclass
class ActionItemDraft:
    title: str
    description: str
    owner_name: str | None                                                         
    owner_id: uuid.UUID | None                                                       
    deadline_text: str | None
    deadline_dt: datetime | None                                              
    deadline_is_explicit: bool
    priority: str
    related_decision_title: str | None
    confidence_score: float
    raw_output: dict = field(default_factory=dict)


class S3ActionExtractor:

    def __init__(self, client: BaseAIClient | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    async def run(
        self,
        chunks: list[str],
        decisions: list[DecisionDraft],
        speaker_map: dict[str, str],
        meeting_date: datetime | None = None,
    ) -> list[ActionItemDraft]:
        t0 = time.perf_counter()

        decisions_context = self._format_decisions(decisions)
        all_drafts: list[ActionItemDraft] = []

        for i, chunk in enumerate(chunks):
            drafts = await self._extract_from_chunk(
                chunk, decisions_context, chunk_index=i
            )
            all_drafts.extend(drafts)

        deduped = self._deduplicate(all_drafts)

                                                       
        for draft in deduped:
            if draft.owner_name:
                matched = speaker_map.get(draft.owner_name)
                if matched and self._is_uuid(matched):
                    try:
                        draft.owner_id = uuid.UUID(matched)
                    except ValueError:
                        draft.owner_id = None

                                            
            if draft.deadline_text and meeting_date:
                draft.deadline_dt = self._parse_deadline(draft.deadline_text, meeting_date)

        logger.info(
            "s3_complete",
            raw_count=len(all_drafts),
            deduped_count=len(deduped),
            elapsed=round(time.perf_counter() - t0, 2),
        )
        return deduped

    async def _extract_from_chunk(
        self,
        chunk: str,
        decisions_context: str,
        chunk_index: int,
    ) -> list[ActionItemDraft]:
        prompt_text = self._prompt_template.replace("{decisions_context}", decisions_context)
        user_prompt = f"MEETING TRANSCRIPT:\n\n{chunk}"

        try:
            response = await self._client.complete(
                system_prompt=prompt_text,
                user_prompt=user_prompt,
                max_tokens=3000,
                temperature=0.1,
                json_mode=True,
            )
            data = GroqClient.parse_json(response.content)
            drafts = []
            for item in data.get("action_items", []):
                score = float(item.get("confidence_score", 0.8))
                if score < 0.6:
                    continue
                drafts.append(ActionItemDraft(
                    title=item.get("title", "Untitled Task")[:100],
                    description=item.get("description", ""),
                    owner_name=item.get("owner_name") or None,
                    owner_id=None,
                    deadline_text=item.get("deadline_text") or None,
                    deadline_dt=None,
                    deadline_is_explicit=bool(item.get("deadline_is_explicit", False)),
                    priority=item.get("priority", "medium"),
                    related_decision_title=item.get("related_decision_title") or None,
                    confidence_score=score,
                    raw_output=item,
                ))
            return drafts
        except Exception as exc:
            logger.warning("s3_chunk_failed", chunk_index=chunk_index, error=str(exc))
            return []

    def _format_decisions(self, decisions: list[DecisionDraft]) -> str:
        if not decisions:
            return "No decisions extracted."
        lines = []
        for d in decisions:
            lines.append(f"- [{d.decision_type.upper()}] {d.title}: {d.description}")
        return "\n".join(lines)

    def _deduplicate(self, drafts: list[ActionItemDraft]) -> list[ActionItemDraft]:
        seen: list[ActionItemDraft] = []
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
        return len(wa & wb) / len(wa | wb) > 0.75

    @staticmethod
    def _is_uuid(s: str) -> bool:
        try:
            uuid.UUID(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def _parse_deadline(text: str, base_date: datetime) -> datetime | None:
           
        text_lower = text.lower().strip()
        now = base_date.replace(tzinfo=timezone.utc) if base_date.tzinfo is None else base_date

        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
        }

        if "today" in text_lower:
            return now
        if "tomorrow" in text_lower:
            return now + timedelta(days=1)
        if "end of week" in text_lower or "eow" in text_lower:
            days_ahead = 4 - now.weekday()           
            return now + timedelta(days=max(days_ahead, 0))
        if "next week" in text_lower:
            return now + timedelta(weeks=1)
        if "end of month" in text_lower or "eom" in text_lower:
            import calendar
            last_day = calendar.monthrange(now.year, now.month)[1]
            return now.replace(day=last_day)
        if "end of sprint" in text_lower:
            return now + timedelta(weeks=2)

        for day_name, day_num in weekday_map.items():
            if day_name in text_lower:
                days_ahead = (day_num - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return now + timedelta(days=days_ahead)

                           
        m = re.search(r"in\s+(\d+)\s+(day|week)", text_lower)
        if m:
            n = int(m.group(1))
            unit = m.group(2)
            delta = timedelta(days=n) if unit == "day" else timedelta(weeks=n)
            return now + delta

        return None
