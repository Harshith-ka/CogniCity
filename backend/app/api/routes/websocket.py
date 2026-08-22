"""WebSocket endpoint for real-time simulation updates."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.api.routes.simulation import get_simulation_engine

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active[:]:
            try:
                await ws.send_json(data)
            except Exception:
                self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/simulation")
async def simulation_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            try:
                engine = get_simulation_engine()
                metrics = await engine.get_metrics()
                metrics["tick"] = engine.current_tick
                metrics["status"] = engine.status.value
                await ws.send_json(metrics)
            except Exception:
                await ws.send_json({"error": "Engine not ready"})

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(ws)
