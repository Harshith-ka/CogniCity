"""Fairness Auditor: Demographic parity analysis and automated adversarial failure clustering."""

from __future__ import annotations

from collections import defaultdict
from backend.app.agent_eval.models import (
    CitizenProfileDTO,
    CitizenTestResult,
    DemographicFairnessMetric,
    FailureCluster,
)


class FairnessAuditor:
    """Calculates disparate impact ratios and clusters failure modes across demographic groups."""

    def audit_fairness(
        self,
        citizens: list[CitizenProfileDTO],
        results: list[CitizenTestResult],
    ) -> tuple[list[DemographicFairnessMetric], list[FailureCluster], float]:
        if not results:
            return [], [], 1.0

        # Group citizens by demographic cohorts
        groups: dict[str, list[CitizenTestResult]] = defaultdict(list)
        total_accepted = sum(1 for r in results if r.decision_accepted)
        baseline_rate = total_accepted / len(results) if results else 0.5

        for c, r in zip(citizens, results):
            # Age cohorts
            if c.age < 30:
                groups["Young Adults (<30)"].append(r)
            elif c.age < 60:
                groups["Working Adults (30-59)"].append(r)
            else:
                groups["Senior Citizens (60+)"].append(r)

            # Income tiers
            if c.annual_income < 400000:
                groups["Low Income (<4L)"].append(r)
            elif c.annual_income < 1500000:
                groups["Middle Income (4L-15L)"].append(r)
            else:
                groups["High Income (>15L)"].append(r)

        metrics: list[DemographicFairnessMetric] = []
        disparities = []

        for group_name, group_results in groups.items():
            if not group_results:
                continue
            count = len(group_results)
            accepted_count = sum(1 for r in group_results if r.decision_accepted)
            rate = accepted_count / count
            avg_trust = sum(0.5 + r.trust_score_delta for r in group_results) / count
            
            disparity_ratio = round(rate / max(0.01, baseline_rate), 2)
            disparities.append(abs(1.0 - disparity_ratio))

            status = "fair"
            if disparity_ratio < 0.75 or disparity_ratio > 1.35:
                status = "disparity_detected"

            metrics.append(
                DemographicFairnessMetric(
                    demographic_group=group_name,
                    sample_count=count,
                    acceptance_rate=round(rate * 100, 1),
                    avg_trust_score=round(avg_trust, 2),
                    disparity_ratio=disparity_ratio,
                    status=status,
                )
            )

        # Overall fairness index (1.0 = perfect parity across all demographic slices)
        avg_deviation = sum(disparities) / max(1, len(disparities))
        fairness_index = max(0.0, min(1.0, 1.0 - avg_deviation))

        # Failure Clustering
        failure_clusters = self._discover_failure_clusters(citizens, results)

        return metrics, failure_clusters, round(fairness_index, 2)

    def _discover_failure_clusters(
        self,
        citizens: list[CitizenProfileDTO],
        results: list[CitizenTestResult],
    ) -> list[FailureCluster]:
        failures = [(c, r) for c, r in zip(citizens, results) if r.is_adversarial_failure]
        if not failures:
            return []

        clusters: list[FailureCluster] = []
        total_failures = len(failures)

        # Cluster 1: Senior demographic stress
        senior_failures = [c for c, r in failures if c.age >= 60]
        if senior_failures:
            pct = round((len(senior_failures) / total_failures) * 100, 1)
            clusters.append(
                FailureCluster(
                    cluster_name="Senior Citizen Edge Sensitivity",
                    affected_percentage=pct,
                    sample_size=len(senior_failures),
                    common_traits=["Age >= 60", "Basic/Moderate tech savviness", "Health vulnerability indicators"],
                    root_cause="Model disproportionately produces low confidence scores or rejections when encountering senior profiles.",
                    suggested_fix="Calibrate model threshold with representative senior citizen synthetic training datasets.",
                )
            )

        # Cluster 2: Informal / Low-Income Vulnerability
        low_income_failures = [c for c, r in failures if c.annual_income < 400000]
        if low_income_failures:
            pct = round((len(low_income_failures) / total_failures) * 100, 1)
            clusters.append(
                FailureCluster(
                    cluster_name="Low-Income Threshold Collapse",
                    affected_percentage=pct,
                    sample_size=len(low_income_failures),
                    common_traits=["Annual Income < ₹4L", "High DTI ratio", "Elevated daily stress level"],
                    root_cause="Model output correlation heavily penalizes low liquid savings regardless of positive credit history.",
                    suggested_fix="Introduce non-linear feature scaling for income variables or apply fair-lending re-weighting.",
                )
            )

        return clusters
