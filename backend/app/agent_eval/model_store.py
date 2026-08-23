"""Storage and inference for user-uploaded ONNX models — the Sandbox's "test your own
model file" capability.

Deliberately ONNX-only, not pickle/joblib. scikit-learn's native `pickle.load()` /
`joblib.load()` executes arbitrary code embedded in the file — a well-known RCE vector
for exactly the kind of "let a stranger upload a file" surface this sandbox is (this
project now has open self-signup; an uploaded file here could come from anyone).
ONNX is a static computation-graph format: onnxruntime interprets the graph, it never
executes arbitrary Python, so there's no equivalent risk from loading an untrusted
.onnx file.

Uploaded models are given a fixed input contract — the caller must build a model that
accepts a single float32 tensor of shape [1, 8] in this exact feature order:
age, annual_income, savings, monthly_expenses, credit_score_estimate, health_index,
stress_level, happiness — the same fields CitizenProfileDTO already carries. The
output is read positionally: a single value is treated as an accept-probability; two
values are treated as [reject_prob, accept_prob].
"""

from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import onnxruntime as ort

from backend.app.agent_eval.models import CitizenProfileDTO

MODEL_DIR = Path(__file__).parent / "uploaded_models"
MODEL_DIR.mkdir(exist_ok=True)

FEATURE_ORDER = [
    "age", "annual_income", "savings", "monthly_expenses",
    "credit_score_estimate", "health_index", "stress_level", "happiness",
]

# In-memory session cache — avoids re-loading the same .onnx file from disk on every
# citizen in a batch. Keyed by model_id; cleared on process restart, which is fine
# since model_id is only ever referenced within a single dashboard session anyway.
_session_cache: dict[str, ort.InferenceSession] = {}


class InvalidModelError(Exception):
    pass


def upload_model(file_bytes: bytes, filename: str) -> dict:
    if len(file_bytes) > 50 * 1024 * 1024:
        raise InvalidModelError("Model file exceeds 50MB limit")

    try:
        session = ort.InferenceSession(file_bytes, providers=["CPUExecutionProvider"])
    except Exception as err:
        raise InvalidModelError(f"Not a valid ONNX model: {err}")

    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs:
        raise InvalidModelError("Model has no input tensors")

    model_id = str(uuid.uuid4())
    (MODEL_DIR / f"{model_id}.onnx").write_bytes(file_bytes)
    _session_cache[model_id] = session

    return {
        "model_id": model_id,
        "filename": filename,
        "input_name": inputs[0].name,
        "input_shape": inputs[0].shape,
        "output_names": [o.name for o in outputs],
        "expected_feature_order": FEATURE_ORDER,
    }


def _get_session(model_id: str) -> ort.InferenceSession:
    if model_id in _session_cache:
        return _session_cache[model_id]
    path = MODEL_DIR / f"{model_id}.onnx"
    if not path.exists():
        raise InvalidModelError(f"Unknown model_id {model_id!r} — upload may have happened in a previous session")
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    _session_cache[model_id] = session
    return session


def run_inference(model_id: str, citizen: CitizenProfileDTO) -> dict:
    session = _get_session(model_id)
    input_name = session.get_inputs()[0].name

    features = np.array([[
        float(citizen.age), citizen.annual_income, citizen.savings, citizen.monthly_expenses,
        float(citizen.credit_score_estimate), citizen.health_index, citizen.stress_level, citizen.happiness,
    ]], dtype=np.float32)

    try:
        raw_outputs = session.run(None, {input_name: features})
    except Exception as err:
        return {"error": str(err), "decision": "model_error", "confidence": 0.0}

    values = np.asarray(raw_outputs[0]).flatten()
    if values.size >= 2:
        accept_prob = float(values[1])
    elif values.size == 1:
        accept_prob = float(values[0])
    else:
        return {"error": "Model returned an empty output", "decision": "model_error", "confidence": 0.0}

    # Some models output logits rather than probabilities — clip defensively so a
    # value outside [0, 1] doesn't produce a nonsensical "120% confident" reading.
    accept_prob = max(0.0, min(1.0, accept_prob))
    approved = accept_prob >= 0.5

    return {
        "decision": "approved" if approved else "rejected",
        "score": round(accept_prob * 100, 1),
        "confidence": round(accept_prob if approved else 1 - accept_prob, 3),
        "rationale": "Output of the uploaded ONNX model, run locally.",
    }
