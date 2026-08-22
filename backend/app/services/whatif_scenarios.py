"""What-If Scenarios — grounded projections, not LLM speculation.

Every preset scenario here computes its projected numbers from the simulation's own
live formulas and current data. Only two mechanics in this codebase actually connect a
policy lever to a real outcome today:

  1. Police effectiveness/officers -> crime solve chance (crime_engine.py:155-164)
  2. Tax rate -> citizen net salary (economy_engine.py:49-51)

Department budget/efficiency and hospital quality/staff are NOT wired to any downstream
effect in the simulation (verified by direct code inspection) — so a "what if we boost
the healthcare budget" scenario can't honestly claim a grounded health outcome the way
police funding can claim a grounded crime outcome. Rather than inventing a formula that
doesn't exist elsewhere in the sim, this module only offers grounded presets for the
mechanics that are actually real, plus infrastructure scenarios that reuse the already-
grounded impact_strategies.py system. The LLM is used only to phrase a plain-language
summary of numbers already computed here — it never generates the numbers themselves.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.crime import CrimeRecord, PoliceUnit
from backend.app.models.city import District
from backend.app.services.llm_service import get_llm_service

# Real-world estimate — officer headcount isn't tied to Department.budget anywhere in
# the simulation, so converting a budget increase into new officers requires a stated
# assumption. Everything downstream of this number uses the exact live formula.
OFFICER_ANNUAL_COST = 70_000
ECONOMY_ENGINE_TAX_RATE = 0.15  # the live default in economy_engine.py — not persisted anywhere


@dataclass
class ScenarioResult:
    scenario_key: str
    title: str
    grounded: bool = True
    assumptions: list[str] = field(default_factory=list)
    current_state: dict = field(default_factory=dict)
    projected_state: dict = field(default_factory=dict)
    deltas: dict = field(default_factory=dict)
    cost: float | None = None
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "scenario_key": self.scenario_key,
            "title": self.title,
            "grounded": self.grounded,
            "assumptions": self.assumptions,
            "current_state": self.current_state,
            "projected_state": self.projected_state,
            "deltas": self.deltas,
            "cost": self.cost,
            "narrative": self.narrative,
        }


def _capacity_bonus(total_effectiveness: float, unsolved_count: int) -> float:
    """The exact formula from crime_engine.py:162 — reused verbatim, not approximated."""
    return min(0.2, total_effectiveness / max(unsolved_count, 1) * 0.01)


async def police_funding_scenario(db: AsyncSession, budget_increase: float) -> ScenarioResult:
    units_result = await db.execute(select(PoliceUnit).where(PoliceUnit.is_active.is_(True)))
    units = list(units_result.scalars().all())
    current_officers = sum(u.officers for u in units)
    current_total_effectiveness = sum(u.effectiveness * u.officers for u in units) if units else 5.0

    new_officers = max(0, int(budget_increase / OFFICER_ANNUAL_COST))
    avg_effectiveness = current_total_effectiveness / max(current_officers, 1)
    projected_total_effectiveness = current_total_effectiveness + new_officers * avg_effectiveness

    unsolved_result = await db.execute(
        select(sqlfunc.count()).select_from(CrimeRecord).where(CrimeRecord.is_solved.is_(False))
    )
    unsolved_count = min(20, unsolved_result.scalar() or 0)  # the investigation query itself caps at 20/tick

    # Reference backlog sizes so the (real, capped-at-0.2) bonus is shown at both the
    # city's actual current backlog and a heavier one — funding matters more when the
    # backlog is large; at a near-zero backlog the bonus is already near its cap.
    reference_backlogs = sorted(set([max(1, unsolved_count), 20]))
    bonus_before = {n: round(_capacity_bonus(current_total_effectiveness, n), 4) for n in reference_backlogs}
    bonus_after = {n: round(_capacity_bonus(projected_total_effectiveness, n), 4) for n in reference_backlogs}

    return ScenarioResult(
        scenario_key="police_funding",
        title=f"Increase Police Funding by ${budget_increase:,.0f}/yr",
        assumptions=[
            f"Officer headcount isn't tied to department budget anywhere in the simulation today "
            f"(a real gap, not a design choice) — assumes ~${OFFICER_ANNUAL_COST:,.0f}/yr fully-loaded "
            f"cost per additional officer to translate budget into headcount. Everything downstream of "
            f"that headcount number uses the simulation's exact, unmodified solve-chance formula."
        ],
        current_state={
            "total_officers": current_officers,
            "effectiveness_weighted_capacity": round(current_total_effectiveness, 1),
            "current_unsolved_cases": unsolved_count,
            "solve_chance_bonus_by_backlog": bonus_before,
        },
        projected_state={
            "total_officers": current_officers + new_officers,
            "effectiveness_weighted_capacity": round(projected_total_effectiveness, 1),
            "solve_chance_bonus_by_backlog": bonus_after,
        },
        deltas={
            "new_officers": new_officers,
            "capacity_increase_pct": round((projected_total_effectiveness / current_total_effectiveness - 1) * 100, 1) if current_total_effectiveness else 0,
        },
        cost=budget_increase,
    )


async def tax_rate_scenario(db: AsyncSession, new_tax_rate: float) -> ScenarioResult:
    avg_salary_result = await db.execute(
        select(sqlfunc.avg(Citizen.salary)).where(Citizen.salary > 0, Citizen.is_alive.is_(True))
    )
    avg_salary = float(avg_salary_result.scalar() or 0.0)

    employed_result = await db.execute(
        select(sqlfunc.count()).select_from(Citizen)
        .where(Citizen.is_alive.is_(True), Citizen.occupation != "unemployed")
    )
    employed = employed_result.scalar() or 0

    old_rate = ECONOMY_ENGINE_TAX_RATE
    daily_salary = avg_salary / 30.0
    old_net_daily = daily_salary * (1 - old_rate)
    new_net_daily = daily_salary * (1 - new_tax_rate)
    delta_monthly_per_citizen = (new_net_daily - old_net_daily) * 30
    citywide_monthly_income_delta = delta_monthly_per_citizen * employed

    return ScenarioResult(
        scenario_key="tax_rate",
        title=f"Change Tax Rate to {new_tax_rate * 100:.1f}%",
        assumptions=[
            "Uses economy_engine.py's exact salary-withholding formula (net = daily_salary * (1 - tax_rate)) "
            "applied to the current average salary and employed population — no estimation involved."
        ],
        current_state={"tax_rate": old_rate, "avg_monthly_net_salary": round(daily_salary * (1 - old_rate) * 30, 2), "employed_population": employed},
        projected_state={"tax_rate": new_tax_rate, "avg_monthly_net_salary": round(daily_salary * (1 - new_tax_rate) * 30, 2)},
        deltas={
            "monthly_net_per_citizen": round(delta_monthly_per_citizen, 2),
            "citywide_monthly_income_change": round(citywide_monthly_income_delta, 2),
            "citywide_monthly_tax_revenue_change": round(-citywide_monthly_income_delta, 2),
        },
        cost=None,
    )


async def infrastructure_scenario(db: AsyncSession, infra_type: str, count: int) -> ScenarioResult:
    from backend.app.infrastructure.impact_strategies import IMPACT_STRATEGIES
    from backend.app.infrastructure.config import INFRASTRUCTURE_CONFIG

    strategy = IMPACT_STRATEGIES.get(infra_type)
    cfg = INFRASTRUCTURE_CONFIG.get(infra_type)
    if not strategy or not cfg or cfg.category != "point":
        raise ValueError(f"Unsupported infrastructure type for what-if: {infra_type!r}")

    districts_result = await db.execute(select(District))
    districts = list(districts_result.scalars().all())

    candidates = []
    for d in districts:
        impact = await strategy(db, d.center_x, d.center_y, target_x=None, target_y=None, project_type=infra_type)
        candidates.append((d, impact))
    candidates.sort(key=lambda c: -c[1].ai_score)
    chosen = candidates[:count]

    total_coverage = sum(c[1].coverage_count for c in chosen)
    avg_score = round(sum(c[1].ai_score for c in chosen) / max(len(chosen), 1), 1)
    total_cost = cfg.construction_cost * count

    return ScenarioResult(
        scenario_key=f"build_{infra_type}",
        title=f"Build {count}x {cfg.name}",
        assumptions=[
            f"Locations chosen automatically as the {count} highest-scoring district centers for this "
            f"type (using the same grounded impact model as the 3D Build Mode preview) — an actual build "
            f"could target a more precise spot within a district for a better result than its centroid."
        ],
        current_state={},
        projected_state={"recommended_districts": [c[0].name for c in chosen], "avg_location_suitability_score_out_of_100": avg_score},
        deltas={"total_coverage_gain": total_coverage, "avg_location_suitability_score_out_of_100": avg_score},
        cost=total_cost,
    )


def _fallback_narrative(result: ScenarioResult) -> str:
    parts = [f"{k.replace('_', ' ')}: {v}" for k, v in result.deltas.items()]
    return f"{result.title} — " + "; ".join(parts) + "."


async def add_narrative(result: ScenarioResult) -> ScenarioResult:
    llm = get_llm_service()
    if not llm.is_available:
        result.narrative = _fallback_narrative(result)
        return result

    prompt = (
        f"A city simulation computed these EXACT results for the scenario '{result.title}' using the "
        f"simulation's own real formulas. Do not invent, estimate, or contradict any of these numbers — "
        f"only explain what they mean in plain language for a mayor.\n\n"
        f"Current state: {json.dumps(result.current_state)}\n"
        f"Projected state: {json.dumps(result.projected_state)}\n"
        f"Deltas: {json.dumps(result.deltas)}\n"
        f"Cost: {result.cost}\n"
        f"Stated assumptions: {result.assumptions}\n\n"
        "Write a 2-3 sentence plain-language summary."
    )
    text = await llm.chat(
        messages=[{"role": "user", "content": prompt}],
        system=(
            "You are a city policy analyst. Explain computed numbers plainly and accurately. "
            "Never invent a number that wasn't given to you, and never contradict one that was."
        ),
        temperature=0.3,
        max_tokens=220,
    )
    result.narrative = text.strip() if text else _fallback_narrative(result)
    return result


WHATIF_PRESETS = [
    {
        "key": "police_funding", "name": "Increase Police Funding", "icon": "🚔",
        "params": [{"name": "budget_increase", "label": "Annual budget increase ($)", "type": "number", "default": 500000, "min": 50000, "max": 5000000, "step": 50000}],
    },
    {
        "key": "tax_rate", "name": "Change Tax Rate", "icon": "💰",
        "params": [{"name": "new_tax_rate", "label": "New tax rate", "type": "percent", "default": 0.15, "min": 0.0, "max": 0.5, "step": 0.01}],
    },
    {
        "key": "build_hospital_build", "name": "Build Hospitals", "icon": "🏥",
        "params": [{"name": "count", "label": "Number to build", "type": "int", "default": 2, "min": 1, "max": 5, "step": 1}],
    },
    {
        "key": "build_school_build", "name": "Build Schools", "icon": "🏫",
        "params": [{"name": "count", "label": "Number to build", "type": "int", "default": 2, "min": 1, "max": 5, "step": 1}],
    },
    {
        "key": "build_fire_station_build", "name": "Build Fire Stations", "icon": "🚒",
        "params": [{"name": "count", "label": "Number to build", "type": "int", "default": 2, "min": 1, "max": 5, "step": 1}],
    },
    {
        "key": "build_police_station_build", "name": "Build Police Stations", "icon": "🚓",
        "params": [{"name": "count", "label": "Number to build", "type": "int", "default": 2, "min": 1, "max": 5, "step": 1}],
    },
]


async def run_preset_scenario(db: AsyncSession, key: str, params: dict) -> ScenarioResult:
    if key == "police_funding":
        result = await police_funding_scenario(db, float(params.get("budget_increase", 500000)))
    elif key == "tax_rate":
        result = await tax_rate_scenario(db, float(params.get("new_tax_rate", 0.15)))
    elif key.startswith("build_"):
        infra_type = key[len("build_"):]
        result = await infrastructure_scenario(db, infra_type, int(params.get("count", 2)))
    else:
        raise ValueError(f"Unknown preset scenario key: {key!r}")

    return await add_narrative(result)
