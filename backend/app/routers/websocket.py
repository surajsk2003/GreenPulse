from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time updates every 5 seconds
            await asyncio.sleep(5)
            update = {
                "type": "energy_update",
                "timestamp": datetime.now().isoformat(),
                "data": {"current_usage": 150.5, "alerts": 2}
            }
            await websocket.send_text(json.dumps(update))
    except WebSocketDisconnect:
        manager.disconnect(websocket)