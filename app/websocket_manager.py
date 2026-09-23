import json
from typing import Dict, List

from fastapi import WebSocket


class WSManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, token: str, ws: WebSocket):
        await ws.accept()
        self.connections.setdefault(token, []).append(ws)

    def disconnect(self, token: str, ws: WebSocket):
        conns = self.connections.get(token, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, token: str, message: dict):
        dead = []
        for ws in self.connections.get(token, []):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(token, ws)


manager = WSManager()
