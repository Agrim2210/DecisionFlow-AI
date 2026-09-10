   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.domains.graph.application.commands import (
    AddDependencyCommand,
    BulkAddDependenciesCommand,
    RemoveDependencyCommand,
)
from app.domains.graph.application.cycle_detector import CycleDetector
from app.domains.graph.application.queries import (
    GetDependencyQuery,
    GetMeetingGraphQuery,
    GetTaskDependenciesQuery,
)
from app.domains.graph.domain.entities import DependencyGraph, TaskDependency
from app.domains.graph.domain.exceptions import (
    CircularDependencyError,
    DependencyNotFoundError,
    DuplicateDependencyError,
    SelfDependencyError,
)
from app.domains.graph.domain.repositories import IDependencyRepository
from app.domains.graph.domain.value_objects import (
    ConfidenceScore,
    DetectedBy,
    DependencyType,
    GraphEdge,
    GraphNode,
)

logger = structlog.get_logger(__name__)


class DependencyService:
       

    def __init__(
        self,
        dep_repo: IDependencyRepository,
        cycle_detector: CycleDetector | None = None,
    ) -> None:
        self._repo = dep_repo
        self._cycle = cycle_detector or CycleDetector()

                                                                    

    async def add_dependency(self, cmd: AddDependencyCommand) -> TaskDependency:
           
                            
        if cmd.upstream_id == cmd.downstream_id:
            raise SelfDependencyError()

                            
        already_exists = await self._repo.exists(
            upstream_id=cmd.upstream_id,
            downstream_id=cmd.downstream_id,
            org_id=cmd.org_id,
        )
        if already_exists:
            raise DuplicateDependencyError(
                f"Dependency {cmd.upstream_id} → {cmd.downstream_id} already exists"
            )

                                                                           
        existing = await self._repo.get_all_for_org(cmd.org_id)
        if self._cycle.would_create_cycle(existing, cmd.upstream_id, cmd.downstream_id):
            cycle_path = self._cycle.find_cycle_path(existing, cmd.upstream_id, cmd.downstream_id)
            raise CircularDependencyError(
                f"Adding this dependency would create a cycle: "
                f"{' → '.join(cycle_path) if cycle_path else str(cmd.upstream_id) + ' → ' + str(cmd.downstream_id)}"
            )

                                     
        dep_type = DependencyType.safe(cmd.dependency_type)

                    
        dep = TaskDependency(
            id=uuid.uuid4(),
            org_id=cmd.org_id,
            upstream_id=cmd.upstream_id,
            downstream_id=cmd.downstream_id,
            dependency_type=dep_type.value,
            detected_by=DetectedBy.MANUAL,
            confidence_score=1.0,
            created_by=cmd.created_by,
        )
        result = await self._repo.create(dep)

        logger.info(
            "dependency_added",
            dep_id=str(result.id),
            upstream=str(cmd.upstream_id),
            downstream=str(cmd.downstream_id),
            org_id=str(cmd.org_id),
            by=str(cmd.created_by),
        )
        return result

                                                                     

    async def bulk_add_from_pipeline(
        self, cmd: BulkAddDependenciesCommand
    ) -> list[TaskDependency]:
           
        if not cmd.edges:
            return []

        existing = await self._repo.get_all_for_org(cmd.org_id)

                                                                         
        candidate_pairs: list[tuple[str, str]] = []
        edge_map: dict[tuple[str, str], dict] = {}

        for edge in cmd.edges:
            try:
                up_id = str(edge["upstream_id"])
                down_id = str(edge["downstream_id"])
            except (KeyError, TypeError):
                logger.warning("bulk_dependency_invalid_edge", edge=str(edge))
                continue

            if up_id == down_id:
                logger.warning("bulk_dependency_self_loop", task_id=up_id)
                continue

            candidate_pairs.append((up_id, down_id))
            edge_map[(up_id, down_id)] = edge

                                    
        safe_pairs, rejected_pairs = self._cycle.validate_bulk_edges(
            existing, candidate_pairs
        )

        if rejected_pairs:
            logger.warning(
                "bulk_dependencies_cycle_rejected",
                count=len(rejected_pairs),
                org_id=str(cmd.org_id),
            )

                                                                
        to_create: list[TaskDependency] = []
        for up_str, down_str in safe_pairs:
            raw = edge_map[(up_str, down_str)]

                                    
            try:
                up_uuid = uuid.UUID(up_str)
                down_uuid = uuid.UUID(down_str)
            except ValueError:
                continue

            already = await self._repo.exists(
                upstream_id=up_uuid, downstream_id=down_uuid, org_id=cmd.org_id
            )
            if already:
                logger.debug(
                    "bulk_dependency_duplicate_skipped",
                    upstream=up_str,
                    downstream=down_str,
                )
                continue

            dep_type = DependencyType.safe(raw.get("dependency_type", "finish_to_start"))
            confidence = ConfidenceScore.safe(raw.get("confidence_score"))

            to_create.append(TaskDependency(
                id=uuid.uuid4(),
                org_id=cmd.org_id,
                upstream_id=up_uuid,
                downstream_id=down_uuid,
                dependency_type=dep_type.value,
                detected_by=DetectedBy.AI,
                confidence_score=float(confidence),
            ))

        if not to_create:
            return []

        created = await self._repo.bulk_create(to_create)
        logger.info(
            "bulk_dependencies_persisted",
            count=len(created),
            org_id=str(cmd.org_id),
        )
        return created

                                                                    

    async def remove_dependency(self, cmd: RemoveDependencyCommand) -> None:
           
        deleted = await self._repo.delete(cmd.dep_id, cmd.org_id)
        if not deleted:
            raise DependencyNotFoundError(
                f"Dependency {cmd.dep_id} not found in this organization"
            )

        logger.info(
            "dependency_removed",
            dep_id=str(cmd.dep_id),
            org_id=str(cmd.org_id),
            by=str(cmd.removed_by),
        )

                                                                    

    async def get_dependency(self, query: GetDependencyQuery) -> TaskDependency:
        dep = await self._repo.get_by_id(query.dep_id, query.org_id)
        if not dep:
            raise DependencyNotFoundError()
        return dep

    async def get_task_dependencies(
        self, query: GetTaskDependenciesQuery
    ) -> list[TaskDependency]:
           
        return await self._repo.list_for_task(query.task_id, query.org_id)

    async def get_meeting_graph(
        self, query: GetMeetingGraphQuery
    ) -> DependencyGraph:
           
        deps = await self._repo.list_by_meeting(query.meeting_id, query.org_id)

        if not deps:
            return DependencyGraph(
                meeting_id=query.meeting_id,
                org_id=query.org_id,
                nodes=[],
                edges=[],
            )

                                     
        task_ids: set[uuid.UUID] = set()
        for dep in deps:
            task_ids.add(dep.upstream_id)
            task_ids.add(dep.downstream_id)

                                                
        task_map: dict[str, dict] = {}
        try:
            task_map = await self._load_task_metadata(list(task_ids), query.org_id)
        except Exception as exc:
            logger.warning("graph_task_metadata_failed", error=str(exc))
                                        
            task_map = {}

                     
        nodes: list[dict] = []
        for task_id in task_ids:
            task_id_str = str(task_id)
            meta = task_map.get(task_id_str, {})
            nodes.append({
                "id":           task_id_str,
                "label":        meta.get("title", task_id_str)[:60],
                "status":       meta.get("status", "unknown"),
                "priority":     meta.get("priority", "medium"),
                "owner_id":     meta.get("owner_id"),
                "is_overdue":   meta.get("is_overdue", False),
                "is_unassigned":meta.get("is_unassigned", True),
                "meeting_id":   str(query.meeting_id),
            })

                     
        dep_type_vo = DependencyType
        edges: list[dict] = []
        for dep in deps:
            edges.append({
                "id":               str(dep.id),
                "source":           str(dep.upstream_id),
                "target":           str(dep.downstream_id),
                "type":             dep.dependency_type,
                "label":            dep_type_vo.safe(dep.dependency_type).label,
                "detected_by":      dep.detected_by,
                "confidence_score": dep.confidence_score,
            })

        return DependencyGraph(
            meeting_id=query.meeting_id,
            org_id=query.org_id,
            nodes=nodes,
            edges=edges,
        )

                                                                    

    async def _load_task_metadata(
        self, task_ids: list[uuid.UUID], org_id: uuid.UUID
    ) -> dict[str, dict]:
           
        from app.domains.extraction.infra.orm_models import ActionItemORM
        from sqlalchemy import select

                                                                           
        if not hasattr(self, "_db") or self._db is None:
            return {}

        result = await self._db.execute(
            select(
                ActionItemORM.id,
                ActionItemORM.title,
                ActionItemORM.status,
                ActionItemORM.priority,
                ActionItemORM.owner_id,
                ActionItemORM.due_date,
            ).where(
                ActionItemORM.id.in_(task_ids),
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
        )
        rows = result.fetchall()

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        metadata: dict[str, dict] = {}
        for row in rows:
            is_overdue = (
                row.due_date is not None
                and row.due_date < now
                and row.status not in ("completed", "cancelled")
            )
            metadata[str(row.id)] = {
                "title":        row.title,
                "status":       row.status,
                "priority":     row.priority,
                "owner_id":     str(row.owner_id) if row.owner_id else None,
                "is_overdue":   is_overdue,
                "is_unassigned": row.owner_id is None,
            }
        return metadata


class DependencyServiceWithDB(DependencyService):
       

    def __init__(
        self,
        dep_repo: IDependencyRepository,
        db,                                                                                     
        cycle_detector: CycleDetector | None = None,
    ) -> None:
        super().__init__(dep_repo=dep_repo, cycle_detector=cycle_detector)
        self._db = db
