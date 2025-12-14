"""MCP Server Manager - Handles connections to MCP servers."""
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self, config_path: str = "mcp_config.json"):
        # Resolve config path relative to project root
        project_root = Path(__file__).parent.parent
        self.config_path = project_root / config_path
        self.sessions: Dict[str, ClientSession] = {}
        self.server_params: Dict[str, StdioServerParameters] = {}
        self.tools_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.transports: Dict[str, Any] = {}  # Store context managers
        
    def load_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from JSON file."""
        if not self.config_path.exists():
            return {"servers": {}}
        
        with open(self.config_path, "r") as f:
            return json.load(f)
    
    async def connect_server(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Connect to an MCP server."""
        if server_name in self.sessions:
            return True
        
        try:
            command = config["command"]
            args = config.get("args", [])
            
            server_params = StdioServerParameters(
                command=command,
                args=args,
            )
            
            self.server_params[server_name] = server_params
            
            # Create and store stdio client context manager
            stdio_transport_cm = stdio_client(server_params)
            read_stream, write_stream = await stdio_transport_cm.__aenter__()
            
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            await session.initialize()
            
            self.sessions[server_name] = session
            self.transports[server_name] = (stdio_transport_cm, session)
            await self._refresh_tools(server_name)
            
            return True
        except Exception as e:
            print(f"Error connecting to {server_name}: {e}")
            return False
    
    async def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server."""
        if server_name in self.transports:
            try:
                stdio_transport_cm, session = self.transports[server_name]
                await session.__aexit__(None, None, None)
                await stdio_transport_cm.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error disconnecting {server_name}: {e}")
            del self.transports[server_name]
        
        if server_name in self.sessions:
            del self.sessions[server_name]
        if server_name in self.server_params:
            del self.server_params[server_name]
        if server_name in self.tools_cache:
            del self.tools_cache[server_name]
    
    async def connect_all(self):
        """Connect to all servers in configuration."""
        config = self.load_config()
        servers = config.get("servers", {})
        
        for server_name, server_config in servers.items():
            await self.connect_server(server_name, server_config)
    
    async def _refresh_tools(self, server_name: str):
        """Refresh tools cache for a server."""
        if server_name not in self.sessions:
            return
        
        try:
            session = self.sessions[server_name]
            tools_result = await session.list_tools()
            self.tools_cache[server_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in tools_result.tools
            ]
        except Exception as e:
            print(f"Error refreshing tools for {server_name}: {e}")
            self.tools_cache[server_name] = []
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tools from all connected servers."""
        return self.tools_cache.copy()
    
    def get_servers(self) -> List[str]:
        """Get list of connected server names."""
        return list(self.sessions.keys())
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server."""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        
        try:
            session = self.sessions[server_name]
            result = await session.call_tool(tool_name, arguments)
            
            return {
                "content": [
                    {
                        "type": item.type,
                        "text": item.text if hasattr(item, "text") else str(item),
                    }
                    for item in result.content
                ],
                "isError": result.isError if hasattr(result, "isError") else False,
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }
    
    async def find_tool_server(self, tool_name: str) -> Optional[str]:
        """Find which server has a specific tool."""
        for server_name, tools in self.tools_cache.items():
            if any(tool["name"] == tool_name for tool in tools):
                return server_name
        return None


# Global instance
_manager: Optional[MCPManager] = None


def get_manager() -> MCPManager:
    """Get or create the global MCP manager instance."""
    global _manager
    if _manager is None:
        _manager = MCPManager()
    return _manager

