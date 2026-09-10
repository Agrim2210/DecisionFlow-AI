   
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.groq_client import GroqClient
from app.domains.extraction.domain.pipeline.stages.s3_action_extractor import ActionItemDraft

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "v1" / "detect_dependencies.txt"


@dataclass
class DependencyDraft:
    upstream_title: str                          
    downstream_title: str                                   
    dependency_type: str                                                         
    confidence_score: float
    reasoning: str = ""


class S4DependencyDetector:

    def __init__(self, client: BaseAIClient | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    async def run(self, action_items: list[ActionItemDraft]) -> list[DependencyDraft]:
           
        t0 = time.perf_counter()

        if len(action_items) < 2:
            return []

        items_context = self._format_items(action_items)
        prompt_text = self._prompt_template.replace("{action_items_context}", items_context)

        try:
            response = await self._client.complete(
                system_prompt=prompt_text,
                user_prompt="Analyze the action items above and identify all dependencies.",
                max_tokens=2000,
                temperature=0.1,
                json_mode=True,
            )
            data = GroqClient.parse_json(response.content)
        except Exception as exc:
            logger.warning("s4_ai_failed", error=str(exc))
            return []

        raw_deps = [
            DependencyDraft(
                upstream_title=d.get("upstream_task_title", ""),
                downstream_title=d.get("downstream_task_title", ""),
                dependency_type=d.get("dependency_type", "finish_to_start"),
                confidence_score=float(d.get("confidence_score", 0.8)),
                reasoning=d.get("reasoning", ""),
            )
            for d in data.get("dependencies", [])
            if d.get("upstream_task_title") and d.get("downstream_task_title")
            and float(d.get("confidence_score", 0)) >= 0.65
        ]

                                               
        valid_titles = {item.title for item in action_items}
        raw_deps = [
            d for d in raw_deps
            if d.upstream_title in valid_titles and d.downstream_title in valid_titles
        ]

                                                               
        safe_deps = self._remove_cycles(raw_deps)

        logger.info(
            "s4_complete",
            raw_deps=len(raw_deps),
            safe_deps=len(safe_deps),
            cycles_removed=len(raw_deps) - len(safe_deps),
            elapsed=round(time.perf_counter() - t0, 2),
        )
        return safe_deps

    def _format_items(self, items: list[ActionItemDraft]) -> str:
        lines = []
        for item in items:
            owner = item.owner_name or "Unassigned"
            deadline = item.deadline_text or "No deadline"
            lines.append(
                f"- Title: {item.title}\n"
                f"  Owner: {owner} | Deadline: {deadline} | Priority: {item.priority}\n"
                f"  Description: {item.description}"
            )
        return "\n\n".join(lines)

    def _remove_cycles(self, deps: list[DependencyDraft]) -> list[DependencyDraft]:
           
        safe: list[DependencyDraft] = []
        graph: dict[str, set[str]] = defaultdict(set)

        for dep in deps:
                                  
            graph[dep.upstream_title].add(dep.downstream_title)

            if self._has_cycle(graph):
                                         
                graph[dep.upstream_title].discard(dep.downstream_title)
                logger.warning(
                    "dependency_cycle_prevented",
                    upstream=dep.upstream_title,
                    downstream=dep.downstream_title,
                )
            else:
                safe.append(dep)

        return safe

    @staticmethod
    def _has_cycle(graph: dict[str, set[str]]) -> bool:
                                                                       
        in_degree: dict[str, int] = defaultdict(int)
        all_nodes: set[str] = set()

        for node, neighbors in graph.items():
            all_nodes.add(node)
            for n in neighbors:
                in_degree[n] += 1
                all_nodes.add(n)

        queue = deque(n for n in all_nodes if in_degree.get(n, 0) == 0)
        processed = 0

        while queue:
            node = queue.popleft()
            processed += 1
            for neighbor in graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return processed != len(all_nodes)
