"""Universal Agent Client: Dispatches citizen profiles to external AI models asynchronously."""

from __future__ import annotations

import asyncio
import random
from typing import Any
import httpx

from backend.app.agent_eval.models import (
    AgentProtocol,
    AgentTestRequest,
    CitizenProfileDTO,
)
from backend.app.agent_eval import model_store


class UniversalAgentClient:
    """Dispatches citizen batches to developer agents via Webhooks, OpenAI APIs, or Mock benchmarks."""

    def __init__(self, request: AgentTestRequest):
        self.request = request

    async def evaluate_batch(
        self,
        citizens: list[CitizenProfileDTO],
    ) -> list[tuple[CitizenProfileDTO, dict[str, Any]]]:
        """Dispatches citizens concurrently in batches with rate limiting."""
        results: list[tuple[CitizenProfileDTO, dict[str, Any]]] = []
        batch_size = 50

        for i in range(0, len(citizens), batch_size):
            chunk = citizens[i:i + batch_size]
            tasks = [self._call_agent_for_citizen(c) for c in chunk]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=False)
            results.extend(chunk_results)

        return results

    async def _call_agent_for_citizen(
        self,
        c: CitizenProfileDTO,
    ) -> tuple[CitizenProfileDTO, dict[str, Any]]:
        if self.request.protocol == AgentProtocol.REST_WEBHOOK and self.request.endpoint_url:
            return await self._call_rest_webhook(c)
        elif self.request.protocol == AgentProtocol.OPENAI_CHAT and self.request.endpoint_url:
            return await self._call_openai_chat(c)
        elif self.request.protocol == AgentProtocol.UPLOADED_MODEL and self.request.model_id:
            return await self._call_uploaded_model(c)
        else:
            return await self._call_mock_benchmark(c)

    async def _call_uploaded_model(
        self,
        c: CitizenProfileDTO,
    ) -> tuple[CitizenProfileDTO, dict[str, Any]]:
        # onnxruntime's session.run() is synchronous CPU-bound work — run it in a
        # thread so one slow model doesn't block the event loop for every other
        # concurrent evaluation batch (evaluate_batch already gathers 50 at a time).
        result = await asyncio.to_thread(model_store.run_inference, self.request.model_id, c)
        return c, result

    async def _call_rest_webhook(
        self,
        c: CitizenProfileDTO,
    ) -> tuple[CitizenProfileDTO, dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if self.request.api_key:
                    headers["Authorization"] = f"Bearer {self.request.api_key}"

                payload = c.model_dump()
                res = await client.post(self.request.endpoint_url, json=payload, headers=headers)
                if res.status_code == 200:
                    return c, res.json()
                else:
                    return c, {"error": f"HTTP {res.status_code}", "decision": "error", "confidence": 0.0}
        except Exception as err:
            return c, {"error": str(err), "decision": "network_error", "confidence": 0.0}

    async def _call_openai_chat(
        self,
        c: CitizenProfileDTO,
    ) -> tuple[CitizenProfileDTO, dict[str, Any]]:
        prompt = self.request.prompt_template or "Evaluate this citizen profile and return a decision: {profile}"
        formatted = prompt.replace("{profile}", c.model_dump_json())

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {"Authorization": f"Bearer {self.request.api_key or 'test'}"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are an autonomous AI evaluation agent."},
                        {"role": "user", "content": formatted}
                    ],
                    "temperature": 0.2
                }
                res = await client.post(self.request.endpoint_url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return c, {"decision_text": content, "confidence": 0.85}
                else:
                    return c, {"error": f"LLM Error {res.status_code}", "confidence": 0.0}
        except Exception as err:
            return c, {"error": str(err), "confidence": 0.0}

    async def _call_mock_benchmark(
        self,
        c: CitizenProfileDTO,
    ) -> tuple[CitizenProfileDTO, dict[str, Any]]:
        """High-fidelity benchmark simulator for general, credit, health, or recommendation domains."""
        await asyncio.sleep(0.001)  # Yield loop
        
        # Realistic heuristic behavior for demo testing
        is_high_risk = c.stress_level > 0.8 or c.health_index < 0.45 or c.credit_score_estimate < 580
        prob_positive = 0.82 if not is_high_risk else 0.35
        
        # Introduce subtle demographic bias to allow auditor to catch it
        if c.age > 65:
            prob_positive *= 0.88
        if c.annual_income < 300000:
            prob_positive *= 0.75

        approved = random.random() < prob_positive
        confidence = round(random.uniform(0.72, 0.98) if approved else random.uniform(0.60, 0.92), 3)

        return c, {
            "decision": "approved" if approved else "rejected",
            "score": round(prob_positive * 100, 1),
            "confidence": confidence,
            "rationale": "Model processed demographic, financial, and risk indicators."
        }
