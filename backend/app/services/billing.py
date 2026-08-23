"""Simulated credits ledger — Phase 3 of the multi-tenant platform plan.

No real payment gateway anywhere in this module: grant_credits() is the only way
credits enter an org's balance, and it's only ever called from a super_admin action
(the admin portal's "top up" control) — the same "manually seeded test value" pattern
as every other credential in this project. consume_credits() is the automatic side,
wired into the Twin Platform run endpoint alongside Phase 2's usage recording.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.plans import PLAN_BY_KEY
from backend.app.models.auth import Organization
from backend.app.models.billing import CreditTransaction, CreditTransactionType


class InsufficientCreditsError(Exception):
    def __init__(self, requested: float, balance: float):
        self.requested = requested
        self.balance = balance
        super().__init__(f"Requested {requested:.1f} credits exceeds available balance of {balance:.1f}")


async def grant_credits(db: AsyncSession, org: Organization, amount: float, description: str) -> Organization:
    if amount <= 0:
        raise ValueError("grant_credits amount must be positive — use adjust_credits for corrections")
    org.credits_balance += amount
    db.add(CreditTransaction(
        organization_id=org.id, type=CreditTransactionType.GRANT,
        amount=amount, balance_after=org.credits_balance, description=description,
    ))
    await db.commit()
    await db.refresh(org)
    return org


async def adjust_credits(db: AsyncSession, org: Organization, amount: float, description: str) -> Organization:
    """Manual correction — amount may be positive or negative, unlike grant_credits."""
    org.credits_balance += amount
    db.add(CreditTransaction(
        organization_id=org.id, type=CreditTransactionType.ADJUSTMENT,
        amount=amount, balance_after=org.credits_balance, description=description,
    ))
    await db.commit()
    await db.refresh(org)
    return org


def check_credit_balance(org: Organization, cost: float) -> None:
    if cost > org.credits_balance:
        raise InsufficientCreditsError(cost, org.credits_balance)


async def consume_credits(db: AsyncSession, org: Organization, cost: float, description: str) -> None:
    """Caller must have already checked check_credit_balance — this does not
    re-validate, since the Twin Platform run it's billing for has already happened
    by the time this is called (see twin_platform.py). Going slightly negative here
    reflects real usage that occurred; it should never happen if the pre-check ran."""
    org.credits_balance -= cost
    db.add(CreditTransaction(
        organization_id=org.id, type=CreditTransactionType.CONSUMPTION,
        amount=-cost, balance_after=org.credits_balance, description=description,
    ))
    await db.commit()


class UnknownPlanError(Exception):
    def __init__(self, plan_key: str):
        self.plan_key = plan_key
        super().__init__(f"Unknown plan key {plan_key!r}")


async def subscribe_to_plan(db: AsyncSession, org: Organization, plan_key: str) -> Organization:
    """The self-service 'purchase' action — an org_admin picking a plan for their own
    org, not a super_admin override. Still no real payment: choosing a plan here
    instantly switches to it and grants that plan's included_credits, simulating what
    a real subscription would hand you on renewal. Distinct from the super_admin-only
    PUT /organizations/{id}/plan, which changes the plan without granting credits —
    that one is a correction tool, not a purchase."""
    plan = PLAN_BY_KEY.get(plan_key)
    if not plan:
        raise UnknownPlanError(plan_key)

    org.plan_key = plan["key"]
    org.agent_quota = plan["agent_quota"]
    org.model_tier = plan["model_tier"]
    # A subscription's entitlements REPLACE whatever was there before, not merge —
    # switching plans is switching to that plan's included features. A super_admin
    # can still hand-tune beyond the plan defaults afterward via the existing
    # PUT /environments and /modules endpoints; this just sets the starting point.
    org.allowed_environments = list(plan.get("allowed_environments", []))
    org.allowed_modules = list(plan.get("allowed_modules", []))
    await db.commit()
    await db.refresh(org)
    return await grant_credits(db, org, plan["included_credits"], f"Subscribed to {plan['name']}")


async def get_billing_summary(db: AsyncSession, org: Organization) -> dict:
    plan = PLAN_BY_KEY.get(org.plan_key)
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.organization_id == org.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(20)
    )
    recent = result.scalars().all()
    return {
        "plan": plan,
        "credits_balance": org.credits_balance,
        "recent_transactions": [
            {
                "id": str(t.id), "type": t.type.value, "amount": t.amount,
                "balance_after": t.balance_after, "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in recent
        ],
    }
