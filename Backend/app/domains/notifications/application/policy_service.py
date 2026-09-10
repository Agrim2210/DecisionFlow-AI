   
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.domains.notifications.application.commands import (
    CreatePolicyCommand,
    UpdatePolicyCommand,
)
from app.domains.notifications.application.queries import ListPoliciesQuery
from app.domains.notifications.domain.entities import EscalationPolicy
from app.domains.notifications.domain.exceptions import PolicyNotFoundError
from app.domains.notifications.domain.repositories import IEscalationPolicyRepository
from app.domains.notifications.domain.value_objects import PolicyConfig
from app.shared.exceptions import BadRequestError, ConflictError

logger = structlog.get_logger(__name__)


class PolicyService:
       

    def __init__(self, policy_repo: IEscalationPolicyRepository) -> None:
        self._repo = policy_repo

                                                                    

    async def create_policy(self, cmd: CreatePolicyCommand) -> EscalationPolicy:
           
                                           
        validated_levels = self._validate_levels(cmd.levels)

        policy = EscalationPolicy(
            id=uuid.uuid4(),
            org_id=cmd.org_id,
            name=cmd.name.strip(),
            is_default=cmd.is_default,
            trigger_after_hours=cmd.trigger_after_hours,
            levels=[lvl.to_dict() for lvl in validated_levels],
        )

                                                                   
        if cmd.is_default:
            await self._clear_existing_default(cmd.org_id)

        result = await self._repo.create(policy)

        logger.info(
            "policy_created",
            policy_id=str(result.id),
            org_id=str(cmd.org_id),
            name=result.name,
            is_default=result.is_default,
            levels=len(validated_levels),
        )
        return result

    async def create_default_for_org(self, org_id: uuid.UUID) -> EscalationPolicy:
           
        existing = await self._repo.get_default(org_id)
        if existing:
            logger.debug("default_policy_already_exists", org_id=str(org_id))
            return existing

        default_levels = PolicyConfig.default_levels()
        policy = EscalationPolicy(
            id=uuid.uuid4(),
            org_id=org_id,
            name="Default Escalation Policy",
            is_default=True,
            trigger_after_hours=24,
            levels=[lvl.to_dict() for lvl in default_levels],
        )
        result = await self._repo.create(policy)

        logger.info(
            "default_policy_created",
            policy_id=str(result.id),
            org_id=str(org_id),
        )
        return result

                                                                    

    async def get_policy(
        self, policy_id: uuid.UUID, org_id: uuid.UUID
    ) -> EscalationPolicy:
                                                                                 
        policy = await self._repo.get_by_id(policy_id, org_id)
        if not policy:
            raise PolicyNotFoundError(
                f"Escalation policy {policy_id} not found in this organization"
            )
        return policy

    async def get_default_policy(self, org_id: uuid.UUID) -> EscalationPolicy:
           
        policy = await self._repo.get_default(org_id)
        if policy:
            return policy
        return await self.create_default_for_org(org_id)

    async def list_policies(self, query: ListPoliciesQuery) -> list[EscalationPolicy]:
           
        return await self._repo.list_by_org(query.org_id)

                                                                    

    async def update_policy(self, cmd: UpdatePolicyCommand) -> EscalationPolicy:
           
        policy = await self._repo.get_by_id(cmd.policy_id, cmd.org_id)
        if not policy:
            raise PolicyNotFoundError()

                                                           
        if cmd.is_default is False and policy.is_default:
            existing_policies = await self._repo.list_by_org(cmd.org_id)
            other_policies = [p for p in existing_policies if p.id != cmd.policy_id]
            if not any(p.is_default for p in other_policies):
                raise BadRequestError(
                    "Cannot remove default status — set another policy as default first",
                    error_code="NO_DEFAULT_POLICY",
                )

                           
        if cmd.name is not None:
            policy.name = cmd.name.strip()

                                          
        if cmd.trigger_after_hours is not None:
            if cmd.trigger_after_hours < 1 or cmd.trigger_after_hours > 720:
                raise BadRequestError(
                    "trigger_after_hours must be between 1 and 720",
                    error_code="INVALID_TRIGGER_HOURS",
                )
            policy.trigger_after_hours = cmd.trigger_after_hours

                                                          
        if cmd.levels is not None:
            validated_levels = self._validate_levels(cmd.levels)
            policy.levels = [lvl.to_dict() for lvl in validated_levels]

                                     
        if cmd.is_default is True and not policy.is_default:
            await self._clear_existing_default(cmd.org_id)
            policy.is_default = True
        elif cmd.is_default is False and policy.is_default:
            policy.is_default = False

        policy.updated_at = datetime.now(timezone.utc)
        updated = await self._repo.update(policy)

        logger.info(
            "policy_updated",
            policy_id=str(cmd.policy_id),
            org_id=str(cmd.org_id),
            is_default=updated.is_default,
        )
        return updated

    async def set_as_default(
        self, policy_id: uuid.UUID, org_id: uuid.UUID
    ) -> EscalationPolicy:
           
        policy = await self._repo.get_by_id(policy_id, org_id)
        if not policy:
            raise PolicyNotFoundError()

        if policy.is_default:
            return policy                            

        await self._clear_existing_default(org_id)

        policy.is_default = True
        policy.updated_at = datetime.now(timezone.utc)
        updated = await self._repo.update(policy)

        logger.info(
            "policy_set_as_default",
            policy_id=str(policy_id),
            org_id=str(org_id),
        )
        return updated

                                                                    

    def _validate_levels(
        self, raw_levels: list[dict[str, Any]]
    ) -> list[PolicyConfig]:
           
        if not raw_levels:
            return PolicyConfig.default_levels()

        validated: list[PolicyConfig] = []
        seen_levels: set[int] = set()

        for raw in raw_levels:
            try:
                config = PolicyConfig.from_dict(raw)
            except (ValueError, KeyError, TypeError) as exc:
                raise BadRequestError(
                    f"Invalid escalation level config: {exc}",
                    error_code="INVALID_POLICY_LEVEL",
                )

            if config.level in seen_levels:
                raise BadRequestError(
                    f"Duplicate level number: {config.level}",
                    error_code="DUPLICATE_LEVEL",
                )
            seen_levels.add(config.level)
            validated.append(config)

                                                              
        sorted_levels = sorted(validated, key=lambda c: c.level)
        for i, config in enumerate(sorted_levels, start=1):
            if config.level != i:
                raise BadRequestError(
                    f"Level numbers must be sequential starting at 1. "
                    f"Expected level {i}, got {config.level}",
                    error_code="NON_SEQUENTIAL_LEVELS",
                )

        return sorted_levels

    async def _clear_existing_default(self, org_id: uuid.UUID) -> None:
           
        current_default = await self._repo.get_default(org_id)
        if current_default:
            current_default.is_default = False
            current_default.updated_at = datetime.now(timezone.utc)
            await self._repo.update(current_default)
            logger.debug(
                "default_policy_demoted",
                old_default_id=str(current_default.id),
                org_id=str(org_id),
            )
