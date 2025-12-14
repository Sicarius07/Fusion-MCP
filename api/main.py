"""FastAPI server with WebSocket support for MCP client."""
import os
import json
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from mcp_manager import get_manager
from openai_handler import OpenAIHandler

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handlers
openai_handler: OpenAIHandler | None = None


@app.on_event("startup")
async def startup():
    """Initialize MCP connections on startup."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    global openai_handler
    openai_handler = OpenAIHandler(api_key)
    
    # Connect to all configured MCP servers
    manager = get_manager()
    await manager.connect_all()


@app.on_event("shutdown")
async def shutdown():
    """Clean up MCP connections on shutdown."""
    manager = get_manager()
    for server_name in manager.get_servers():
        await manager.disconnect_server(server_name)


@app.get("/api/servers")
async def get_servers():
    """Get list of connected MCP servers and their tools."""
    manager = get_manager()
    servers = manager.get_servers()
    tools = manager.get_all_tools()
    
    return {
        "servers": [
            {
                "name": server_name,
                "connected": True,
                "tools": tools.get(server_name, []),
            }
            for server_name in servers
        ]
    }


@app.post("/api/servers")
async def add_server(server_config: Dict[str, Any]):
    """Add a new MCP server connection."""
    server_name = server_config.get("name")
    if not server_name:
        raise HTTPException(status_code=400, detail="Server name required")
    
    config = server_config.get("config", {})
    manager = get_manager()
    
    success = await manager.connect_server(server_name, config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to connect to server")
    
    return {"status": "connected", "server": server_name}


@app.delete("/api/servers/{server_name}")
async def remove_server(server_name: str):
    """Remove an MCP server connection."""
    manager = get_manager()
    await manager.disconnect_server(server_name)
    return {"status": "disconnected", "server": server_name}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    
    conversation_history: List[Dict[str, Any]] = []
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                user_message = message_data.get("content", "")
                
                if not openai_handler:
                    await websocket.send_json({
                        "type": "error",
                        "content": "OpenAI handler not initialized"
                    })
                    continue
                
                # Update conversation history with user message
                conversation_history.append({"role": "user", "content": user_message})
                
                # Process message with streaming
                final_messages = []
                async for chunk in openai_handler.process_message(conversation_history):
                    await websocket.send_json(chunk)
                    # Track final messages for history
                    if chunk.get("type") == "assistant" and chunk.get("content"):
                        if not final_messages:
                            final_messages.append({"role": "assistant", "content": ""})
                        final_messages[0]["content"] += chunk["content"]
                
                # Update conversation history with assistant response
                if final_messages:
                    conversation_history.append(final_messages[0])
                
            elif message_data.get("type") == "clear":
                conversation_history = []
                await websocket.send_json({"type": "cleared"})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"Error: {str(e)}"
        })


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "MCP Client API"}

