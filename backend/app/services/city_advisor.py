"""
AI City Advisor: LLM-powered analysis of city metrics, trends, active crises.
Provides natural language policy recommendations, what-if scenario analysis,
and narrative city reports.
"""

from __future__ import annotations

import json
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.llm_service import get_llm_service

log = structlog.get_logger()

ADVISOR_SYSTEM = """You are the AI City Advisor for a digital twin smart city simulation.
You analyze city data, identify trends, and provide actionable policy recommendations.

Your responses should be:
- Data-driven and specific (reference actual numbers)
- Actionable with clear priority levels
- Balanced between short-term and long-term thinking
- Aware of trade-offs between different city objectives

Always respond in valid JSON format as specified."""


class CityAdvisor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    @property
    def is_available(self) -> bool:
        return self.llm.is_available

    async def analyze_city_state(self, metrics: dict, history: list[dict] | None = None) -> dict | None:
        if not self.is_available:
            return self._rule_based_analysis(metrics)

        metrics_summary = self._format_metrics(metrics)
        trend_summary = self._format_trends(history) if history else "No historical data."

        prompt = (
            f"Current city metrics:\n{metrics_summary}\n\n"
            f"Recent trends:\n{trend_summary}\n\n"
            "Analyze the city's current state. Identify the top 3 issues and "
            "provide specific policy recommendations for each."
        )

        result = await self.llm.generate_json(
            prompt=prompt,
            system=ADVISOR_SYSTEM,
            schema_hint="""{
  "overall_assessment": "string (1-2 sentences)",
  "risk_level": "low|moderate|high|critical",
  "top_issues": [
    {
      "issue": "string",
      "severity": "low|medium|high|critical",
      "metric": "string (the metric driving this)",
      "recommendation": "string",
      "expected_impact": "string"
    }
  ],
  "positive_trends": ["string"],
  "action_priority": "string (what to do first)"
}""",
            temperature=0.5,
        )

        return result or self._rule_based_analysis(metrics)

    async def scenario_analysis(
        self, metrics: dict, scenario: str
    ) -> dict | None:
        if not self.is_available:
            return {"analysis": "LLM not available for scenario analysis.", "feasible": True}

        metrics_summary = self._format_metrics(metrics)

        prompt = (
            f"Current city metrics:\n{metrics_summary}\n\n"
            f"Proposed scenario: {scenario}\n\n"
            "Analyze the likely outcomes of this scenario. Consider impact on "
            "population happiness, health, economy, stress, and any side effects."
        )

        return await self.llm.generate_json(
            prompt=prompt,
            system=ADVISOR_SYSTEM,
            schema_hint="""{
  "scenario": "string",
  "feasible": true/false,
  "analysis": "string (2-3 sentences)",
  "projected_impacts": {
    "happiness": "increase|decrease|stable (with magnitude)",
    "health": "increase|decrease|stable",
    "economy": "increase|decrease|stable",
    "stress": "increase|decrease|stable"
  },
  "risks": ["string"],
  "timeline": "string (short-term or long-term)",
  "recommendation": "proceed|modify|reject"
}""",
            temperature=0.6,
        )

    async def generate_city_report(
        self, metrics: dict, history: list[dict] | None = None,
        events: list[dict] | None = None,
    ) -> str | None:
        if not self.is_available:
            return self._rule_based_report(metrics)

        metrics_summary = self._format_metrics(metrics)
        trend_summary = self._format_trends(history) if history else "No historical data."
        events_summary = self._format_events(events) if events else "No active events."

        prompt = (
            f"City metrics:\n{metrics_summary}\n\n"
            f"Trends:\n{trend_summary}\n\n"
            f"Active events:\n{events_summary}\n\n"
            "Write a concise city status report (3-5 paragraphs) that a mayor "
            "would read. Include key highlights, concerns, and recommendations. "
            "Write in a professional but accessible tone. Just the report text, no JSON."
        )

        return await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system=(
                "You are the AI City Advisor writing a briefing for the mayor. "
                "Be concise, data-driven, and actionable."
            ),
            temperature=0.6,
            max_tokens=800,
        )

    async def ask_advisor(self, question: str, metrics: dict) -> str | None:
        if not self.is_available:
            return "AI Advisor is not available. Configure an LLM provider in settings."

        metrics_summary = self._format_metrics(metrics)

        prompt = (
            f"City metrics:\n{metrics_summary}\n\n"
            f"Question: {question}\n\n"
            "Answer the question based on the city data. Be specific and actionable."
        )

        return await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system=ADVISOR_SYSTEM,
            temperature=0.6,
            max_tokens=500,
        )

    def _format_metrics(self, metrics: dict) -> str:
        lines = []
        key_metrics = [
            ("population", "Population"),
            ("employed", "Employed"),
            ("unemployed", "Unemployed"),
            ("unemployment_rate", "Unemployment Rate"),
            ("avg_happiness", "Avg Happiness"),
            ("avg_health", "Avg Health"),
            ("avg_stress", "Avg Stress"),
            ("total_gdp", "Total GDP"),
            ("avg_income", "Avg Income"),
            ("active_events", "Active Events"),
        ]
        for key, label in key_metrics:
            if key in metrics:
                val = metrics[key]
                if isinstance(val, float) and val < 1.0:
                    lines.append(f"- {label}: {val:.1%}")
                elif isinstance(val, float):
                    lines.append(f"- {label}: ${val:,.0f}")
                else:
                    lines.append(f"- {label}: {val}")
        return "\n".join(lines) if lines else "No metrics available."

    def _format_trends(self, history: list[dict]) -> str:
        if not history or len(history) < 2:
            return "Insufficient historical data."
        recent = history[-1]
        earlier = history[0]
        lines = []
        for key in ["avg_happiness", "avg_health", "avg_stress", "unemployment_rate"]:
            if key in recent and key in earlier:
                delta = recent[key] - earlier[key]
                direction = "up" if delta > 0 else "down"
                lines.append(f"- {key}: {direction} {abs(delta):.2%} over {len(history)} snapshots")
        return "\n".join(lines) if lines else "Stable trends."

    def _format_events(self, events: list[dict]) -> str:
        if not events:
            return "No active events."
        return "\n".join(
            f"- {e.get('name', 'Unknown')} ({e.get('severity', 'unknown')} severity)"
            for e in events
        )

    def _rule_based_analysis(self, metrics: dict) -> dict:
        issues = []
        positives = []

        unemployment = metrics.get("unemployment_rate", 0)
        if unemployment > 0.15:
            issues.append({
                "issue": "High unemployment",
                "severity": "high",
                "metric": f"{unemployment:.1%}",
                "recommendation": "Launch job creation programs and business incentives",
                "expected_impact": "Reduce unemployment by 5-10%",
            })

        avg_happiness = metrics.get("avg_happiness", 0.5)
        if avg_happiness < 0.4:
            issues.append({
                "issue": "Low citizen happiness",
                "severity": "high",
                "metric": f"{avg_happiness:.1%}",
                "recommendation": "Organize community events and improve public services",
                "expected_impact": "Boost happiness by 10-15%",
            })
        elif avg_happiness > 0.7:
            positives.append(f"High citizen happiness at {avg_happiness:.1%}")

        avg_stress = metrics.get("avg_stress", 0.3)
        if avg_stress > 0.6:
            issues.append({
                "issue": "High population stress",
                "severity": "medium",
                "metric": f"{avg_stress:.1%}",
                "recommendation": "Invest in parks, mental health services, and reduce work hours",
                "expected_impact": "Reduce stress by 10-20%",
            })

        avg_health = metrics.get("avg_health", 0.8)
        if avg_health < 0.6:
            issues.append({
                "issue": "Population health concerns",
                "severity": "high",
                "metric": f"{avg_health:.1%}",
                "recommendation": "Increase healthcare funding and deploy free checkup programs",
                "expected_impact": "Improve health metrics by 15%",
            })

        if not issues:
            issues.append({
                "issue": "No critical issues detected",
                "severity": "low",
                "metric": "All within normal range",
                "recommendation": "Maintain current policies",
                "expected_impact": "Sustained stability",
            })

        risk = "low"
        high_count = sum(1 for i in issues if i["severity"] in ("high", "critical"))
        if high_count >= 2:
            risk = "critical"
        elif high_count == 1:
            risk = "high"
        elif any(i["severity"] == "medium" for i in issues):
            risk = "moderate"

        return {
            "overall_assessment": f"City has {len(issues)} identified issues. Risk level: {risk}.",
            "risk_level": risk,
            "top_issues": issues[:3],
            "positive_trends": positives,
            "action_priority": issues[0]["recommendation"] if issues else "Maintain course",
        }

    def _rule_based_report(self, metrics: dict) -> str:
        pop = metrics.get("population", 0)
        happiness = metrics.get("avg_happiness", 0)
        health = metrics.get("avg_health", 0)
        stress = metrics.get("avg_stress", 0)
        unemployment = metrics.get("unemployment_rate", 0)
        gdp = metrics.get("total_gdp", 0)

        return (
            f"City Status Report\n\n"
            f"Population: {pop} citizens. "
            f"Average happiness: {happiness:.1%}, health: {health:.1%}, stress: {stress:.1%}. "
            f"Unemployment rate: {unemployment:.1%}. GDP: ${gdp:,.0f}.\n\n"
            f"{'The city is in good shape overall.' if happiness > 0.5 and health > 0.6 else 'Several metrics need attention.'}\n\n"
            f"Configure an LLM provider for detailed AI-powered analysis."
        )
