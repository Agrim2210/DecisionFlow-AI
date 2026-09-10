   
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.groq_client import GroqClient
from app.domains.extraction.domain.pipeline.stages.s2_decision_extractor import DecisionDraft
from app.domains.extraction.domain.pipeline.stages.s3_action_extractor import ActionItemDraft
from app.domains.extraction.domain.pipeline.stages.s4_dependency_detector import DependencyDraft

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "v1" / "analyze_risks.txt"


@dataclass
class RiskDraft:
    risk_type: str
    severity: str
    related_item_title: str
    related_item_type: str                                  
    description: str
    recommendation: str = ""


class S5RiskAnalyzer:

    def __init__(self, client: BaseAIClient | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    async def run(
        self,
        decisions: list[DecisionDraft],
        action_items: list[ActionItemDraft],
        dependencies: list[DependencyDraft],
    ) -> list[RiskDraft]:
        t0 = time.perf_counter()

                                                              
        rule_risks = self._rule_based_risks(decisions, action_items, dependencies)

                                                      
        ai_risks = await self._ai_risks(decisions, action_items, dependencies)

                                                               
        all_risks = rule_risks + ai_risks
        seen: set[tuple[str, str]] = set()
        deduped: list[RiskDraft] = []
        for r in all_risks:
            key = (r.risk_type, r.related_item_title.lower()[:50])
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        logger.info(
            "s5_complete",
            rule_risks=len(rule_risks),
            ai_risks=len(ai_risks),
            total=len(deduped),
            elapsed=round(time.perf_counter() - t0, 2),
        )
        return deduped

    def _rule_based_risks(
        self,
        decisions: list[DecisionDraft],
        action_items: list[ActionItemDraft],
        dependencies: list[DependencyDraft],
    ) -> list[RiskDraft]:
        risks: list[RiskDraft] = []

                              
        for item in action_items:
            if not item.owner_name:
                risks.append(RiskDraft(
                    risk_type="unclear_ownership",
                    severity="high",
                    related_item_title=item.title,
                    related_item_type="action_item",
                    description=f"'{item.title}' has no assigned owner.",
                    recommendation="Assign an owner before the next check-in.",
                ))

                                              
        decision_titles_with_tasks = {
            item.related_decision_title
            for item in action_items
            if item.related_decision_title
        }
        for decision in decisions:
            if decision.title not in decision_titles_with_tasks:
                risks.append(RiskDraft(
                    risk_type="no_follow_up",
                    severity="medium",
                    related_item_title=decision.title,
                    related_item_type="decision",
                    description=f"Decision '{decision.title}' has no action items linked to it.",
                    recommendation="Create at least one action item to execute this decision.",
                ))

                                                                          
        deadline_map = {
            item.title: item.deadline_dt
            for item in action_items
            if item.deadline_dt
        }
        for dep in dependencies:
            up_dl = deadline_map.get(dep.upstream_title)
            down_dl = deadline_map.get(dep.downstream_title)
            if up_dl and down_dl and down_dl < up_dl:
                risks.append(RiskDraft(
                    risk_type="deadline_conflict",
                    severity="critical",
                    related_item_title=dep.downstream_title,
                    related_item_type="action_item",
                    description=(
                        f"'{dep.downstream_title}' is due before its dependency "
                        f"'{dep.upstream_title}' completes."
                    ),
                    recommendation="Adjust deadline or remove the dependency.",
                ))

        return risks

    async def _ai_risks(
        self,
        decisions: list[DecisionDraft],
        action_items: list[ActionItemDraft],
        dependencies: list[DependencyDraft],
    ) -> list[RiskDraft]:
        decisions_ctx = "\n".join(f"- {d.title}: {d.description}" for d in decisions)
        actions_ctx = "\n".join(
            f"- {a.title} | Owner: {a.owner_name or 'None'} | Deadline: {a.deadline_text or 'None'}"
            for a in action_items
        )
        deps_ctx = "\n".join(
            f"- {d.upstream_title} → {d.downstream_title} ({d.dependency_type})"
            for d in dependencies
        ) or "No dependencies detected."

        prompt = (
            self._prompt_template
            .replace("{decisions_context}", decisions_ctx or "None")
            .replace("{action_items_context}", actions_ctx or "None")
            .replace("{dependencies_context}", deps_ctx)
        )

        try:
            response = await self._client.complete(
                system_prompt=prompt,
                user_prompt="Analyze the above and identify execution risks.",
                max_tokens=2000,
                temperature=0.1,
                json_mode=True,
            )
            data = GroqClient.parse_json(response.content)
            return [
                RiskDraft(
                    risk_type=r.get("risk_type", "no_follow_up"),
                    severity=r.get("severity", "medium"),
                    related_item_title=r.get("related_item_title", "Unknown"),
                    related_item_type=r.get("related_item_type", "action_item"),
                    description=r.get("description", ""),
                    recommendation=r.get("recommendation", ""),
                )
                for r in data.get("risks", [])
            ]
        except Exception as exc:
            logger.warning("s5_ai_failed", error=str(exc))
            return []
