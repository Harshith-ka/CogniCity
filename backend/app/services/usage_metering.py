"""Usage metering — Phase 2 of the multi-tenant platform plan.

Called only from the optional-auth path in the Twin Platform run endpoint: an
unauthenticated run never touches this module, so the existing open marketplace UI
keeps behaving exactly as it does today. See [[usage.py]] for the table this writes to.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.plans import PLAN_BY_KEY
from backend.app.models.auth import Organization
from backend.app.models.usage import UsageMetricType, UsageRecord


class QuotaExceededError(Exception):
    def __init__(self, requested: int, quota: int):
        self.requested = requested
        self.quota = quota
        super().__init__(f"Requested {requested} agents exceeds organization quota of {quota}")


class SimulationLimitReachedError(Exception):
    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(f"This plan is limited to {limit} simulation runs — subscribe to a paid plan to continue")


def check_agent_quota(org: Organization, requested_agents: int) -> None:
    if requested_agents > org.agent_quota:
        raise QuotaExceededError(requested_agents, org.agent_quota)


async def check_simulation_run_limit(db: AsyncSession, org: Organization) -> None:
    """Only the free trial plan carries a max_simulation_runs cap — every paid plan
    has it set to None (unlimited) in the catalog, so this is a no-op for them."""
    plan = PLAN_BY_KEY.get(org.plan_key)
    limit = plan.get("max_simulation_runs") if plan else None
    if limit is None:
        return
    result = await db.execute(
        select(func.count(UsageRecord.id)).where(
            UsageRecord.organization_id == org.id,
            UsageRecord.metric_type == UsageMetricType.API_REQUEST,
        )
    )
    runs_so_far = result.scalar_one()
    if runs_so_far >= limit:
        raise SimulationLimitReachedError(limit)


async def record_usage(
    db: AsyncSession,
    organization_id: uuid.UUID,
    metric_type: UsageMetricType,
    quantity: float,
    environment_key: str | None = None,
) -> None:
    db.add(UsageRecord(
        organization_id=organization_id,
        metric_type=metric_type,
        quantity=quantity,
        environment_key=environment_key,
    ))
    await db.commit()


async def get_usage_summary(db: AsyncSession, organization_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(UsageRecord.metric_type, func.sum(UsageRecord.quantity), func.count(UsageRecord.id))
        .where(UsageRecord.organization_id == organization_id)
        .group_by(UsageRecord.metric_type)
    )
    totals = {
        metric_type.value: {"total_quantity": float(total or 0), "record_count": count}
        for metric_type, total, count in result.all()
    }
    for metric_type in UsageMetricType:
        totals.setdefault(metric_type.value, {"total_quantity": 0.0, "record_count": 0})
    return totals
