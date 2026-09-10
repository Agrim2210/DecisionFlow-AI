   
from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.domains.notifications.application.commands import (
    AdvanceEscalationCommand,
    CreatePolicyCommand,
    DismissEscalationCommand,
    ResolveEscalationCommand,
    TriggerEscalationCommand,
    UpdatePolicyCommand,
)
from app.domains.notifications.application.queries import (
    GetEscalationQuery,
    ListEscalationsQuery,
    ListPoliciesQuery,
)
from app.domains.notifications.domain.entities import (
    Escalation,
    EscalationLevel,
    EscalationPolicy,
    EscalationStatus,
    NotifChannel,
    NotifEventType,
    Notification,
    NotifStatus,
)
from app.domains.notifications.domain.exceptions import (
    EscalationAlreadyResolvedError,
    EscalationMaxLevelError,
    EscalationNotFoundError,
    PolicyNotFoundError,
)
from app.domains.notifications.domain.repositories import (
    IEscalationPolicyRepository,
    IEscalationRepository,
    INotificationRepository,
)

logger = structlog.get_logger(__name__)


class EscalationService:

    def __init__(
        self,
        escalation_repo: IEscalationRepository,
        policy_repo: IEscalationPolicyRepository,
        notif_repo: INotificationRepository,
        user_lookup: Any = None,
    ) -> None:
        self._escalations = escalation_repo
        self._policies = policy_repo
        self._notifs = notif_repo
        self._user_lookup = user_lookup

    async def trigger(self, cmd: TriggerEscalationCommand) -> Escalation:
        existing = await self._escalations.get_by_action_item(cmd.action_item_id, cmd.org_id)
        if existing and existing.is_active:
            logger.debug("escalation_already_active", action_item_id=str(cmd.action_item_id))
            return existing

        policy = await self._policies.get_default(cmd.org_id)
        if not policy:
            policy = await self._policies.ensure_default_exists(cmd.org_id)

        escalation = Escalation(
            id=uuid.uuid4(),
            org_id=cmd.org_id,
            action_item_id=cmd.action_item_id,
            policy_id=policy.id,
            current_level=EscalationLevel.ONE,
            status=EscalationStatus.ACTIVE,
        )

        recipients = await self._get_level_recipients(
            level=EscalationLevel.ONE, org_id=cmd.org_id,
            owner_id=cmd.owner_id, policy=policy,
        )

        escalation.trigger(notified_ids=[r["id"] for r in recipients])
        escalation = await self._escalations.create(escalation)

        await self._send_escalation_notifications(
            escalation=escalation, recipients=recipients,
            event_type=NotifEventType.ESCALATION_TRIGGERED,
            subject=f"⚠️ Overdue Task: {cmd.action_item_title}",
            body=(
                f"Task '{cmd.action_item_title}' was due {cmd.due_date_str} "
                f"and has not been completed.\n\n"
                f"Please update the status or mark it complete in DecisionFlow."
            ),
            payload={
                "action_item_id": str(cmd.action_item_id),
                "action_item_title": cmd.action_item_title,
                "due_date": cmd.due_date_str,
                "meeting_title": cmd.meeting_title,
                "escalation_level": EscalationLevel.ONE,
            },
            related_item_id=cmd.action_item_id,
        )

        logger.info("escalation_triggered", escalation_id=str(escalation.id),
                   action_item_id=str(cmd.action_item_id), recipients=len(recipients))
        return escalation

    async def advance(self, cmd: AdvanceEscalationCommand) -> Escalation:
        escalation = await self._escalations.get_by_id(cmd.escalation_id, cmd.org_id)
        if not escalation:
            raise EscalationNotFoundError()
        if not escalation.is_active:
            raise EscalationAlreadyResolvedError()

        policy = await self._policies.get_by_id(escalation.policy_id, cmd.org_id)
        if not policy:
            policy = await self._policies.ensure_default_exists(cmd.org_id)

        next_level = escalation.current_level + 1
        if next_level > policy.max_level:
            raise EscalationMaxLevelError(f"Already at max level ({policy.max_level})")

        recipients = await self._get_level_recipients(
            level=next_level, org_id=cmd.org_id, owner_id=None, policy=policy,
        )

        escalation.advance(new_level=next_level, notified_ids=[r["id"] for r in recipients])
        escalation = await self._escalations.update(escalation)

        event_map = {2: NotifEventType.ESCALATION_LEVEL_2, 3: NotifEventType.ESCALATION_LEVEL_3}
        subject_map = {2: "🚨 Escalated to Manager: Overdue Task", 3: "🔴 Final Escalation: Overdue Task"}

        await self._send_escalation_notifications(
            escalation=escalation, recipients=recipients,
            event_type=event_map.get(next_level, NotifEventType.ESCALATION_LEVEL_2),
            subject=subject_map.get(next_level, f"Escalation Level {next_level}"),
            body=(
                f"An overdue task has been escalated to level {next_level}.\n\n"
                f"Escalation ID: {escalation.id}\n"
                f"Please review and take ownership of this task."
            ),
            payload={
                "escalation_id": str(escalation.id),
                "action_item_id": str(escalation.action_item_id),
                "escalation_level": next_level,
            },
            related_item_id=escalation.action_item_id,
        )

        logger.info("escalation_advanced", escalation_id=str(escalation.id), new_level=next_level)
        return escalation

    async def resolve(self, cmd: ResolveEscalationCommand) -> Escalation:
        escalation = await self._escalations.get_by_id(cmd.escalation_id, cmd.org_id)
        if not escalation:
            raise EscalationNotFoundError()
        if not escalation.is_active:
            raise EscalationAlreadyResolvedError()
        escalation.resolve(cmd.resolved_by)
        escalation = await self._escalations.update(escalation)
        logger.info("escalation_resolved", escalation_id=str(cmd.escalation_id))
        return escalation

    async def dismiss(self, cmd: DismissEscalationCommand) -> Escalation:
        escalation = await self._escalations.get_by_id(cmd.escalation_id, cmd.org_id)
        if not escalation:
            raise EscalationNotFoundError()
        if not escalation.is_active:
            raise EscalationAlreadyResolvedError()
        escalation.dismiss(cmd.dismissed_by)
        escalation = await self._escalations.update(escalation)
        logger.info("escalation_dismissed", escalation_id=str(cmd.escalation_id))
        return escalation

    async def list_escalations(self, query: ListEscalationsQuery) -> list[Escalation]:
        return await self._escalations.list_all(
            org_id=query.org_id, status=query.status,
            limit=query.limit + 1, cursor_id=query.cursor_id,
        )

    async def get_escalation(self, query: GetEscalationQuery) -> Escalation:
        esc = await self._escalations.get_by_id(query.escalation_id, query.org_id)
        if not esc:
            raise EscalationNotFoundError()
        return esc

    async def create_policy(self, cmd: CreatePolicyCommand) -> EscalationPolicy:
        policy = EscalationPolicy(
            id=uuid.uuid4(), org_id=cmd.org_id, name=cmd.name,
            is_default=cmd.is_default, trigger_after_hours=cmd.trigger_after_hours,
            levels=cmd.levels or [
                {"level": 1, "notify": "owner",      "after_hours": 0},
                {"level": 2, "notify": "admin",      "after_hours": 24},
                {"level": 3, "notify": "owner_role", "after_hours": 48},
            ],
        )
        return await self._policies.create(policy)

    async def update_policy(self, cmd: UpdatePolicyCommand) -> EscalationPolicy:
        policy = await self._policies.get_by_id(cmd.policy_id, cmd.org_id)
        if not policy:
            raise PolicyNotFoundError()
        if cmd.name is not None:
            policy.name = cmd.name
        if cmd.trigger_after_hours is not None:
            policy.trigger_after_hours = cmd.trigger_after_hours
        if cmd.levels is not None:
            policy.levels = cmd.levels
        if cmd.is_default is not None:
            policy.is_default = cmd.is_default
        return await self._policies.update(policy)

    async def list_policies(self, query: ListPoliciesQuery) -> list[EscalationPolicy]:
        return await self._policies.list_by_org(query.org_id)

    async def _get_level_recipients(
        self, level: int, org_id: uuid.UUID, owner_id: uuid.UUID | None,
        policy: EscalationPolicy,
    ) -> list[dict]:
        level_config = policy.get_level_config(level)
        notify_type = level_config.get("notify", "owner") if level_config else "owner"
        recipients: list[dict] = []

        if self._user_lookup:
            try:
                all_users = await self._user_lookup(org_id)
                if notify_type == "owner" and owner_id:
                    user = next((u for u in all_users if u["id"] == owner_id), None)
                    recipients = [user] if user else [u for u in all_users if u["role"] in ("admin", "owner")]
                elif notify_type == "admin":
                    recipients = [u for u in all_users if u["role"] in ("admin", "owner")]
                elif notify_type == "owner_role":
                    recipients = [u for u in all_users if u["role"] == "owner"]
                else:
                    recipients = [u for u in all_users if u["role"] in ("admin", "owner")]
            except Exception as exc:
                logger.warning("user_lookup_failed", error=str(exc))

        if level == EscalationLevel.ONE and owner_id and not recipients:
            recipients = [{"id": owner_id, "email": None, "name": "Task Owner"}]

        return recipients

    async def _send_escalation_notifications(
        self, escalation: Escalation, recipients: list[dict], event_type: str,
        subject: str, body: str, payload: dict, related_item_id: uuid.UUID | None = None,
    ) -> None:
        notifications: list[Notification] = []
        for recipient in recipients:
            recipient_id = recipient["id"]
            if isinstance(recipient_id, str):
                try:
                    recipient_id = uuid.UUID(recipient_id)
                except ValueError:
                    continue

            for channel in [NotifChannel.IN_APP, NotifChannel.EMAIL]:
                notifications.append(Notification(
                    id=uuid.uuid4(), org_id=escalation.org_id,
                    recipient_id=recipient_id, event_type=event_type,
                    channel=channel, status=NotifStatus.PENDING,
                    subject=subject, body=body,
                    related_item_id=related_item_id, related_item_type="action_item",
                    payload={**payload, "recipient_name": recipient.get("name", "")},
                ))

        if notifications:
            await self._notifs.bulk_create(notifications)
            logger.debug("escalation_notifications_created", count=len(notifications),
                        escalation_id=str(escalation.id))
