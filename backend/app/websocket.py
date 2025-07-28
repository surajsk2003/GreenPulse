from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time updates every 5 seconds
            data = {
                "timestamp": datetime.now().isoformat(),
                "type": "energy_update",
                "data": {
                    "total_consumption": 1250.5,
                    "cost_today": 150.25,
                    "carbon_emissions": 1150.8,
                    "efficiency_score": 85
                }
            }
            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)