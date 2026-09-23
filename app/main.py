import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import UPLOAD_DIR
from .store import store
from .websocket_manager import manager

app = FastAPI(title="Group Music Room")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOAD_PATH = os.path.join(BASE_DIR, UPLOAD_DIR)
os.makedirs(UPLOAD_PATH, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_PATH), name="uploads")


@app.get("/room/{token}")
async def room_page(token: str):
    room = store.get_by_token(token)
    if not room:
        return JSONResponse({"error": "Room not found"}, status_code=404)
    return FileResponse(os.path.join(FRONTEND_DIR, "room.html"))


@app.get("/api/room/{token}/state")
async def room_state(token: str):
    room = store.get_by_token(token)
    if not room:
        return JSONResponse({"error": "Room not found"}, status_code=404)
    return store.state_dict(room)


@app.websocket("/ws/{token}")
async def ws_endpoint(websocket: WebSocket, token: str):
    room = store.get_by_token(token)
    if not room:
        await websocket.close(code=4404)
        return

    await manager.connect(token, websocket)
    try:
        await websocket.send_json({"type": "state", **store.state_dict(room)})
        while True:
            # Client doesn't need to send anything; this just keeps the socket open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(token, websocket)
