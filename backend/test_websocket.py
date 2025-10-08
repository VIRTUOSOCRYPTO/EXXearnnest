#!/usr/bin/env python3
"""
WebSocket Test Script
Simple test to verify WebSocket functionality
"""

import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

@app.websocket("/test/ws")
async def test_websocket(websocket: WebSocket):
    """Simple WebSocket test endpoint"""
    await websocket.accept()
    await websocket.send_text("WebSocket connection successful!")
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
