   
from __future__ import annotations

from typing import Any

import structlog

from app.shared.config import settings

logger = structlog.get_logger(__name__)

_SEVERITY_COLORS = {
    "critical": "#D32F2F", "high": "#F57C00",
    "medium": "#FBC02D", "low": "#388E3C", "info": "#1976D2",
}

_EVENT_EMOJI = {
    "task_assigned": "📋", "task_overdue": "⚠️",
    "escalation_triggered": "🚨", "escalation_level_2": "🔴",
    "escalation_level_3": "🆘", "escalation_resolved": "✅",
    "meeting_processed": "🎉", "risk_detected": "⚠️",
    "risk_critical": "🔴", "pipeline_failed": "❌",
}


class SlackAdapter:
                                                                              

    def __init__(self) -> None:
        self._webhook_url = settings.SLACK_WEBHOOK_URL or ""

    async def send(self, subject: str, body: str, payload: dict[str, Any]) -> bool:
        if not self._webhook_url:
            logger.debug("slack_not_configured", subject=subject[:50])
            return False

        event_type = payload.get("event_type", "info")
        severity = payload.get("severity", "info")
        emoji = _EVENT_EMOJI.get(event_type, "🔔")
        color = _SEVERITY_COLORS.get(severity, _SEVERITY_COLORS["info"])

        blocks = self._build_blocks(emoji=emoji, subject=subject, body=body, payload=payload)
        return await self._post({"blocks": blocks, "attachments": [{"color": color}]})

    async def send_task_overdue(
        self, task_title: str, task_id: str, owner_name: str,
        due_date: str, meeting_title: str, escalation_level: int = 1,
    ) -> bool:
        level_emoji = {1: "⚠️", 2: "🚨", 3: "🆘"}.get(escalation_level, "⚠️")
        return await self.send(
            subject=f"{level_emoji} Overdue Task: {task_title}",
            body=f"Task assigned to {owner_name} from meeting '{meeting_title}' is overdue.",
            payload={
                "event_type": "task_overdue", "task_title": task_title, "task_id": task_id,
                "owner_name": owner_name, "due_date": due_date, "meeting_title": meeting_title,
                "escalation_level": escalation_level,
                "severity": "high" if escalation_level == 1 else "critical",
            },
        )

    def _build_blocks(self, emoji: str, subject: str, body: str, payload: dict[str, Any]) -> list[dict]:
        blocks: list[dict] = [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {subject}", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": body}},
        ]

        context_elements = []
        field_map = {
            "task_title": "Task", "due_date": "Due", "meeting_title": "Meeting",
            "escalation_level": "Escalation Level", "owner_name": "Owner",
            "decision_count": "Decisions", "task_count": "Tasks", "risk_count": "Risks",
        }
        for key, label in field_map.items():
            if key in payload and payload[key]:
                context_elements.append({"type": "mrkdwn", "text": f"*{label}:* {payload[key]}"})

        if context_elements:
            blocks.append({"type": "context", "elements": context_elements[:10]})

        action_url = payload.get("action_url", "")
        if action_url:
            blocks.append({
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in DecisionFlow"},
                    "url": action_url, "style": "primary",
                }],
            })

        return blocks

    async def _post(self, payload: dict[str, Any]) -> bool:
        try:
            import asyncio
            import json
            import urllib.request

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._webhook_url, data=data, headers={"Content-Type": "application/json"},
            )
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=10),
            )
            logger.debug("slack_sent")
            return True
        except Exception as exc:
            logger.error("slack_send_failed", error=str(exc))
            return False
