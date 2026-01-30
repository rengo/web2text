from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import sites, pages, feed, settings, auth
import asyncio
import asyncpg
import json
import logging
from shared.core.database import DATABASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="Web2Text Scraper API")

import os

# ...

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:3005").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sites.router)
app.include_router(pages.router)
app.include_router(feed.router)
app.include_router(settings.router)
app.include_router(auth.router)
from backend.app.routers import public, api_keys
app.include_router(public.router)
app.include_router(api_keys.router)

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Web2Text Public API" if os.getenv("ENVIRONMENT") == "production" else "Web2Text Scraper API",
        version="1.0.0",
        description="Public API for content consumption" if os.getenv("ENVIRONMENT") == "production" else "Full Scraper API Documentation",
        routes=app.routes,
    )
    
    # Logic to filter schema in production
    if os.getenv("ENVIRONMENT") == "production":
        paths = openapi_schema.get("paths", {})
        public_paths = {}
        
        for path, methods in paths.items():
            new_methods = {}
            for method, details in methods.items():
                # Only include endpoints with the 'public' tag
                if "public" in details.get("tags", []):
                    new_methods[method] = details
            
            if new_methods:
                public_paths[path] = new_methods
        
        openapi_schema["paths"] = public_paths
        
        # Clean up tags metadata
        if "tags" in openapi_schema:
            openapi_schema["tags"] = [t for t in openapi_schema["tags"] if t["name"] == "public"]
            
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Handle disconnected clients that weren't properly removed
                pass

manager = ConnectionManager()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just keep the connection open, we don't expect messages from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

# Background task to listen to Postgres notifications
async def listen_to_logs():
    # asyncpg expects 'postgresql://' not 'postgresql+asyncpg://'
    dsn = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    try:
        conn = await asyncpg.connect(dsn)
        await conn.add_listener("worker_logs", lambda connection, pid, channel, payload: asyncio.create_task(manager.broadcast(payload)))
        logger.info("Listening to worker_logs channel...")
        while True:
            await asyncio.sleep(60) # Keep the listener alive
            if conn.is_closed():
                break
    except Exception as e:
        logger.error(f"Error in log listener: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(listen_to_logs())
    finally:
        try:
            if 'conn' in locals() and not conn.is_closed():
                await conn.close()
        except:
            pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(listen_to_logs())

@app.get("/health")
async def health_check():
    return {"status": "ok"}
