from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_players: dict[str, WebSocket] = {}
        self.admin: WebSocket = None

    async def connect(self, websocket: WebSocket, user_type: str, user_id: str):
        await websocket.accept()
        if user_type == "admin":
            self.admin = websocket
            await websocket.send_text(f"Admin {user_id} connected")
        else:
            self.active_players[user_id] = websocket
            await websocket.send_text(f"Player {user_id} connected")
        
    def disconnect(self, websocket: WebSocket):
        if websocket == self.admin:
            self.admin = None
        else:
            for user_id, ws in self.active_players.items():
                if ws == websocket:
                    del self.active_players[user_id]
                    break

    async def broadcast(self, message: str):
        # Send a message to all players
        for connection in self.active_players.values():
            await connection.send_text(message)
        if self.admin:
            await self.admin.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_type}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_type: str, user_id: str):
    await manager.connect(websocket, user_type, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Handle Admin Commands
            if user_type == "admin":
                if data == "start":
                    await manager.broadcast("Game started by admin")
                elif data == "stop":
                    await manager.broadcast("Game stopped by admin")
                else:
                    await manager.admin.send_text(f"Unknown admin command: {data}")
            
            # Handle Player Commands
            else:
                # Here you would process player actions (move, fire, etc.)
                await manager.broadcast(f"Player {user_id} action: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{user_type.capitalize()} {user_id} disconnected")
